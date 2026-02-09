"""
Classes de permissions personnalisées pour les 4 types d'utilisateurs
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission uniquement pour SUPERADMIN
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'SUPERADMIN'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission pour ADMIN (et SUPERADMIN qui a tous les droits)
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type in ['ADMIN', 'SUPERADMIN']
        )


class IsMembre(permissions.BasePermission):
    """
    Permission pour MEMBRE uniquement
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'MEMBRE'
        )


class IsClient(permissions.BasePermission):
    """
    Permission pour CLIENT uniquement
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'CLIENT'
        )


class IsMembreOrClient(permissions.BasePermission):
    """
    Permission pour MEMBRE ou CLIENT
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type in ['MEMBRE', 'CLIENT']
        )


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Permission pour ADMIN ou SUPERADMIN
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type in ['ADMIN', 'SUPERADMIN']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour le propriétaire de la ressource ou Admin/SuperAdmin
    Utile pour que les membres/clients voient uniquement leurs propres données
    """
    def has_object_permission(self, request, view, obj):
        # SuperAdmin et Admin ont accès à tout
        if request.user.user_type in ['SUPERADMIN', 'ADMIN']:
            return True
        
        # Membre peut voir uniquement ses propres données
        if request.user.user_type == 'MEMBRE' and request.user.membre:
            if hasattr(obj, 'membre') and obj.membre == request.user.membre:
                return True
            if hasattr(obj, 'titulaire_membre') and obj.titulaire_membre == request.user.membre:
                return True
            if hasattr(obj, 'titulaire_client') and obj.titulaire_client:
                return False  # Les membres ne peuvent pas voir les données des clients
        
        # Client peut voir uniquement ses propres données
        if request.user.user_type == 'CLIENT' and request.user.client:
            if hasattr(obj, 'client') and obj.client == request.user.client:
                return True
            if hasattr(obj, 'titulaire_client') and obj.titulaire_client == request.user.client:
                return True
            if hasattr(obj, 'titulaire_membre') and obj.titulaire_membre:
                return False  # Les clients ne peuvent pas voir les données des membres
        
        return False
