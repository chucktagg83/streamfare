from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'accounts'
    
    def ready(self):
        """
        Django calls ready() when this app start.
        
        Importing signals here activates the login listener
        """
        
        import accounts.signals
