"""
Vues pour la configuration SMTP dynamique
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.conf import settings
from .permissions import IsAdminOrSuperAdmin
from .email_config import set_smtp_config, get_smtp_config, clear_smtp_config, get_smtp_backend, get_default_from_email
from .smtp_serializers import SMTPConfigSerializer, SMTPConfigReadSerializer


@extend_schema(
    summary="Configurer ou récupérer les paramètres SMTP",
    description="""
    - GET : Récupère la configuration SMTP actuelle
    - POST/PUT/PATCH : Configure les paramètres SMTP dynamiquement via le frontend.
    
    Les paramètres sont stockés en mémoire (pas en base de données) et sont utilisés
    pour tous les envois d'email jusqu'à ce qu'ils soient modifiés ou que le serveur redémarre.
    
    **Important** :
    - Les paramètres sont stockés en mémoire uniquement (perdus au redémarrage du serveur)
    - Si un paramètre n'est pas fourni, il conserve sa valeur actuelle ou utilise celle du settings.py
    - Pour réinitialiser, utilisez l'endpoint DELETE /api/smtp/config/reset/
    """,
    request=SMTPConfigSerializer,
    responses={
        200: {
            'description': 'Configuration SMTP mise à jour ou récupérée avec succès',
            'examples': {
                'application/json': {
                    'message': 'Configuration SMTP mise à jour avec succès',
                    'config': {
                        'host': 'smtp.gmail.com',
                        'port': 587,
                        'use_tls': True,
                        'use_ssl': False,
                        'host_user': 'pima62016@gmail.com',
                        'host_password': '***',
                        'default_from_email': 'pima62016@gmail.com',
                        'using_default': False
                    }
                }
            }
        },
        400: {'description': 'Erreur de validation des paramètres'}
    },
    tags=['Configuration SMTP']
)
@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsAdminOrSuperAdmin])
def smtp_config_view(request):
    """
    Gère la configuration SMTP
    - GET /api/smtp/config/ : Récupère la configuration actuelle
    - POST/PUT/PATCH /api/smtp/config/ : Configure les paramètres SMTP
    
    Body pour POST/PUT/PATCH (tous les champs sont optionnels) :
    {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": true,
        "use_ssl": false,
        "host_user": "votre_email@gmail.com",
        "host_password": "votre_mot_de_passe_application",
        "default_from_email": "votre_email@gmail.com"
    }
    """
    # Si GET, retourner la configuration actuelle
    if request.method == 'GET':
        current_config = get_smtp_config()
        is_using_default = len(current_config) == 0
        
        if not is_using_default:
            response_config = {
                'host': current_config.get('host', getattr(settings, 'EMAIL_HOST', None)),
                'port': current_config.get('port', getattr(settings, 'EMAIL_PORT', None)),
                'use_tls': current_config.get('use_tls', getattr(settings, 'EMAIL_USE_TLS', None)),
                'use_ssl': current_config.get('use_ssl', getattr(settings, 'EMAIL_USE_SSL', None)),
                'host_user': current_config.get('host_user', getattr(settings, 'EMAIL_HOST_USER', None)),
                'host_password': '***',
                'default_from_email': current_config.get('default_from_email', getattr(settings, 'DEFAULT_FROM_EMAIL', None)),
                'using_default': False
            }
        else:
            response_config = {
                'host': getattr(settings, 'EMAIL_HOST', None),
                'port': getattr(settings, 'EMAIL_PORT', None),
                'use_tls': getattr(settings, 'EMAIL_USE_TLS', None),
                'use_ssl': getattr(settings, 'EMAIL_USE_SSL', None),
                'host_user': getattr(settings, 'EMAIL_HOST_USER', None),
                'host_password': '***',
                'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                'using_default': True
            }
        
        serializer = SMTPConfigReadSerializer(response_config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Si POST/PUT/PATCH, configurer les paramètres
    serializer = SMTPConfigSerializer(data=request.data)
    
    if serializer.is_valid():
        # Appliquer la configuration
        set_smtp_config(**serializer.validated_data)
        
        # Retourner la configuration actuelle (sans le mot de passe)
        current_config = get_smtp_config()
        is_using_default = len(current_config) == 0
        
        # Ajouter les valeurs par défaut si nécessaire
        if not is_using_default:
            response_config = {
                'host': current_config.get('host', getattr(settings, 'EMAIL_HOST', None)),
                'port': current_config.get('port', getattr(settings, 'EMAIL_PORT', None)),
                'use_tls': current_config.get('use_tls', getattr(settings, 'EMAIL_USE_TLS', None)),
                'use_ssl': current_config.get('use_ssl', getattr(settings, 'EMAIL_USE_SSL', None)),
                'host_user': current_config.get('host_user', getattr(settings, 'EMAIL_HOST_USER', None)),
                'host_password': '***',
                'default_from_email': current_config.get('default_from_email', getattr(settings, 'DEFAULT_FROM_EMAIL', None)),
                'using_default': False
            }
        else:
            response_config = {
                'host': getattr(settings, 'EMAIL_HOST', None),
                'port': getattr(settings, 'EMAIL_PORT', None),
                'use_tls': getattr(settings, 'EMAIL_USE_TLS', None),
                'use_ssl': getattr(settings, 'EMAIL_USE_SSL', None),
                'host_user': getattr(settings, 'EMAIL_HOST_USER', None),
                'host_password': '***',
                'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                'using_default': True
            }
        
        return Response({
            'message': 'Configuration SMTP mise à jour avec succès',
            'config': response_config
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@extend_schema(
    summary="Réinitialiser la configuration SMTP",
    description="""
    Réinitialise la configuration SMTP dynamique.
    Après cette opération, le système utilisera les paramètres par défaut du settings.py.
    """,
    responses={
        200: {
            'description': 'Configuration SMTP réinitialisée',
            'examples': {
                'application/json': {
                    'message': 'Configuration SMTP réinitialisée. Utilisation des paramètres par défaut du settings.py.'
                }
            }
        }
    },
    tags=['Configuration SMTP']
)
@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def reset_smtp_config_view(request):
    """
    Réinitialise la configuration SMTP (retour aux paramètres par défaut)
    DELETE /api/smtp/config/reset/
    """
    clear_smtp_config()
    
    return Response({
        'message': 'Configuration SMTP réinitialisée. Utilisation des paramètres par défaut du settings.py.'
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Tester la configuration SMTP",
    description="""
    Teste la configuration SMTP en envoyant un email de test.
    L'email sera envoyé à l'adresse spécifiée dans le paramètre 'test_email'.
    """,
    parameters=[
        OpenApiParameter(
            name='test_email',
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Email de destination pour le test'
        )
    ],
    responses={
        200: {
            'description': 'Email de test envoyé avec succès',
            'examples': {
                'application/json': {
                    'message': 'Email de test envoyé avec succès à test@example.com'
                }
            }
        },
        400: {'description': 'Email de test non fourni'},
        500: {'description': 'Erreur lors de l\'envoi de l\'email'}
    },
    tags=['Configuration SMTP']
)
@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def test_smtp_config_view(request):
    """
    Teste la configuration SMTP en envoyant un email de test
    POST /api/smtp/test/?test_email=votre_email@example.com
    """
    test_email = request.query_params.get('test_email') or request.data.get('test_email')
    
    if not test_email:
        return Response(
            {'error': 'Le paramètre test_email est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Utiliser le backend SMTP configuré dynamiquement
        backend = get_smtp_backend()
        from_email = get_default_from_email()
        
        # Créer et envoyer l'email de test
        from django.core.mail.message import EmailMessage
        
        email = EmailMessage(
            subject='Test de configuration SMTP - COOPEC',
            body=f"""
Bonjour,

Ceci est un email de test pour vérifier la configuration SMTP de votre système COOPEC.

Si vous recevez cet email, cela signifie que la configuration SMTP fonctionne correctement.

Configuration utilisée :
- Serveur SMTP : {backend.host}
- Port : {backend.port}
- TLS : {backend.use_tls}
- SSL : {backend.use_ssl}
- Email expéditeur : {from_email}

Cordialement,
Système COOPEC
            """,
            from_email=from_email,
            to=[test_email],
            connection=backend
        )
        
        email.send()
        
        return Response({
            'message': f'Email de test envoyé avec succès à {test_email}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': f'Erreur lors de l\'envoi de l\'email de test: {str(e)}',
                'details': 'Vérifiez que les paramètres SMTP sont corrects et que le serveur est accessible.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

