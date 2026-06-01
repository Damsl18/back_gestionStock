"""
Modèles pour la gestion des ventes de sacs de farines
Incluent: Produits, Utilisateurs, Ventes, Factures, Réductions
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from decimal import Decimal


# ==================== CUSTOM USER MODEL ====================
class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé avec trois rôles:
    - worker: Enregistre les ventes et crée les factures
    - client: Gère les prix, réductions et rapports
    - super_admin: Accès complet au système
    """
    
    # Définition des choix de rôles disponibles
    ROLE_CHOICES = [
        ('worker', 'Travailleur'),
        ('client', 'Client/Manager'),
        ('super_admin', 'Super Administrateur'),
    ]
    
    # Champ pour définir le rôle de l'utilisateur
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='worker',
        help_text='Rôle de l\'utilisateur dans le système'
    )
    
    # Champ pour compter les tentatives de connexion échouées (sécurité)
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text='Nombre de tentatives de connexion échouées'
    )
    
    # Champ pour bloquer le compte après 3 essais échoués
    is_locked = models.BooleanField(
        default=False,
        help_text='Compte verrouillé après 3 tentatives échouées'
    )
    
    # Champ pour enregistrer la dernière présence du worker
    last_presence = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Dernière présence enregistrée du worker'
    )
    
    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_role(self, role):
        """Vérifier si l'utilisateur a un rôle spécifique"""
        return self.role == role
    
    def is_worker(self):
        """Vérifier si l'utilisateur est un worker"""
        return self.role == 'worker'
    
    def is_client(self):
        """Vérifier si l'utilisateur est un client/manager"""
        return self.role == 'client'
    
    def is_super_admin(self):
        """Vérifier si l'utilisateur est un super admin"""
        return self.role == 'super_admin'
    
    def unlock_account(self):
        """Déverrouiller le compte et réinitialiser les tentatives"""
        self.is_locked = False
        self.failed_login_attempts = 0
        self.save()


# ==================== PRODUCT MODEL ====================
class Product(models.Model):
    """
    Modèle pour les produits (Sacs de farines)
    Gère le stock et les prix
    """
    
    # Nom du produit
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Nom du produit (ex: Farine de blé 10kg)'
    )
    
    # Description détaillée
    description = models.TextField(
        blank=True,
        help_text='Description détaillée du produit'
    )
    
    # Prix unitaire (en devises locales)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Prix unitaire du produit'
    )
    
    # Quantité en stock
    quantity_in_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Quantité disponible en stock'
    )
    
    # Prix du jour (peut être modifié par le client/manager)
    daily_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Prix du jour (peut différer du prix standard)'
    )
    
    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date de création du produit'
    )
    
    # Date de dernière modification
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Date de dernière modification'
    )
    
    class Meta:
        db_table = 'sales_product'
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - Stock: {self.quantity_in_stock}"
    
    def get_current_price(self):
        """Obtenir le prix du jour s'il existe, sinon le prix standard"""
        return self.daily_price if self.daily_price else self.price
    
    def is_in_stock(self, quantity):
        """Vérifier si la quantité demandée est en stock"""
        return self.quantity_in_stock >= quantity
    
    def reduce_stock(self, quantity):
        """Réduire le stock après une vente"""
        if self.is_in_stock(quantity):
            self.quantity_in_stock -= quantity
            self.save()
            return True
        return False


# ==================== DISCOUNT MODEL ====================
class Discount(models.Model):
    """
    Modèle pour les réductions
    Permet de créer des réductions sur les produits
    """
    
    # Produit affecté par la réduction
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        help_text='Produit affecté (null = tous les produits)'
    )
    
    # Pourcentage de réduction (0-100%)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Pourcentage de réduction (0-100%)'
    )
    
    # Date de début de la réduction
    start_date = models.DateTimeField(
        help_text='Date de début de la réduction'
    )
    
    # Date de fin de la réduction
    end_date = models.DateTimeField(
        help_text='Date de fin de la réduction'
    )
    
    # Description de la réduction
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Description de la réduction'
    )
    
    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date de création de la réduction'
    )
    
    class Meta:
        db_table = 'sales_discount'
        verbose_name = 'Réduction'
        verbose_name_plural = 'Réductions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.discount_percentage}%"
    
    def is_active(self):
        """Vérifier si la réduction est actuellement active"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def get_discounted_price(self, original_price):
        """Calculer le prix après réduction"""
        if self.is_active():
            discount_amount = original_price * (self.discount_percentage / 100)
            return original_price - discount_amount
        return original_price


# ==================== SALE MODEL ====================
class Sale(models.Model):
    """
    Modèle pour enregistrer les ventes
    Associe un worker à la vente, avec les produits et les quantités
    """
    
    # Worker qui a enregistré la vente
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sales',
        help_text='Utilisateur qui a enregistré la vente'
    )
    
    # Produit vendu
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sales',
        help_text='Produit vendu'
    )
    
    # Quantité vendue
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantité vendue'
    )
    
    # Réduction appliquée (s'il y en a une)
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales',
        help_text='Réduction appliquée à cette vente'
    )
    
    # Prix unitaire au moment de la vente
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Prix unitaire au moment de la vente'
    )
    
    # Prix total (prix_unitaire * quantité - réduction)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Prix total de la vente'
    )
    
    # Date et heure de la vente
    sale_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date et heure de la vente'
    )
    
    class Meta:
        db_table = 'sales_sale'
        verbose_name = 'Vente'
        verbose_name_plural = 'Ventes'
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"Vente de {self.quantity} x {self.product.name} - {self.total_price}"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer le prix total automatiquement"""
        # Calculer le prix total
        self.total_price = self.unit_price * self.quantity
        
        # Appliquer la réduction s'il y en a une
        if self.discount and self.discount.is_active():
            discount_amount = self.total_price * (self.discount.discount_percentage / 100)
            self.total_price -= discount_amount
        
        super().save(*args, **kwargs)


# ==================== INVOICE MODEL ====================
class Invoice(models.Model):
    """
    Modèle pour les factures normalisées
    Génère une facture pour une ou plusieurs ventes
    """
    
    # Numéro de facture unique
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Numéro unique de la facture'
    )
    
    # Worker qui a créé la facture
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text='Utilisateur qui a créé la facture'
    )
    
    # Ventes associées à cette facture
    sales = models.ManyToManyField(
        Sale,
        related_name='invoices',
        help_text='Ventes incluses dans cette facture'
    )
    
    # Montant total de la facture
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Montant total de la facture (calculé après ajout des ventes)'
    )
    
    # Montant payé
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Montant payé'
    )
    
    # Statut de la facture
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('issued', 'Émise'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Statut de la facture'
    )
    
    # Notes ou commentaires
    notes = models.TextField(
        blank=True,
        help_text='Notes ou commentaires sur la facture'
    )
    
    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date de création de la facture'
    )
    
    # Date d'émission
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date d\'émission de la facture'
    )
    
    class Meta:
        db_table = 'sales_invoice'
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Facture #{self.invoice_number} - {self.get_status_display()}"
    
    def calculate_total(self):
        """Calculer le montant total de la facture"""
        total = sum(sale.total_price for sale in self.sales.all())
        self.total_amount = total
        return total
    
    def mark_as_issued(self):
        """Marquer la facture comme émise"""
        self.status = 'issued'
        self.issued_at = timezone.now()
        self.save()
    
    def mark_as_paid(self, amount_paid=None):
        """Marquer la facture comme payée"""
        if amount_paid is None:
            amount_paid = self.total_amount
        self.amount_paid = amount_paid
        self.status = 'paid'
        self.save()
    
    def is_paid(self):
        """Vérifier si la facture est complètement payée"""
        return self.amount_paid >= self.total_amount


# ==================== ACTIVITY LOG MODEL ====================
class ActivityLog(models.Model):
    """
    Modèle pour enregistrer les activités des workers
    Utile pour le suivi des présences et des actions
    """
    
    # ACTION_CHOICES définit les types d'actions possibles
    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('sale', 'Vente enregistrée'),
        ('invoice', 'Facture créée'),
        ('price_change', 'Changement de prix'),
        ('discount_applied', 'Réduction appliquée'),
    ]
    
    # Worker qui a effectué l'action
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activity_logs',
        help_text='Utilisateur qui a effectué l\'action'
    )
    
    # Type d'action effectuée
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='Type d\'action effectuée'
    )
    
    # Description de l'action
    description = models.TextField(
        blank=True,
        help_text='Description détaillée de l\'action'
    )
    
    # Date et heure de l'action
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='Date et heure de l\'action'
    )
    
    # Adresse IP du client (pour les audits de sécurité)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Adresse IP du client'
    )
    
    class Meta:
        db_table = 'sales_activitylog'
        verbose_name = 'Journal d\'activité'
        verbose_name_plural = 'Journaux d\'activité'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.worker.username} - {self.get_action_display()} - {self.timestamp}"


# ==================== DAILY REPORT MODEL ====================
class DailyReport(models.Model):
    """
    Modèle pour les rapports journaliers des ventes
    Agrège les données des ventes pour chaque jour
    """
    
    # Date du rapport
    report_date = models.DateField(
        unique=True,
        help_text='Date du rapport'
    )
    
    # Nombre total de ventes
    total_sales_count = models.IntegerField(
        default=0,
        help_text='Nombre total de ventes'
    )
    
    # Montant total des ventes
    total_sales_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Montant total des ventes'
    )
    
    # Quantité totale vendue
    total_quantity_sold = models.IntegerField(
        default=0,
        help_text='Quantité totale vendue'
    )
    
    # Prix moyen des ventes
    average_sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Prix moyen des ventes'
    )
    
    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date de création du rapport'
    )
    
    class Meta:
        db_table = 'sales_dailyreport'
        verbose_name = 'Rapport journalier'
        verbose_name_plural = 'Rapports journaliers'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Rapport du {self.report_date}"
