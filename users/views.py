from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from coopec.pagination import StandardResultsSetPagination
from .models import Membre, Client, Cooperative
from .serializers import MembreSerializer, ClientSerializer, CooperativeSerializer
from .permissions import IsAdminOrSuperAdmin, IsOwnerOrAdmin
from .email_config import set_smtp_config, get_smtp_config, clear_smtp_config, get_smtp_backend, get_default_from_email
from .smtp_serializers import SMTPConfigSerializer, SMTPConfigReadSerializer
from django.conf import settings

@extend_schema(tags=['Coopératives'])
class CooperativeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les coopératives.
    Supporte toutes les opérations CRUD : GET, POST, PUT, PATCH, DELETE
    Accessible uniquement aux ADMIN et SUPERADMIN
    
    IMPORTANT : Le système n'autorise qu'une seule coopérative.
    Si une coopérative existe déjà, la création d'une nouvelle sera refusée.
    """
    queryset = Cooperative.objects.all()
    serializer_class = CooperativeSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination
    
    def create(self, request, *args, **kwargs):
        """
        Empêche la création d'une nouvelle coopérative si une existe déjà.
        Le système n'autorise qu'une seule coopérative.
        """
        # Vérifier si une coopérative existe déjà
        if Cooperative.objects.exists():
            return Response(
                {
                    'error': 'Une coopérative existe déjà dans le système.',
                    'message': 'Il ne peut y avoir qu\'une seule coopérative. Veuillez modifier la coopérative existante ou la supprimer avant d\'en créer une nouvelle.',
                    'detail': 'Il y a déjà une coopérative existante. Le système n\'autorise qu\'une seule coopérative.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si aucune coopérative n'existe, procéder à la création normale
        return super().create(request, *args, **kwargs)
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête pour générer les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_serializer(self, *args, **kwargs):
        """S'assurer que le contexte est toujours passé au serializer"""
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)

@extend_schema(tags=['Membres'])
class MembreViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les membres.
    - ADMIN et SUPERADMIN : accès complet
    - MEMBRE : peut voir uniquement son propre profil
    """
    queryset = Membre.objects.all()
    serializer_class = MembreSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les membres selon le type d'utilisateur
        """
        user = self.request.user
        if user.user_type in ['SUPERADMIN', 'ADMIN']:
            return Membre.objects.all()
        elif user.user_type == 'MEMBRE' and user.membre:
            return Membre.objects.filter(id=user.membre.id)
        return Membre.objects.none()
    
    def get_permissions(self):
        """
        Permissions selon l'action
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête pour générer les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @extend_schema(
        summary="Rechercher un membre par numéro de compte",
        description="Permet de récupérer un membre en utilisant son numéro de compte (ex: MB-2026-00001) au lieu de l'ID",
        parameters=[
            OpenApiParameter(
                name='numero_compte',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Numéro de compte du membre (ex: MB-2026-00001)"
            )
        ],
        responses={200: MembreSerializer, 404: None}
    )
    @action(detail=False, methods=['get'], url_path='par-compte/(?P<numero_compte>[^/.]+)')
    def par_compte(self, request, numero_compte=None):
        """
        Recherche un membre par son numéro de compte
        Exemple: GET /api/membres/par-compte/MB-2026-00001/
        """
        try:
            membre = Membre.objects.get(numero_compte=numero_compte)
            # Vérifier les permissions
            user = request.user
            if user.user_type not in ['SUPERADMIN', 'ADMIN']:
                if user.user_type == 'MEMBRE' and user.membre.id != membre.id:
                    return Response(
                        {'detail': 'Vous n\'avez pas la permission d\'accéder à ce membre.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = self.get_serializer(membre)
            return Response(serializer.data)
        except Membre.DoesNotExist:
            return Response(
                {'detail': f'Aucun membre trouvé avec le numéro de compte "{numero_compte}".'},
                status=status.HTTP_404_NOT_FOUND
            )

@extend_schema(tags=['Clients'])
class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les clients.
    - ADMIN et SUPERADMIN : accès complet
    - CLIENT : peut voir uniquement son propre profil
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les clients selon le type d'utilisateur
        """
        user = self.request.user
        if user.user_type in ['SUPERADMIN', 'ADMIN']:
            return Client.objects.all()
        elif user.user_type == 'CLIENT' and user.client:
            return Client.objects.filter(id=user.client.id)
        return Client.objects.none()
    
    def get_permissions(self):
        """
        Permissions selon l'action
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête pour générer les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @extend_schema(
        summary="Rechercher un client par numéro de compte",
        description="Permet de récupérer un client en utilisant son numéro de compte (ex: CL-2026-00001) au lieu de l'ID",
        parameters=[
            OpenApiParameter(
                name='numero_compte',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Numéro de compte du client (ex: CL-2026-00001)"
            )
        ],
        responses={200: ClientSerializer, 404: None}
    )
    @action(detail=False, methods=['get'], url_path='par-compte/(?P<numero_compte>[^/.]+)')
    def par_compte(self, request, numero_compte=None):
        """
        Recherche un client par son numéro de compte
        Exemple: GET /api/clients/par-compte/CL-2026-00001/
        """
        try:
            client = Client.objects.get(numero_compte=numero_compte)
            # Vérifier les permissions
            user = request.user
            if user.user_type not in ['SUPERADMIN', 'ADMIN']:
                if user.user_type == 'CLIENT' and user.client.id != client.id:
                    return Response(
                        {'detail': 'Vous n\'avez pas la permission d\'accéder à ce client.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = self.get_serializer(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response(
                {'detail': f'Aucun client trouvé avec le numéro de compte "{numero_compte}".'},
                status=status.HTTP_404_NOT_FOUND
            )