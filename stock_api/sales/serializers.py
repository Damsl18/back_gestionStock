"""
Sérialiseurs (Serializers) pour convertir les modèles en JSON
Utilisés pour la sérialisation et désérialisation des données API
"""
from django.utils import timezone

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    CustomUser, Product, Sale, Invoice, Discount, 
    ActivityLog, DailyReport
)
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count
from decimal import Decimal


# ==================== USER SERIALIZERS ====================
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'enregistrement des nouveaux utilisateurs
    Valide les informations et crée un nouvel utilisateur
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        help_text='Mot de passe (minimum 8 caractères)'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        help_text='Confirmer le mot de passe'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
    
    def validate(self, data):
        """Valider que les deux mots de passe correspondent"""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return data
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur avec le mot de passe hashé"""
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)  # Hasher le mot de passe
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Sérialiseur pour la connexion des utilisateurs
    Vérifie les identifiants et implémente la protection contre le brute force
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        """
        Valider les identifiants et implémenter la sécurité contre le brute force
        Après 3 tentatives échouées, le compte est verrouillé
        """
        username = data.get('username')
        password = data.get('password')
        
        try:
            user = CustomUser.objects.get(username=username)
            
            # Vérifier si le compte est verrouillé
            if user.is_locked:
                raise serializers.ValidationError(
                    "Compte verrouillé. Maximum 3 tentatives échouées atteint. "
                    "Contactez l'administrateur."
                )
            
            # Vérifier le mot de passe
            if not user.check_password(password):
                # Incrémenter le compteur de tentatives échouées
                user.failed_login_attempts += 1
                
                # Verrouiller le compte après 3 tentatives échouées
                if user.failed_login_attempts >= 3:
                    user.is_locked = True
                
                user.save()
                raise serializers.ValidationError("Identifiants invalides.")
            
            # Connexion réussie - réinitialiser les tentatives échouées
            user.failed_login_attempts = 0
            user.last_presence = timezone.now()
            user.save()
            
            data['user'] = user
            return data
        
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher le profil détaillé d'un utilisateur
    Affiche les informations personnelles et l'historique d'activité
    """
    last_presence_formatted = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()
    sales_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'last_presence', 'last_presence_formatted',
            'activities_count', 'sales_count', 'is_locked'
        ]
        read_only_fields = ['id', 'last_presence', 'activities_count', 'sales_count']
    
    def get_last_presence_formatted(self, obj):
        """Formater la dernière présence en texte lisible"""
        if obj.last_presence:
            return obj.last_presence.strftime('%d/%m/%Y %H:%M:%S')
        return "Jamais connecté"
    
    def get_activities_count(self, obj):
        """Compter les activités du worker"""
        if obj.is_worker():
            return obj.activity_logs.count()
        return 0
    
    def get_sales_count(self, obj):
        """Compter les ventes enregistrées par le worker"""
        if obj.is_worker():
            return obj.sales.count()
        return 0


class UserListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher la liste des utilisateurs
    Version simplifiée du profil complet
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']


# ==================== PRODUCT SERIALIZERS ====================
class ProductSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les produits (sacs de farines)
    Gère l'affichage et la modification des produits
    """
    current_price = serializers.SerializerMethodField()
    active_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'daily_price',
            'current_price', 'quantity_in_stock', 'active_discount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_price']
    
    def get_current_price(self, obj):
        """Obtenir le prix actuel (prix du jour ou prix standard)"""
        return str(obj.get_current_price())
    
    def get_active_discount(self, obj):
        """Obtenir la réduction active s'il en existe une"""
        active_discount = obj.discounts.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        if active_discount:
            return {
                'id': active_discount.id,
                'percentage': str(active_discount.discount_percentage),
                'description': active_discount.description
            }
        return None


# ==================== DISCOUNT SERIALIZERS ====================
class DiscountSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les réductions
    Permet de créer et gérer les réductions sur les produits
    """
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Discount
        fields = [
            'id', 'product', 'discount_percentage', 'start_date',
            'end_date', 'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at', 'is_active']
    
    def get_is_active(self, obj):
        """Vérifier si la réduction est actuellement active"""
        return obj.is_active()


# ==================== SALE SERIALIZERS ====================
class SaleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les ventes
    Enregistre les ventes avec les produits, quantités et réductions
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    worker_username = serializers.CharField(source='worker.username', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'worker', 'worker_username', 'product', 'product_name',
            'quantity', 'unit_price', 'discount', 'discount_percentage',
            'total_price', 'sale_date'
        ]
        read_only_fields = ['total_price', 'sale_date', 'worker', 'worker_username', 'unit_price']
    
    def get_discount_percentage(self, obj):
        """Obtenir le pourcentage de la réduction appliquée"""
        if obj.discount:
            return str(obj.discount.discount_percentage)
        return None
    
    def create(self, validated_data):
        """Créer une vente et mettre à jour le stock"""
        # Récupérer le worker depuis le contexte de la requête
        request = self.context.get('request')
        validated_data['worker'] = request.user
        
        # Obtenir le prix unitaire actuel du produit
        product = validated_data['product']
        validated_data['unit_price'] = product.get_current_price()
        
        # Créer la vente
        sale = Sale(**validated_data)
        
        # Réduire le stock si la quantité est disponible
        if product.reduce_stock(validated_data['quantity']):
            sale.save()
            return sale
        else:
            raise serializers.ValidationError(
                f"Stock insuffisant. Disponible: {product.quantity_in_stock}"
            )


# ==================== INVOICE SERIALIZERS ====================
class InvoiceDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour les factures
    Affiche toutes les informations de la facture et les ventes associées
    """
    sales = SaleSerializer(many=True, read_only=True)
    sales_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    worker_name = serializers.CharField(source='worker.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'worker', 'worker_name', 'sales', 'sales_ids',
            'total_amount', 'amount_paid', 'remaining_amount',
            'status', 'status_display', 'notes', 'created_at', 'issued_at'
        ]
        read_only_fields = [
            'total_amount', 'created_at', 'issued_at', 'worker',
            'worker_name', 'status_display', 'remaining_amount', 'sales'
        ]
    
    def get_remaining_amount(self, obj):
        """Calculer le montant restant à payer"""
        return str(obj.total_amount - obj.amount_paid)
    
    def create(self, validated_data):
        """
        FIX: Créer facture en gérant correctement le M2M sales + worker.
        """
        # Extraire sales_ids
        sales_data = validated_data.pop('sales_ids', [])
        if not sales_data:
            sales_data = validated_data.pop('sales', [])

        # Extraire worker depuis le contexte de la requête (read_only → pas dans validated_data)
        request = self.context.get('request')
        if request and request.user:
            validated_data['worker'] = request.user

        # Créer la facture sans les M2M
        invoice = Invoice.objects.create(**validated_data)

        # Résoudre les IDs de ventes
        if sales_data:
            from django.db.models import Q
            # sales_data peut être une liste d'IDs ou d'objets Sale
            if sales_data and isinstance(sales_data[0], int):
                sale_ids = sales_data
            else:
                sale_ids = [s.id if hasattr(s, 'id') else s for s in sales_data]

            sales_objs = Sale.objects.filter(id__in=sale_ids)
            invoice.sales.set(sales_objs)

            # Calculer le total depuis les ventes ajoutées
            invoice.calculate_total()
            invoice.save()

        return invoice


class InvoiceListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des factures
    Version allégée avec les informations essentielles
    """
    worker_name = serializers.CharField(source='worker.username', read_only=True)
    sales_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'worker_name', 'total_amount',
            'amount_paid', 'status', 'sales_count', 'created_at'
        ]
        read_only_fields = fields

    def get_sales_count(self, obj):
        """Compter le nombre de ventes dans la facture"""
        return obj.sales.count()


# ==================== ACTIVITY LOG SERIALIZERS ====================
class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les journaux d'activité
    Enregistre les actions des workers pour l'audit
    """
    worker_username = serializers.CharField(source='worker.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'worker', 'worker_username', 'action', 'action_display',
            'description', 'timestamp', 'ip_address'
        ]
        read_only_fields = ['id', 'worker', 'timestamp', 'worker_username', 'action_display']


# ==================== DAILY REPORT SERIALIZERS ====================
class DailyReportSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les rapports journaliers
    Affiche les statistiques agrégées des ventes par jour
    """
    class Meta:
        model = DailyReport
        fields = [
            'id', 'report_date', 'total_sales_count', 'total_sales_amount',
            'total_quantity_sold', 'average_sale_price', 'created_at'
        ]
        read_only_fields = fields


# ==================== WEEKLY REPORT SERIALIZER ====================
class WeeklyReportSerializer(serializers.Serializer):
    """
    Sérialiseur pour les rapports hebdomadaires
    Génère les statistiques des 7 derniers jours
    """
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_quantity = serializers.IntegerField()
    average_daily_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    daily_breakdown = serializers.ListField(child=serializers.DictField())  # FIX: dicts depuis Sale

    @staticmethod
    def generate_weekly_report():
        """
        FIX F13: Rapport hebdomadaire basé sur Sale directement.
        DailyReport n'est jamais peuplé automatiquement.
        """
        from django.utils import timezone as tz
        today = tz.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Ventes de la semaine depuis Sale directement
        weekly_sales = Sale.objects.filter(
            sale_date__date__range=[week_start, week_end]
        )

        total_sales = weekly_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
        total_quantity = weekly_sales.aggregate(Sum('quantity'))['quantity__sum'] or 0

        # Breakdown journalier
        daily_breakdown = []
        current = week_start
        while current <= week_end:
            day_sales = weekly_sales.filter(sale_date__date=current)
            day_count = day_sales.count()
            if day_count > 0:
                day_total = day_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
                day_qty = day_sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
                daily_breakdown.append({
                    'report_date': str(current),
                    'total_sales_count': day_count,
                    'total_sales_amount': str(day_total),
                    'total_quantity_sold': day_qty,
                    'average_sale_price': str(day_total / day_count),
                })
            current += timedelta(days=1)

        days_with_sales = len(daily_breakdown)
        average_daily_sales = total_sales / days_with_sales if days_with_sales > 0 else Decimal('0')

        return {
            'week_start': str(week_start),
            'week_end': str(week_end),
            'total_sales': str(total_sales),
            'total_quantity': total_quantity,
            'average_daily_sales': str(average_daily_sales),
            'daily_breakdown': daily_breakdown,
        }