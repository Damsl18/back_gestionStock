"""
Throttling (Limitation de débit) pour protéger l'API contre les abus
Implémente la protection contre le brute force et les attaques par force brute
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache
import time


# ==================== CUSTOM THROTTLING CLASSES ====================
class UserRateThrottle_10_Per_Minute(UserRateThrottle):
    """
    Limiter les utilisateurs authentifiés à 10 requêtes par minute
    Utilisé pour les endpoints normaux
    """
    scope = 'user_10_per_minute'
    rate = '10/minute'  # 10 requêtes par minute pour les utilisateurs authentifiés


class UserRateThrottle_100_Per_Hour(UserRateThrottle):
    """
    Limiter les utilisateurs authentifiés à 100 requêtes par heure
    Utilisé pour les endpoints critiques
    """
    scope = 'user_100_per_hour'
    rate = '100/hour'  # 100 requêtes par heure


class AnonRateThrottle_5_Per_Minute(AnonRateThrottle):
    """
    Limiter les utilisateurs non authentifiés à 5 requêtes par minute
    Utilisé pour la connexion et l'enregistrement
    """
    scope = 'anon_5_per_minute'
    rate = '5/minute'  # 5 requêtes par minute pour les utilisateurs anonymes


class LoginAttemptThrottle(SimpleRateThrottle):
    """
    Throttle spécialisé pour la protection contre le brute force sur les tentatives de connexion
    Maximum 5 tentatives de connexion par 15 minutes par adresse IP
    """
    scope = 'login_attempt'
    rate = '5/15minutes'  # 5 tentatives par 15 minutes
    
    def get_cache_key(self):
        """
        Utiliser l'adresse IP comme clé de cache
        Cela limite le nombre de tentatives de connexion par adresse IP
        """
        # Récupérer l'adresse IP du client
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        # Retourner la clé de cache basée sur l'adresse IP
        return f'login_attempt_{ip}'


class RegistrationAttemptThrottle(SimpleRateThrottle):
    """
    Throttle pour la protection contre les abus d'enregistrement
    Maximum 10 enregistrements par 1 heure par adresse IP
    """
    scope = 'registration_attempt'
    rate = '10/hour'  # 10 enregistrements par heure
    
    def get_cache_key(self):
        """Utiliser l'adresse IP comme clé de cache"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        return f'registration_attempt_{ip}'


class APIAbuseThrottle(SimpleRateThrottle):
    """
    Throttle pour détecter les abus d'API généraux
    Limite le nombre de requêtes par utilisateur
    """
    scope = 'api_abuse'
    rate = '1000/hour'  # 1000 requêtes par heure
    
    def get_cache_key(self):
        """
        Créer une clé de cache basée sur l'utilisateur ou l'adresse IP
        """
        if self.request.user and self.request.user.is_authenticated:
            # Pour les utilisateurs authentifiés, utiliser leur ID
            return f'api_abuse_{self.request.user.id}'
        else:
            # Pour les utilisateurs anonymes, utiliser leur IP
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            
            return f'api_abuse_{ip}'


class PriceChangeThrottle(SimpleRateThrottle):
    """
    Throttle pour les changements de prix
    Limite les changements de prix à 50 par heure par client
    Prévient les abus de manipulation de prix
    """
    scope = 'price_change'
    rate = '50/hour'
    
    def get_cache_key(self):
        """Utiliser l'ID de l'utilisateur comme clé"""
        if self.request.user and self.request.user.is_authenticated:
            return f'price_change_{self.request.user.id}'
        return None


class DiscountThrottle(SimpleRateThrottle):
    """
    Throttle pour les créations/modifications de réductions
    Limite à 30 créations de réductions par heure par client
    """
    scope = 'discount_creation'
    rate = '30/hour'
    
    def get_cache_key(self):
        """Utiliser l'ID de l'utilisateur comme clé"""
        if self.request.user and self.request.user.is_authenticated:
            return f'discount_creation_{self.request.user.id}'
        return None


class SaleCreationThrottle(SimpleRateThrottle):
    """
    Throttle pour la création de ventes
    Limite à 500 ventes par heure par worker
    Prévient les spam de création de ventes
    """
    scope = 'sale_creation'
    rate = '500/hour'
    
    def get_cache_key(self):
        """Utiliser l'ID de l'utilisateur comme clé"""
        if self.request.user and self.request.user.is_authenticated:
            return f'sale_creation_{self.request.user.id}'
        return None
