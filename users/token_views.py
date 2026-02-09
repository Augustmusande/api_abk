"""
Vues personnalisées pour les tokens JWT avec documentation
"""
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    summary="Rafraîchir le token d'accès",
    description="Endpoint pour rafraîchir le token d'accès en utilisant le refresh token. Génère un nouveau access token et refresh token.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh token à utiliser pour obtenir un nouveau access token'
                }
            },
            'required': ['refresh']
        }
    },
    responses={
        200: {
            'description': 'Nouveau token généré avec succès',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                }
            }
        },
        401: {'description': 'Refresh token invalide ou expiré'}
    },
    tags=['Authentification']
)
class CustomTokenRefreshView(TokenRefreshView):
    """Vue personnalisée pour le refresh token avec documentation"""
    pass


