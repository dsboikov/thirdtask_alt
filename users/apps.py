from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = "Покупатели"

    def ready(self):
        # Здесь можно подключать сигналы, если будут
        # Например: import users.signals
        pass