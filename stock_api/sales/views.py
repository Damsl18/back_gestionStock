"""
Vues (Views) pour l'API de gestion des ventes
Définissent les endpoints et la logique métier
Incluent les authentifications, permissions et validations
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    CustomUser, Product, Sale, Invoice, Discount,
    ActivityLog, DailyReport
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserListSerializer, ProductSerializer, SaleSerializer, InvoiceDetailSerializer,
    InvoiceListSerializer, DiscountSerializer, ActivityLogSerializer,
    DailyReportSerializer, WeeklyReportSerializer
)
from .permissions import (
    IsWorker, IsClient, IsSuperAdmin, IsClientOrSuperAdmin,
    IsWorkerOrSuperAdmin, IsOwnerOrAdmin
)
from .throttling import (
    LoginAttemptThrottle, RegistrationAttemptThrottle,
    UserRateThrottle_10_Per_Minute, SaleCreationThrottle,
    PriceChangeThrottle, DiscountThrottle
)


# ==================== AUTHENTICATION VIEWS ====================
class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint pour l'enregistrement des nouveaux utilisateurs
    Accepte les données d'enregistrement et crée un nouvel utilisateur
    
    POST /api/auth/register/
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password",
        "password_confirm": "secure_password",
        "role": "worker",  # ou "client" ou "super_admin"
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationAttemptThrottle]
    
    def create(self, request, *args, **kwargs):
        """Créer un nouvel utilisateur"""
        response = super().create(request, *args, **kwargs)
        
        # Générer un token d'authentification pour l'utilisateur
        if response.status_code == status.HTTP_201_CREATED:
            user = CustomUser.objects.get(username=request.data.get('username'))
            token, _ = Token.objects.get_or_create(user=user)
            response.data['token'] = token.key
            response.data['message'] = 'Utilisateur créé avec succès'
        
        return response


class UserLoginView(generics.GenericAPIView):
    """
    Endpoint pour la connexion des utilisateurs
    Vérifie les identifiants et retourne un token d'authentification
    Implémente la protection contre le brute force (maximum 3 tentatives)
    
    POST /api/auth/login/
    {
        "username": "john_doe",
        "password": "secure_password"
    }
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginAttemptThrottle]
    
    def post(self, request, *args, **kwargs):
        """Authentifier l'utilisateur et retourner un token"""
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Enregistrer l'activité en cas d'échec de connexion
            username = request.data.get('username')
            try:
                user = CustomUser.objects.get(username=username)
                try:
                    ActivityLog.objects.create(
                        worker=user if user.is_worker() else None,
                        action='login', description='Tentative échouée',
                        ip_address=self.get_client_ip(request)
                    )
                except Exception:
                    pass
            except Exception:
                pass
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = serializer.validated_data['user']
        
        # Générer ou obtenir le token
        token, _ = Token.objects.get_or_create(user=user)
        
        try:
            ActivityLog.objects.create(
                worker=user if user.is_worker() else None,
                action='login', description='Connexion réussie',
                ip_address=self.get_client_ip(request)
            )
        except Exception:
            pass
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'message': 'Connexion réussie'
        }, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class UserLogoutView(generics.GenericAPIView):
    """
    Endpoint pour la déconnexion des utilisateurs
    Supprime le token d'authentification et enregistre l'activité
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Déconnecter l'utilisateur"""
        try:
            # Supprimer le token
            Token.objects.get(user=request.user).delete()
            
            # Enregistrer l'activité de déconnexion
            if request.user.is_worker():
                try:
                    ActivityLog.objects.create(
                        worker=request.user, action='logout', description='Déconnexion',
                        ip_address=self.get_client_ip(request)
                    )
                except Exception:
                    pass
        except:
            pass
        
        return Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_200_OK
        )
    
    def get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


# ==================== USER MANAGEMENT VIEWS ====================
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs
    Les super admins peuvent créer/modifier/supprimer des users
    Les clients peuvent créer/modifier des workers
    Chaque utilisateur peut voir son propre profil
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle_10_Per_Minute]
    
    def get_serializer_class(self):
        """Retourner le bon sérialiseur selon l'action"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserProfileSerializer
        return UserProfileSerializer
    
    def get_queryset(self):
        """Filtrer les utilisateurs selon le rôle"""
        user = self.request.user
        
        if user.is_super_admin():
            # Super admins voient tous les utilisateurs
            return CustomUser.objects.all()
        elif user.is_client():
            # Les clients voient les workers uniquement
            return CustomUser.objects.filter(role='worker')
        else:
            # Les workers ne voient que leur propre profil
            return CustomUser.objects.filter(id=user.id)
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'destroy']:
            return [IsClientOrSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]  # FIX: workers peuvent mettre à jour le stock
        elif self.action == 'list':
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint pour obtenir les informations du profil de l'utilisateur actuel
        
        GET /api/users/me/
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def unlock_account(self, request, pk=None):
        """
        Endpoint pour déverrouiller un compte verrouillé
        Seuls les super admins peuvent déverrouiller les comptes
        
        POST /api/users/{user_id}/unlock_account/
        """
        # Vérifier les permissions
        if not request.user.is_super_admin():
            return Response(
                {'error': 'Seul un super admin peut déverrouiller un compte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.unlock_account()
        
        return Response(
            {'message': f'Compte de {user.username} déverrouillé avec succès'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def activities(self, request):
        """
        Endpoint pour voir les activités de l'utilisateur actuel (workers uniquement)
        
        GET /api/users/activities/
        """
        if not request.user.is_worker():
            return Response(
                {'error': 'Seuls les workers ont des activités enregistrées'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        activities = ActivityLog.objects.filter(worker=request.user)
        serializer = ActivityLogSerializer(activities, many=True)
        return Response(serializer.data)


# ==================== PRODUCT VIEWS ====================
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des produits (sacs de farines)
    Les clients peuvent voir et modifier les produits
    Les workers peuvent voir les produits
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle_10_Per_Minute]
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'destroy']:
            return [IsClientOrSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]  # FIX: workers peuvent update le stock
        else:
            return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Endpoint pour voir les produits avec stock faible
        Retourne les produits avec moins de 10 unités en stock
        
        GET /api/products/low_stock/
        """
        low_stock_products = Product.objects.filter(quantity_in_stock__lt=10)
        serializer = ProductSerializer(low_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_daily_price(self, request):
        """
        Endpoint pour mettre à jour les prix du jour
        Seuls les clients/super admins peuvent faire cela
        
        POST /api/products/update_daily_price/
        {
            "products": [
                {"id": 1, "daily_price": 15.99},
                {"id": 2, "daily_price": 12.50}
            ]
        }
        """
        if not request.user.is_client() and not request.user.is_super_admin():
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        products_data = request.data.get('products', [])
        updated_products = []
        
        for product_data in products_data:
            try:
                product = Product.objects.get(id=product_data.get('id'))
                product.daily_price = product_data.get('daily_price')
                product.save()
                updated_products.append(product)
                
                # Enregistrer l'activité
                try:
                    ActivityLog.objects.create(
                        worker=request.user if request.user.is_worker() else None,
                        action='price_change', description=f'Changement de prix pour {product.name}',
                        ip_address=self.get_client_ip(request)
                    )
                except Exception:
                    pass
            except Product.DoesNotExist:
                pass
        
        serializer = ProductSerializer(updated_products, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


# ==================== SALE VIEWS ====================
class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des ventes
    Les workers peuvent créer des ventes
    Les clients et super admins peuvent voir et gérer toutes les ventes
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [SaleCreationThrottle]
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action == 'create':
            return [IsAuthenticated()]  # workers + clients
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        else:
            return [IsAuthenticated()]
    
    def get_serializer_context(self):
        """Passer la requête au sérialiseur"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def today_sales(self, request):
        """
        Endpoint pour voir les ventes d'aujourd'hui
        
        GET /api/sales/today_sales/
        """
        today = timezone.now().date()
        today_sales = Sale.objects.filter(sale_date__date=today)
        
        if request.user.is_worker():
            # Les workers ne voient que leurs propres ventes
            today_sales = today_sales.filter(worker=request.user)
        
        serializer = SaleSerializer(today_sales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sales_statistics(self, request):
        """
        Endpoint pour voir les statistiques des ventes
        
        GET /api/sales/sales_statistics/
        Paramètres:
            - date_from: Date de début (YYYY-MM-DD)
            - date_to: Date de fin (YYYY-MM-DD)
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        sales = Sale.objects.all()
        
        # Filtrer par date
        if date_from:
            try:
                date_from = parse_date(date_from)
                sales = sales.filter(sale_date__date__gte=date_from)
            except:
                pass
        
        if date_to:
            try:
                date_to = parse_date(date_to)
                sales = sales.filter(sale_date__date__lte=date_to)
            except:
                pass
        
        # Filtrer par worker si l'utilisateur est un worker
        if request.user.is_worker():
            sales = sales.filter(worker=request.user)
        
        # Calculer les statistiques
        stats = {
            'total_sales_count': sales.count(),
            'total_sales_amount': sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0'),
            'total_quantity_sold': sales.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'average_sale_price': sales.aggregate(Avg('total_price'))['total_price__avg'] or Decimal('0'),
        }
        
        return Response(stats)


# ==================== INVOICE VIEWS ====================
class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des factures
    Les workers peuvent créer des factures
    Les clients et super admins peuvent voir et gérer les factures
    """
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle_10_Per_Minute]
    
    def get_serializer_class(self):
        """Retourner le bon sérialiseur selon l'action"""
        if self.action == 'list':
            return InvoiceListSerializer
        else:
            return InvoiceDetailSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action == 'create':
            return [IsAuthenticated()]  # workers + clients
        elif self.action in ['update', 'partial_update']:
            return [IsSuperAdmin()]
        else:
            return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Créer une facture"""
        # Générer un numéro de facture unique
        invoice_number = self.generate_invoice_number()
        
        request_data = dict(request.data)
        request_data['invoice_number'] = invoice_number
        request_data['worker'] = request.user.id
        if 'sales' in request_data:
            request_data['sales_ids'] = request_data['sales']
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        try:
            ActivityLog.objects.create(
                worker=request.user if request.user.is_worker() else None,
                action='invoice',
                description=f'Facture créée: {invoice_number}',
                ip_address=self.get_client_ip(request)
            )
        except Exception:
            pass
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def generate_invoice_number(self):
        """Générer un numéro de facture unique"""
        from django.utils.text import slugify
        import uuid
        
        # Format: INV-YYYYMMDD-XXXXXX (ex: INV-20240510-ABC123)
        today = timezone.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:6].upper()
        return f'INV-{today}-{unique_id}'
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """
        Endpoint pour marquer une facture comme payée
        
        POST /api/invoices/{invoice_id}/mark_as_paid/
        {
            "amount_paid": 100.00  # Optionnel, sinon le montant total
        }
        """
        invoice = self.get_object()
        
        amount_paid = request.data.get('amount_paid')
        if amount_paid:
            invoice.mark_as_paid(Decimal(str(amount_paid)))
        else:
            invoice.mark_as_paid()
        
        serializer = InvoiceDetailSerializer(invoice)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_issued(self, request, pk=None):
        """
        Endpoint pour marquer une facture comme émise
        
        POST /api/invoices/{invoice_id}/mark_as_issued/
        """
        invoice = self.get_object()
        
        invoice.mark_as_issued()
        serializer = InvoiceDetailSerializer(invoice)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


# ==================== DISCOUNT VIEWS ====================
class DiscountViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des réductions
    Seuls les clients et super admins peuvent créer/modifier les réductions
    """
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [DiscountThrottle]
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'destroy']:
            return [IsClientOrSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]  # FIX: workers peuvent update le stock
        else:
            return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def active_discounts(self, request):
        """
        Endpoint pour voir les réductions actuellement actives
        
        GET /api/discounts/active_discounts/
        """
        now = timezone.now()
        active_discounts = Discount.objects.filter(
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = DiscountSerializer(active_discounts, many=True)
        return Response(serializer.data)


# ==================== REPORT VIEWS ====================
class DailyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour voir les rapports journaliers
    """
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer
    permission_classes = [IsAuthenticated]  # FIX: client peut voir les rapports
    throttle_classes = [UserRateThrottle_10_Per_Minute]


class WeeklyReportView(generics.GenericAPIView):
    """
    Endpoint pour voir le rapport hebdomadaire
    Affiche les statistiques agrégées de la semaine actuelle
    
    GET /api/reports/weekly/
    """
    permission_classes = [IsAuthenticated]  # FIX: client peut voir le rapport
    throttle_classes = [UserRateThrottle_10_Per_Minute]
    
    def get(self, request):
        """Générer et retourner le rapport hebdomadaire"""
        weekly_data = WeeklyReportSerializer.generate_weekly_report()
        serializer = WeeklyReportSerializer(weekly_data)
        return Response(serializer.data)


class AverageSalesView(generics.GenericAPIView):
    """
    Endpoint pour voir la moyenne de ventes
    Affiche la moyenne des ventes pour les 7 derniers jours
    
    GET /api/reports/average_sales/
    """
    permission_classes = [IsAuthenticated]  # FIX: client peut voir les stats
    throttle_classes = [UserRateThrottle_10_Per_Minute]
    
    def get(self, request):
        """Calculer la moyenne de ventes"""
        # Récupérer les ventes des 7 derniers jours
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_sales = Sale.objects.filter(sale_date__gte=seven_days_ago)
        
        # Calculer les statistiques
        total_sales = recent_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
        total_count = recent_sales.count()
        average_sale = total_sales / total_count if total_count > 0 else Decimal('0')
        
        return Response({
            'period': '7 derniers jours',
            'total_sales': str(total_sales),
            'total_sales_count': total_count,
            'average_sale_price': str(average_sale),
            'average_sales_per_day': str(total_sales / 7) if total_count > 0 else '0',
        })
