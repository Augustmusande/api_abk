"""
Vues pour la gestion du profil des membres et clients
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from .auth_serializers import ChangeMembreClientPasswordSerializer
from .serializers import MembreSerializer, ClientSerializer


@extend_schema(
    summary="Consulter et modifier le profil du membre connecté",
    description="""
    Endpoint pour qu'un membre consulte et modifie son propre profil.
    
    **GET** : Consulter son profil complet
    **PUT** : Modifier tous les champs du profil
    **PATCH** : Modifier certains champs du profil
    
    **Champs modifiables** :
    - Informations personnelles : nom, prenom, postnom, sexe, date_naissance
    - Contact : email, telephone, adresse, ville
    - Profession : profession
    - Photo : photo_profil
    - Autres : annee_adhesion
    
    **Champs protégés (non modifiables)** :
    - numero_compte (généré automatiquement)
    - date_adhesion (date de création)
    - actif (géré automatiquement)
    - type_membre (personne physique/morale)
    - password (utiliser l'endpoint dédié /api/auth/membre/change-password/)
    
    **Sécurité** : Seul le membre connecté peut accéder à son propre profil.
    """,
    request={
        'application/json': MembreSerializer,
        'multipart/form-data': MembreSerializer,
    },
    responses={
        200: MembreSerializer,
        400: inline_serializer(
            name='ErrorResponse',
            fields={
                'error': OpenApiTypes.STR,
                'detail': OpenApiTypes.STR,
            }
        ),
        403: inline_serializer(
            name='ForbiddenResponse',
            fields={
                'error': OpenApiTypes.STR,
            }
        ),
    },
    examples=[
        OpenApiExample(
            'Consulter le profil',
            value={},
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Modifier le profil (PATCH)',
            value={
                'email': 'nouveau@example.com',
                'ville': 'Kinshasa',
                'telephone': '+243900000001',
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            'Modifier avec photo (multipart/form-data)',
            value={
                'nom': 'Doe',
                'prenom': 'John',
                'photo_profil': '<fichier image>',
            },
            request_only=True,
            response_only=False,
        ),
    ],
    tags=['Profil Membre']
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def membre_profile_view(request):
    """
    Endpoint pour qu'un membre consulte et modifie son propre profil
    GET /api/auth/membre/profile/ - Consulter son profil
    PUT /api/auth/membre/profile/ - Modifier son profil (tous les champs)
    PATCH /api/auth/membre/profile/ - Modifier son profil (champs partiels)
    
    Nécessite d'être connecté en tant que MEMBRE
    """
    user = request.user
    
    # Vérifier que l'utilisateur est un membre
    if user.user_type != 'MEMBRE' or not user.membre:
        return Response(
            {'error': 'Cet endpoint est réservé aux membres.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    membre = user.membre
    
    if request.method == 'GET':
        serializer = MembreSerializer(membre, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Ne pas permettre la modification de certains champs critiques
        data = request.data.copy()
        
        # Empêcher la modification de ces champs
        restricted_fields = ['numero_compte', 'date_adhesion', 'actif', 'type_membre']
        for field in restricted_fields:
            if field in data:
                del data[field]
        
        # Si le mot de passe est fourni, il doit être changé via l'endpoint dédié
        if 'password' in data:
            return Response(
                {'error': 'Pour changer votre mot de passe, utilisez l\'endpoint /api/auth/membre/change-password/'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        partial = request.method == 'PATCH'
        serializer = MembreSerializer(membre, data=data, partial=partial, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Consulter et modifier le profil du client connecté",
    description="""
    Endpoint pour qu'un client consulte et modifie son propre profil.
    
    **GET** : Consulter son profil complet
    **PUT** : Modifier tous les champs du profil
    **PATCH** : Modifier certains champs du profil
    
    **Champs modifiables** :
    - Informations personnelles : nom, prenom, postnom, sexe, date_naissance
    - Contact : email, telephone, adresse, ville
    - Profession : profession
    - Photo : photo_profil
    - Autres : annee_adhesion
    
    **Champs protégés (non modifiables)** :
    - numero_compte (généré automatiquement)
    - date_inscription (date de création)
    - actif (géré automatiquement)
    - password (utiliser l'endpoint dédié /api/auth/client/change-password/)
    
    **Sécurité** : Seul le client connecté peut accéder à son propre profil.
    """,
    request={
        'application/json': ClientSerializer,
        'multipart/form-data': ClientSerializer,
    },
    responses={
        200: ClientSerializer,
        400: inline_serializer(
            name='ErrorResponse',
            fields={
                'error': OpenApiTypes.STR,
                'detail': OpenApiTypes.STR,
            }
        ),
        403: inline_serializer(
            name='ForbiddenResponse',
            fields={
                'error': OpenApiTypes.STR,
            }
        ),
    },
    examples=[
        OpenApiExample(
            'Consulter le profil',
            value={},
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Modifier le profil (PATCH)',
            value={
                'email': 'nouveau@example.com',
                'ville': 'Kinshasa',
                'telephone': '+243900000001',
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            'Modifier avec photo (multipart/form-data)',
            value={
                'nom': 'Doe',
                'prenom': 'Jane',
                'photo_profil': '<fichier image>',
            },
            request_only=True,
            response_only=False,
        ),
    ],
    tags=['Profil Client']
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def client_profile_view(request):
    """
    Endpoint pour qu'un client consulte et modifie son propre profil
    GET /api/auth/client/profile/ - Consulter son profil
    PUT /api/auth/client/profile/ - Modifier son profil (tous les champs)
    PATCH /api/auth/client/profile/ - Modifier son profil (champs partiels)
    
    Nécessite d'être connecté en tant que CLIENT
    """
    user = request.user
    
    # Vérifier que l'utilisateur est un client
    if user.user_type != 'CLIENT' or not user.client:
        return Response(
            {'error': 'Cet endpoint est réservé aux clients.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    client = user.client
    
    if request.method == 'GET':
        serializer = ClientSerializer(client, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Ne pas permettre la modification de certains champs critiques
        data = request.data.copy()
        
        # Empêcher la modification de ces champs
        restricted_fields = ['numero_compte', 'date_inscription', 'actif']
        for field in restricted_fields:
            if field in data:
                del data[field]
        
        # Si le mot de passe est fourni, il doit être changé via l'endpoint dédié
        if 'password' in data:
            return Response(
                {'error': 'Pour changer votre mot de passe, utilisez l\'endpoint /api/auth/client/change-password/'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        partial = request.method == 'PATCH'
        serializer = ClientSerializer(client, data=data, partial=partial, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Changer le mot de passe du membre connecté",
    description="""
    Endpoint pour qu'un membre change son mot de passe.
    
    **Sécurité** :
    - Nécessite l'ancien mot de passe pour vérification
    - Le nouveau mot de passe doit respecter les règles de sécurité :
      * Minimum 6 caractères
      * Contient des lettres (majuscules et minuscules)
      * Contient des chiffres
      * Contient des caractères spéciaux
    
    **Exemple de mot de passe valide** : `Password123!@#`
    
    **Sécurité** : Seul le membre connecté peut changer son propre mot de passe.
    """,
    request=ChangeMembreClientPasswordSerializer,
    responses={
        200: inline_serializer(
            name='SuccessResponse',
            fields={
                'message': OpenApiTypes.STR,
            }
        ),
        400: inline_serializer(
            name='ValidationErrorResponse',
            fields={
                'old_password': OpenApiTypes.STR,
                'new_password': OpenApiTypes.STR,
            }
        ),
        403: inline_serializer(
            name='ForbiddenResponse',
            fields={
                'error': OpenApiTypes.STR,
            }
        ),
    },
    examples=[
        OpenApiExample(
            'Changer le mot de passe',
            value={
                'old_password': 'AncienMotDePasse123!@#',
                'new_password': 'NouveauMotDePasse456$%^',
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            'Réponse succès',
            value={
                'message': 'Mot de passe modifié avec succès.',
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Erreur - ancien mot de passe incorrect',
            value={
                'old_password': ['L\'ancien mot de passe est incorrect.'],
            },
            request_only=False,
            response_only=True,
        ),
    ],
    tags=['Profil Membre']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_membre_password_view(request):
    """
    Endpoint pour qu'un membre change son mot de passe
    POST /api/auth/membre/change-password/
    
    Body:
    {
        "old_password": "AncienMotDePasse123!@#",
        "new_password": "NouveauMotDePasse123!@#"
    }
    
    Nécessite d'être connecté en tant que MEMBRE
    """
    user = request.user
    
    # Vérifier que l'utilisateur est un membre
    if user.user_type != 'MEMBRE' or not user.membre:
        return Response(
            {'error': 'Cet endpoint est réservé aux membres.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ChangeMembreClientPasswordSerializer(data=request.data, context={'user': user})
    
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        
        # Changer le mot de passe dans le modèle Membre
        from django.contrib.auth.hashers import make_password
        user.membre.password = make_password(new_password)
        user.membre.save()
        
        return Response(
            {'message': 'Mot de passe modifié avec succès.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Changer le mot de passe du client connecté",
    description="""
    Endpoint pour qu'un client change son mot de passe.
    
    **Sécurité** :
    - Nécessite l'ancien mot de passe pour vérification
    - Le nouveau mot de passe doit respecter les règles de sécurité :
      * Minimum 6 caractères
      * Contient des lettres (majuscules et minuscules)
      * Contient des chiffres
      * Contient des caractères spéciaux
    
    **Exemple de mot de passe valide** : `Password123!@#`
    
    **Sécurité** : Seul le client connecté peut changer son propre mot de passe.
    """,
    request=ChangeMembreClientPasswordSerializer,
    responses={
        200: inline_serializer(
            name='SuccessResponse',
            fields={
                'message': OpenApiTypes.STR,
            }
        ),
        400: inline_serializer(
            name='ValidationErrorResponse',
            fields={
                'old_password': OpenApiTypes.STR,
                'new_password': OpenApiTypes.STR,
            }
        ),
        403: inline_serializer(
            name='ForbiddenResponse',
            fields={
                'error': OpenApiTypes.STR,
            }
        ),
    },
    examples=[
        OpenApiExample(
            'Changer le mot de passe',
            value={
                'old_password': 'AncienMotDePasse123!@#',
                'new_password': 'NouveauMotDePasse456$%^',
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            'Réponse succès',
            value={
                'message': 'Mot de passe modifié avec succès.',
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Erreur - ancien mot de passe incorrect',
            value={
                'old_password': ['L\'ancien mot de passe est incorrect.'],
            },
            request_only=False,
            response_only=True,
        ),
    ],
    tags=['Profil Client']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_client_password_view(request):
    """
    Endpoint pour qu'un client change son mot de passe
    POST /api/auth/client/change-password/
    
    Body:
    {
        "old_password": "AncienMotDePasse123!@#",
        "new_password": "NouveauMotDePasse123!@#"
    }
    
    Nécessite d'être connecté en tant que CLIENT
    """
    user = request.user
    
    # Vérifier que l'utilisateur est un client
    if user.user_type != 'CLIENT' or not user.client:
        return Response(
            {'error': 'Cet endpoint est réservé aux clients.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ChangeMembreClientPasswordSerializer(data=request.data, context={'user': user})
    
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        
        # Changer le mot de passe dans le modèle Client
        from django.contrib.auth.hashers import make_password
        user.client.password = make_password(new_password)
        user.client.save()
        
        return Response(
            {'message': 'Mot de passe modifié avec succès.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
