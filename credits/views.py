from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from coopec.pagination import StandardResultsSetPagination
from users.permissions import IsAdminOrSuperAdmin
from .models import  Credit, Remboursement
from .serializers import CreditSerializer, RemboursementSerializer


@extend_schema(tags=['Crédits'])
class CreditViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les crédits.
    - ADMIN et SUPERADMIN : voient tous les crédits
    - MEMBRE : voit uniquement ses propres crédits
    - CLIENT : voit uniquement ses propres crédits
    """
    queryset = Credit.objects.all()
    serializer_class = CreditSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les crédits selon le type d'utilisateur connecté
        """
        user = self.request.user
        
        # ADMIN et SUPERADMIN voient tout
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            return Credit.objects.all()
        
        # MEMBRE voit uniquement ses propres crédits
        if user.user_type == 'MEMBRE' and user.membre:
            return Credit.objects.filter(membre=user.membre)
        
        # CLIENT voit uniquement ses propres crédits
        if user.user_type == 'CLIENT' and user.client:
            return Credit.objects.filter(client=user.client)
        
        # Par défaut, retourner un queryset vide
        return Credit.objects.none()


@extend_schema(tags=['Crédits'])
class RemboursementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les remboursements.
    - ADMIN et SUPERADMIN : voient tous les remboursements
    - MEMBRE : voit uniquement les remboursements de ses crédits
    - CLIENT : voit uniquement les remboursements de ses crédits
    """
    queryset = Remboursement.objects.all()
    serializer_class = RemboursementSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les remboursements selon le type d'utilisateur connecté
        """
        user = self.request.user
        
        # ADMIN et SUPERADMIN voient tout
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            return Remboursement.objects.all()
        
        # MEMBRE voit uniquement les remboursements de ses crédits
        if user.user_type == 'MEMBRE' and user.membre:
            return Remboursement.objects.filter(credit__membre=user.membre)
        
        # CLIENT voit uniquement les remboursements de ses crédits
        if user.user_type == 'CLIENT' and user.client:
            return Remboursement.objects.filter(credit__client=user.client)
        
        # Par défaut, retourner un queryset vide
        return Remboursement.objects.none()
