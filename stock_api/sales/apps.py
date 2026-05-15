"""
Configuration de l'application sales
"""

from django.apps import AppConfig


class SalesConfig(AppConfig):
    """Configuration pour l'application de gestion des ventes"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales'
    verbose_name = 'Gestion des Ventes'
