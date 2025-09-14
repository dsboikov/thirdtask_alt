from __future__ import annotations
from typing import Any
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Создать роли/права (Content Managers)"

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Рекомендуется сначала выполнить миграции.")
        self.stdout.write("Роли создаются data-миграцией users.0002_roles автоматически при migrate.")
        self.stdout.write("Если нужно повторить, удалите группу и выполните migrate заново.")
