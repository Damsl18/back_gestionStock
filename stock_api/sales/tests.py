"""
Tests unitaires pour l'application sales
Teste les modèles, les sérialiseurs et les vues
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import CustomUser, Product, Sale, Invoice, Discount
from datetime import datetime, timedelta
from django.utils import timezone


class UserModelTests(TestCase):
    """Tests pour le modèle CustomUser"""
    
    def setUp(self):
        """Préparer les données de test"""
        self.worker = CustomUser.objects.create_user(
            username='worker1',
            password='testpass123',
            role='worker'
        )
        self.client_user = CustomUser.objects.create_user(
            username='client1',
            password='testpass123',
            role='client'
        )
    
    def test_user_creation(self):
        """Tester la création d'un utilisateur"""
        self.assertEqual(self.worker.username, 'worker1')
        self.assertEqual(self.worker.role, 'worker')
    
    def test_is_worker(self):
        """Tester la méthode is_worker()"""
        self.assertTrue(self.worker.is_worker())
        self.assertFalse(self.client_user.is_worker())
    
    def test_password_hashing(self):
        """Vérifier que le mot de passe est bien hashé"""
        self.assertNotEqual(self.worker.password, 'testpass123')
        self.assertTrue(self.worker.check_password('testpass123'))


class ProductModelTests(TestCase):
    """Tests pour le modèle Product"""
    
    def setUp(self):
        """Préparer les données de test"""
        self.product = Product.objects.create(
            name='Farine de blé 10kg',
            price=15.99,
            quantity_in_stock=50
        )
    
    def test_product_creation(self):
        """Tester la création d'un produit"""
        self.assertEqual(self.product.name, 'Farine de blé 10kg')
        self.assertEqual(self.product.price, 15.99)
    
    def test_is_in_stock(self):
        """Tester la disponibilité du stock"""
        self.assertTrue(self.product.is_in_stock(30))
        self.assertFalse(self.product.is_in_stock(60))
    
    def test_reduce_stock(self):
        """Tester la réduction du stock"""
        result = self.product.reduce_stock(20)
        self.assertTrue(result)
        self.assertEqual(self.product.quantity_in_stock, 30)


class UserAuthenticationTests(TestCase):
    """Tests pour l'authentification des utilisateurs"""
    
    def setUp(self):
        """Préparer les données de test"""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'role': 'worker'
        }
    
    def test_user_registration(self):
        """Tester l'enregistrement d'un nouvel utilisateur"""
        response = self.client.post('/api/auth/register/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
    
    def test_user_login(self):
        """Tester la connexion d'un utilisateur"""
        # D'abord, créer un utilisateur
        user = CustomUser.objects.create_user(
            username='testuser',
            password='securepass123'
        )
        
        # Ensuite, tenter la connexion
        login_data = {
            'username': 'testuser',
            'password': 'securepass123'
        }
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class BruteForceProtectionTests(TestCase):
    """Tests pour la protection contre le brute force"""
    
    def setUp(self):
        """Préparer les données de test"""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='securepass123'
        )
    
    def test_account_locked_after_failed_attempts(self):
        """Tester que le compte est verrouillé après 3 tentatives échouées"""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        # Faire 3 tentatives échouées
        for i in range(3):
            response = self.client.post('/api/auth/login/', login_data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Vérifier que le compte est verrouillé
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)
