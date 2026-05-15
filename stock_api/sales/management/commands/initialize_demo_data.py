"""
Commande de gestion pour initialiser les données de test
Utilisation: python manage.py initialize_demo_data
"""

from django.core.management.base import BaseCommand
from sales.models import CustomUser, Product, Sale, Discount, DailyReport
from django.utils import timezone
from django.db import models
from decimal import Decimal
from datetime import datetime, timedelta


class Command(BaseCommand):
    """Commande pour initialiser les données de démonstration"""
    
    help = 'Initialise les données de démonstration pour l\'application'
    
    def handle(self, *args, **options):
        """Exécuter la commande"""
        self.stdout.write('Initialisation des données de démonstration...')
        
        # Créer les utilisateurs
        self.create_users()
        
        # Créer les produits
        self.create_products()
        
        # Créer les réductions
        self.create_discounts()
        
        # Créer les ventes de test
        self.create_sample_sales()
        
        # Créer les rapports journaliers
        self.create_daily_reports()
        
        self.stdout.write(
            self.style.SUCCESS('✓ Données de démonstration créées avec succès!')
        )
    
    def create_users(self):
        """Créer les utilisateurs de démonstration"""
        self.stdout.write('Création des utilisateurs...')
        
        # Créer un super admin
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='super_admin'
            )
            self.stdout.write('  ✓ Super Admin créé (admin/admin123)')
        
        # Créer des workers
        workers_data = [
            {'username': 'worker1', 'email': 'worker1@example.com'},
            {'username': 'worker2', 'email': 'worker2@example.com'},
        ]
        
        for worker_data in workers_data:
            if not CustomUser.objects.filter(username=worker_data['username']).exists():
                CustomUser.objects.create_user(
                    username=worker_data['username'],
                    email=worker_data['email'],
                    password='worker123',
                    role='worker'
                )
                self.stdout.write(f"  ✓ Worker {worker_data['username']} créé")
        
        # Créer des clients
        clients_data = [
            {'username': 'client1', 'email': 'client1@example.com'},
            {'username': 'client2', 'email': 'client2@example.com'},
        ]
        
        for client_data in clients_data:
            if not CustomUser.objects.filter(username=client_data['username']).exists():
                CustomUser.objects.create_user(
                    username=client_data['username'],
                    email=client_data['email'],
                    password='client123',
                    role='client'
                )
                self.stdout.write(f"  ✓ Client {client_data['username']} créé")
    
    def create_products(self):
        """Créer les produits de démonstration"""
        self.stdout.write('Création des produits...')
        
        products_data = [
            {
                'name': 'Farine de blé 10kg',
                'description': 'Sac de farine de blé de 10 kilogrammes',
                'price': Decimal('15.99'),
                'quantity_in_stock': 100,
            },
            {
                'name': 'Farine de maïs 5kg',
                'description': 'Sac de farine de maïs de 5 kilogrammes',
                'price': Decimal('12.50'),
                'quantity_in_stock': 75,
            },
            {
                'name': 'Farine complète 10kg',
                'description': 'Sac de farine complète de 10 kilogrammes',
                'price': Decimal('18.99'),
                'quantity_in_stock': 50,
            },
            {
                'name': 'Farine biologique 5kg',
                'description': 'Sac de farine biologique de 5 kilogrammes',
                'price': Decimal('22.99'),
                'quantity_in_stock': 30,
            },
        ]
        
        for product_data in products_data:
            if not Product.objects.filter(name=product_data['name']).exists():
                Product.objects.create(**product_data)
                self.stdout.write(f"  ✓ Produit '{product_data['name']}' créé")
    
    def create_discounts(self):
        """Créer les réductions de démonstration"""
        self.stdout.write('Création des réductions...')
        
        products = Product.objects.all()
        
        for product in products[:2]:  # Créer des réductions pour les 2 premiers produits
            if not Discount.objects.filter(product=product).exists():
                Discount.objects.create(
                    product=product,
                    discount_percentage=Decimal('10'),
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                    description=f'Réduction de 10% sur {product.name}'
                )
                self.stdout.write(f"  ✓ Réduction de 10% créée pour '{product.name}'")
    
    def create_sample_sales(self):
        """Créer des ventes de démonstration"""
        self.stdout.write('Création des ventes de démonstration...')
        
        worker = CustomUser.objects.filter(role='worker').first()
        products = Product.objects.all()
        
        if worker and products:
            for i in range(10):  # Créer 10 ventes de démonstration
                product = products[i % len(products)]
                Sale.objects.create(
                    worker=worker,
                    product=product,
                    quantity=5,
                    unit_price=product.price
                )
            self.stdout.write(f"  ✓ {10} ventes de démonstration créées")
    
    def create_daily_reports(self):
        """Créer les rapports journaliers"""
        self.stdout.write('Création des rapports journaliers...')
        
        for i in range(7):
            date = (timezone.now() - timedelta(days=i)).date()
            
            if not DailyReport.objects.filter(report_date=date).exists():
                sales_count = Sale.objects.filter(
                    sale_date__date=date
                ).count()
                
                if sales_count > 0:
                    total_amount = Sale.objects.filter(
                        sale_date__date=date
                    ).aggregate(models.Sum('total_price'))['total_price__sum'] or Decimal('0')
                    
                    total_quantity = Sale.objects.filter(
                        sale_date__date=date
                    ).aggregate(models.Sum('quantity'))['quantity__sum'] or 0
                    
                    avg_price = total_amount / sales_count if sales_count > 0 else Decimal('0')
                    
                    DailyReport.objects.create(
                        report_date=date,
                        total_sales_count=sales_count,
                        total_sales_amount=total_amount,
                        total_quantity_sold=total_quantity,
                        average_sale_price=avg_price
                    )
                    self.stdout.write(f"  ✓ Rapport journalier pour {date} créé")
