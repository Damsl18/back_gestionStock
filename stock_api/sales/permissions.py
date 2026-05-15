"""
Permissions personnalisées pour contrôler l'accès aux endpoints
Assure que seuls les utilisateurs autorisés peuvent accéder aux ressources
"""

from rest_framework import permissions


# ==================== CUSTOM PERMISSIONS ====================
class IsWorker(permissions.BasePermission):
    """
    Permutation pour vérifier si l'utilisateur est un worker
    Les workers peuvent enregistrer les ventes et créer des factures
    """
    message = "Vous devez être un worker pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur est authentifié et est un worker"""
        return request.user and request.user.is_authenticated and request.user.is_worker()


class IsClient(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est un client/manager
    Les clients peuvent gérer les prix, réductions et voir les rapports
    """
    message = "Vous devez être un client/manager pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur est authentifié et est un client"""
        return request.user and request.user.is_authenticated and request.user.is_client()


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est un super admin
    Les super admins ont accès à toutes les fonctionnalités
    """
    message = "Vous devez être un super admin pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur est authentifié et est un super admin"""
        return request.user and request.user.is_authenticated and request.user.is_super_admin()


class IsClientOrSuperAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est un client ou super admin
    """
    message = "Vous devez être un client ou super admin pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur est client ou super admin"""
        return (request.user and request.user.is_authenticated and 
                (request.user.is_client() or request.user.is_super_admin()))


class IsWorkerOrSuperAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est un worker ou super admin
    """
    message = "Vous devez être un worker ou super admin pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        """Vérifier si l'utilisateur est worker ou super admin"""
        return (request.user and request.user.is_authenticated and 
                (request.user.is_worker() or request.user.is_super_admin()))


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est le propriétaire ou admin
    Utilisée pour contrôler l'accès aux ressources personnelles
    """
    message = "Vous n'avez pas la permission d'accéder à cette ressource."
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifier si l'utilisateur est le propriétaire ou un admin
        """
        # Les super admins ont toujours accès
        if request.user.is_super_admin():
            return True
        
        # Vérifier si c'est le propriétaire
        if hasattr(obj, 'worker'):
            return obj.worker == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False
