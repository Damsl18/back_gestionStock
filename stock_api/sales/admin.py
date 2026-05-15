"""
Configuration de l'interface d'administration Django
Enregistre les modèles pour les gérer via l'interface admin
"""

from django.contrib import admin
from .models import (
    CustomUser, Product, Sale, Invoice, Discount,
    ActivityLog, DailyReport
)


# ===================== CUSTOM USER ADMIN =====================
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Interface admin pour les utilisateurs personnalisés
    Affiche les informations de l'utilisateur et ses statuts
    """
    list_display = [
        'username', 'email', 'role', 'is_locked',
        'failed_login_attempts', 'last_presence'
    ]
    list_filter = ['role', 'is_locked', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Rôle et Permissions', {
            'fields': ('role', 'groups', 'user_permissions')
        }),
        ('Sécurité', {
            'fields': (
                'password', 'is_locked', 'failed_login_attempts'
            ),
            'classes': ('collapse',)
        }),
        ('Activité', {
            'fields': ('last_presence', 'last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']


# ===================== PRODUCT ADMIN =====================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Interface admin pour les produits
    Affiche les informations des produits et le stock
    """
    list_display = [
        'name', 'price', 'daily_price', 'quantity_in_stock', 'created_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Informations du Produit', {
            'fields': ('name', 'description')
        }),
        ('Prix', {
            'fields': ('price', 'daily_price')
        }),
        ('Stock', {
            'fields': ('quantity_in_stock',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# ===================== DISCOUNT ADMIN =====================
@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """
    Interface admin pour les réductions
    Affiche les réductions actives et inactives
    """
    list_display = [
        'product', 'discount_percentage', 'start_date', 'end_date', 'created_at'
    ]
    list_filter = ['start_date', 'end_date', 'created_at']
    search_fields = ['product__name', 'description']
    
    fieldsets = (
        ('Produit', {
            'fields': ('product',)
        }),
        ('Réduction', {
            'fields': ('discount_percentage', 'description')
        }),
        ('Période', {
            'fields': ('start_date', 'end_date')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


# ===================== SALE ADMIN =====================
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Interface admin pour les ventes
    Affiche les ventes enregistrées par les workers
    """
    list_display = [
        'id', 'worker', 'product', 'quantity',
        'unit_price', 'total_price', 'sale_date'
    ]
    list_filter = ['sale_date', 'worker', 'product']
    search_fields = ['worker__username', 'product__name']
    
    fieldsets = (
        ('Informations de la Vente', {
            'fields': ('worker', 'product')
        }),
        ('Détails', {
            'fields': ('quantity', 'unit_price', 'total_price', 'discount')
        }),
        ('Métadonnées', {
            'fields': ('sale_date',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['total_price', 'sale_date']


# ===================== INVOICE ADMIN =====================
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Interface admin pour les factures
    Affiche le statut et les montants des factures
    """
    list_display = [
        'invoice_number', 'worker', 'total_amount',
        'amount_paid', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'issued_at']
    search_fields = ['invoice_number', 'worker__username']
    
    fieldsets = (
        ('Informations de la Facture', {
            'fields': ('invoice_number', 'worker', 'sales')
        }),
        ('Montants', {
            'fields': ('total_amount', 'amount_paid')
        }),
        ('Statut', {
            'fields': ('status', 'notes')
        }),
        ('Dates', {
            'fields': ('created_at', 'issued_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'total_amount']


# ===================== ACTIVITY LOG ADMIN =====================
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Interface admin pour les journaux d'activité
    Affiche les actions effectuées par les workers
    """
    list_display = [
        'worker', 'action', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'worker']
    search_fields = ['worker__username', 'description']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('worker',)
        }),
        ('Activité', {
            'fields': ('action', 'description')
        }),
        ('Informations de Sécurité', {
            'fields': ('timestamp', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['timestamp']


# ===================== DAILY REPORT ADMIN =====================
@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    """
    Interface admin pour les rapports journaliers
    Affiche les statistiques agrégées par jour
    """
    list_display = [
        'report_date', 'total_sales_count', 'total_sales_amount',
        'total_quantity_sold', 'average_sale_price'
    ]
    list_filter = ['report_date', 'created_at']
    search_fields = ['report_date']
    
    fieldsets = (
        ('Date', {
            'fields': ('report_date',)
        }),
        ('Statistiques', {
            'fields': (
                'total_sales_count', 'total_sales_amount',
                'total_quantity_sold', 'average_sale_price'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
