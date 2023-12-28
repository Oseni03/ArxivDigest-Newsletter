from django.apps import AppConfig


class newsletterconfig(AppConfig):
    name = 'newsletter'
    
    def ready(self):
        from . import user_signals