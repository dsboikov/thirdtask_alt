from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps

class Command(BaseCommand):
    help = "Создать роли/права (Content Managers)"

    @transaction.atomic
    def handle(self, *args, **options):
        from django.db.migrations.executor import MigrationExecutor
        self.stdout.write("Рекомендуется сначала выполнить миграции.")
        self.stdout.write("Роли создаются data-миграцией users.0002_roles автоматически при migrate.")
        self.stdout.write("Если нужно повторить, удалите группу и выполните migrate заново.")
