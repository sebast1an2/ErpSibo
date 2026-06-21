"""
SIBO ERP — Comando: bootstrap_public_tenant

Crea, de forma IDEMPOTENTE, el tenant `public` y un dominio que apunte a él
(por defecto `localhost`). Es el paso que falta para que django-tenants pueda
resolver las peticiones al dominio raíz en desarrollo.

Uso:
    docker compose exec web python manage.py bootstrap_public_tenant
    # o con dominio distinto:
    docker compose exec web python manage.py bootstrap_public_tenant --domain midominio.com

Requiere haber corrido antes `migrate_schemas --shared` (las tablas de
plataforma deben existir en el schema public).
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name

from apps.plataforma.models import Dominio, Tenant


class Command(BaseCommand):
    help = "Crea (idempotente) el tenant 'public' y su dominio (def: localhost)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            default="localhost",
            help="Dominio que enruta al schema public (por defecto: localhost).",
        )

    def handle(self, *args, **options):
        domain_name = options["domain"]
        public_schema = get_public_schema_name()  # normalmente "public"

        tenant, created = Tenant.objects.get_or_create(
            schema_name=public_schema,
            defaults={"nombre": "Plataforma SIBO (public)"},
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Tenant '{public_schema}' creado.")
            )
        else:
            self.stdout.write(f"Tenant '{public_schema}' ya existía.")

        domain, dcreated = Dominio.objects.get_or_create(
            domain=domain_name,
            defaults={"tenant": tenant, "is_primary": True},
        )
        if dcreated:
            self.stdout.write(
                self.style.SUCCESS(f"Dominio '{domain_name}' -> public creado.")
            )
        else:
            self.stdout.write(f"Dominio '{domain_name}' ya existía.")

        self.stdout.write(self.style.SUCCESS("Bootstrap del tenant public listo."))
