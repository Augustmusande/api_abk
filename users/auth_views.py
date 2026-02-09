"""
Vues pour l'authentification
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from .auth_serializers import (
    LoginSerializer,
    RegisterMembreSerializer,
    RegisterClientSerializer,
    RegisterAdminSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ChangeMembreClientPasswordSerializer
)
from .serializers import MembreSerializer, ClientSerializer
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin

User = get_user_model()


@extend_schema(
    summary="Connexion (Login)",
    description="Endpoint de connexion pour tous les types d'utilisateurs. Accepte username ou email + password.",
    request=LoginSerializer,
    responses={
        200: {
            'description': 'Connexion réussie',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 1,
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'user_type': 'ADMIN',
                        'user_type_display': 'Administrateur'
                    }
                }
            }
        },
        400: {'description': 'Identifiants invalides'}
    },
    tags=['Authentification']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint de connexion
    POST /api/auth/login/
    
    Body:
    {
        "username": "admin" ou "email": "admin@example.com",
        "password": "password123"
    }
    
    Retourne:
    {
        "access": "token...",
        "refresh": "token...",
        "user": {...}
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        # Mettre à jour last_login
        user.save()
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Inscription Membre",
    description="Endpoint d'inscription pour un membre. Crée automatiquement le Membre ET le compte User. Accepte tous les champs du modèle Membre.",
    request=RegisterMembreSerializer,
    responses={
        201: {
            'description': 'Compte créé avec succès',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 2,
                        'username': 'membre_MB-2025-00001',
                        'email': 'membre@example.com',
                        'user_type': 'MEMBRE',
                        'user_type_display': 'Membre'
                    },
                    'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
                }
            }
        },
        400: {'description': 'Erreur de validation'}
    },
    tags=['Authentification']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_membre_view(request):
    """
    Endpoint d'inscription pour un membre
    POST /api/auth/register/membre/
    
    Crée automatiquement le Membre ET le compte User en une seule opération.
    
    Body (Personne physique):
    {
        "email": "membre@example.com",
        "password": "Password123!@#",
        "telephone": "+243900000000",
        "type_membre": "PHYSIQUE",
        "nom": "Doe",
        "prenom": "John",
        "sexe": "M",
        "date_naissance": "1990-01-01",
        "adresse": "123 Rue Example"
    }
    
    Body (Personne morale):
    {
        "email": "entreprise@example.com",
        "password": "Password123!@#",
        "telephone": "+243900000000",
        "type_membre": "MORALE",
        "raison_sociale": "Entreprise Example SARL",
        "sigle": "EEX",
        "forme_juridique": "SARL",
        "adresse": "123 Rue Example"
    }
    
    Retourne:
    {
        "access": "token...",
        "refresh": "token...",
        "user": {...}
    }
    """
    serializer = RegisterMembreSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Inscription Client",
    description="Endpoint d'inscription pour un client. Crée un compte User lié au client existant.",
    request=RegisterClientSerializer,
    responses={
        201: {
            'description': 'Compte créé avec succès',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 3,
                        'username': 'client_CL-2025-00001',
                        'email': 'client@example.com',
                        'user_type': 'CLIENT'
                    },
                    'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
                }
            }
        },
        400: {'description': 'Erreur de validation'}
    },
    tags=['Authentification']
)
@extend_schema(
    summary="Inscription Client",
    description="Endpoint d'inscription pour un client. Crée un compte User lié au client existant.",
    request=RegisterClientSerializer,
    responses={
        201: {
            'description': 'Compte créé avec succès',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 3,
                        'username': 'client_CL-2025-00001',
                        'email': 'client@example.com',
                        'user_type': 'CLIENT',
                        'user_type_display': 'Client'
                    },
                    'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
                }
            }
        },
        400: {'description': 'Erreurs de validation'}
    },
    tags=['Authentification']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_client_view(request):
    """
    Endpoint d'inscription pour un client
    POST /api/auth/register/client/
    
    Crée automatiquement le Client ET le compte User en une seule opération.
    
    Body:
    {
        "email": "client@example.com",
        "password": "Password123!@#",
        "nom": "Doe",
        "prenom": "Jane",
        "sexe": "F",
        "telephone": "+243900000000",
        "date_naissance": "1995-05-15",
        "adresse": "123 Rue Example",
        "profession": "Ingénieur",
        "postnom": "Smith",
        "parrain_id": 1  // Optionnel: ID du membre parrain
    }
    
    Retourne:
    {
        "access": "token...",
        "refresh": "token...",
        "user": {...}
    }
    """
    serializer = RegisterClientSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Déconnexion (Logout)",
    description="Endpoint de déconnexion. Blackliste le refresh token pour invalider la session.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh token à blacklister'
                }
            }
        }
    },
    responses={
        200: {
            'description': 'Déconnexion réussie',
            'examples': {
                'application/json': {
                    'message': 'Déconnexion réussie.'
                }
            }
        },
        400: {'description': 'Erreur lors de la déconnexion'}
    },
    tags=['Authentification']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Endpoint de déconnexion
    POST /api/auth/logout/
    
    Nécessite un token valide dans le header Authorization
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Déconnexion réussie.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Erreur lors de la déconnexion.',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Inscription Admin/SuperAdmin",
    description="Endpoint d'inscription pour un ADMIN ou SUPERADMIN. Nécessite d'être authentifié en tant qu'ADMIN ou SUPERADMIN. Seul un SUPERADMIN peut créer un SUPERADMIN.",
    request=RegisterAdminSerializer,
    responses={
        201: {
            'description': 'Compte créé avec succès',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 4,
                        'username': 'admin1',
                        'email': 'admin1@coopec.com',
                        'user_type': 'ADMIN',
                        'user_type_display': 'Administrateur'
                    },
                    'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
                }
            }
        },
        400: {'description': 'Erreur de validation'},
        403: {
            'description': 'Permission refusée',
            'examples': {
                'application/json': {
                    'error': 'Seul un SUPERADMIN peut créer un compte SUPERADMIN.'
                }
            }
        }
    },
    tags=['Authentification']
)
@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def register_admin_view(request):
    """
    Endpoint d'inscription pour un ADMIN ou SUPERADMIN
    POST /api/auth/register/admin/
    
    Nécessite d'être connecté en tant qu'ADMIN ou SUPERADMIN
    Seul un SUPERADMIN peut créer un SUPERADMIN
    
    Body:
    {
        "username": "admin",
        "email": "admin@example.com",  // Optionnel
        "password": "Password123!@#",
        "first_name": "John",  // Optionnel
        "last_name": "Doe",  // Optionnel
        "user_type": "ADMIN"  // "ADMIN" ou "SUPERADMIN"
    }
    
    Retourne:
    {
        "access": "token...",
        "refresh": "token...",
        "user": {...}
    }
    """
    # Vérifier que seul un SUPERADMIN peut créer un SUPERADMIN
    user_type = request.data.get('user_type', 'ADMIN')
    if user_type == 'SUPERADMIN' and request.user.user_type != 'SUPERADMIN':
        return Response(
            {'error': 'Seul un SUPERADMIN peut créer un compte SUPERADMIN.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = RegisterAdminSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'message': 'Compte créé avec succès. Vous êtes maintenant connecté.'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Informations utilisateur connecté",
    description="Endpoint pour obtenir les informations de l'utilisateur actuellement connecté.",
    responses={
        200: {
            'description': 'Informations de l\'utilisateur',
            'examples': {
                'application/json': {
                    'id': 1,
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'user_type': 'ADMIN',
                    'user_type_display': 'Administrateur',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'date_joined': '2025-01-15T10:00:00Z',
                    'last_login': '2025-01-15T12:00:00Z'
                }
            }
        },
        401: {'description': 'Non authentifié'}
    },
    tags=['Authentification']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Endpoint pour obtenir les informations de l'utilisateur connecté
    GET /api/auth/me/
    
    Nécessite un token valide dans le header Authorization
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Liste des administrateurs",
    description="Endpoint pour récupérer la liste de tous les utilisateurs ADMIN et SUPERADMIN. Accessible uniquement aux SUPERADMIN.",
    responses={
        200: {
            'description': 'Liste des administrateurs',
            'examples': {
                'application/json': {
                    'count': 2,
                    'results': [
                        {
                            'id': 1,
                            'username': 'superadmin',
                            'email': 'superadmin@coopec.com',
                            'user_type': 'SUPERADMIN',
                            'user_type_display': 'Super Administrateur',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'is_active': True,
                            'date_joined': '2025-01-15T10:00:00Z',
                            'last_login': '2025-01-15T12:00:00Z'
                        },
                        {
                            'id': 2,
                            'username': 'admin1',
                            'email': 'admin1@coopec.com',
                            'user_type': 'ADMIN',
                            'user_type_display': 'Administrateur',
                            'first_name': 'Jane',
                            'last_name': 'Smith',
                            'is_active': True,
                            'date_joined': '2025-01-16T10:00:00Z',
                            'last_login': None
                        }
                    ]
                }
            }
        },
        403: {'description': 'Permission refusée - Seul un SUPERADMIN peut accéder à cette liste'}
    },
    tags=['Gestion des administrateurs']
)
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_admins_view(request):
    """
    Endpoint pour récupérer la liste de tous les utilisateurs ADMIN et SUPERADMIN
    GET /api/auth/admins/
    
    Accessible uniquement aux SUPERADMIN
    
    Retourne:
    {
        "count": 2,
        "results": [
            {
                "id": 1,
                "username": "superadmin",
                "email": "superadmin@coopec.com",
                "user_type": "SUPERADMIN",
                ...
            },
            ...
        ]
    }
    """
    # Filtrer uniquement les utilisateurs ADMIN et SUPERADMIN
    admins = User.objects.filter(user_type__in=['ADMIN', 'SUPERADMIN']).order_by('-date_joined')
    
    # Sérialiser les résultats
    serializer = UserSerializer(admins, many=True)
    
    return Response({
        'count': admins.count(),
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Modifier le mot de passe d'un administrateur",
    description="Endpoint pour modifier le mot de passe d'un utilisateur ADMIN ou SUPERADMIN. Un SUPERADMIN peut modifier le mot de passe de n'importe quel ADMIN/SUPERADMIN. Un ADMIN peut modifier uniquement son propre mot de passe.",
    request=ChangePasswordSerializer,
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID de l\'utilisateur ADMIN ou SUPERADMIN dont le mot de passe doit être modifié',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Mot de passe modifié avec succès',
            'examples': {
                'application/json': {
                    'message': 'Mot de passe modifié avec succès.'
                }
            }
        },
        400: {
            'description': 'Erreur de validation',
            'examples': {
                'application/json': {
                    'new_password': ['Le mot de passe doit contenir au moins 6 caractères avec des lettres, chiffres et caractères spéciaux.']
                }
            }
        },
        403: {
            'description': 'Permission refusée',
            'examples': {
                'application/json': {
                    'error': 'Vous ne pouvez modifier que votre propre mot de passe.'
                }
            }
        },
        404: {
            'description': 'Utilisateur non trouvé',
            'examples': {
                'application/json': {
                    'error': 'Utilisateur non trouvé ou n\'est pas un administrateur.'
                }
            }
        }
    },
    tags=['Gestion des administrateurs']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_admin_password_view(request, user_id):
    """
    Endpoint pour modifier le mot de passe d'un utilisateur ADMIN ou SUPERADMIN
    POST /api/auth/admins/{user_id}/change-password/
    
    - SUPERADMIN : peut modifier le mot de passe de n'importe quel ADMIN/SUPERADMIN
    - ADMIN : peut modifier uniquement son propre mot de passe
    
    Body:
    {
        "new_password": "NewPassword123!@#"
    }
    
    Retourne:
    {
        "message": "Mot de passe modifié avec succès."
    }
    """
    try:
        target_user = User.objects.get(id=user_id, user_type__in=['ADMIN', 'SUPERADMIN'])
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur non trouvé ou n\'est pas un administrateur.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Vérifier les permissions
    current_user = request.user
    
    # Un ADMIN ne peut modifier que son propre mot de passe
    if current_user.user_type == 'ADMIN' and current_user.id != target_user.id:
        return Response(
            {'error': 'Vous ne pouvez modifier que votre propre mot de passe.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Un SUPERADMIN peut modifier n'importe quel mot de passe ADMIN/SUPERADMIN
    # Un ADMIN peut modifier son propre mot de passe
    if current_user.user_type not in ['SUPERADMIN', 'ADMIN']:
        return Response(
            {'error': 'Vous n\'avez pas la permission de modifier les mots de passe des administrateurs.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Valider et changer le mot de passe
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        
        # Changer le mot de passe
        target_user.set_password(new_password)
        target_user.save()
        
        return Response(
            {'message': 'Mot de passe modifié avec succès.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

