"""
URLs pour l'application sales
Définit les routes pour tous les endpoints de l'API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView, UserViewSet,
    ProductViewSet, SaleViewSet, InvoiceViewSet, DiscountViewSet,
    DailyReportViewSet, WeeklyReportView, AverageSalesView
)

# Créer un router pour les viewsets
# Le router génère automatiquement les URLs CRUD pour les viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'discounts', DiscountViewSet, basename='discount')
router.register(r'reports/daily', DailyReportViewSet, basename='daily-report')

# Définir les URL patterns pour l'authentification et les rapports
urlpatterns = [
    # ===================== AUTHENTIFICATION =====================
    # Endpoint pour l'enregistrement des nouveaux utilisateurs
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    
    # Endpoint pour la connexion des utilisateurs
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    
    # Endpoint pour la déconnexion des utilisateurs
    path('auth/logout/', UserLogoutView.as_view(), name='user-logout'),
    
    # ===================== RAPPORTS =====================
    # Endpoint pour le rapport hebdomadaire
    path('reports/weekly/', WeeklyReportView.as_view(), name='weekly-report'),
    
    # Endpoint pour la moyenne de ventes
    path('reports/average-sales/', AverageSalesView.as_view(), name='average-sales'),
    
    # Inclure toutes les URLs du router
    path('', include(router.urls)),
]
