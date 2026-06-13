from django.core.management.base import BaseCommand
from sales.models import CustomUser
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Crée un superuser automatiquement'

    def handle(self, *args, **kwargs):
        username = 'admin'
        password = 'admin123'
        
        if not CustomUser.objects.filter(username=username).exists():
            user = CustomUser.objects.create_superuser(
                username=admin,
                password=admin123,
                email='admin@mokonzi.com',
                role='super_admin'
            )
            Token.objects.get_or_create(user=user)
            self.stdout.write(f'Superuser {username} créé avec succès')
        else:
            self.stdout.write(f'Superuser {username} existe déjà')
