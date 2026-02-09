from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "change-me-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'users',
    'membres',
    'credits',
    'caisse',
    'rapports',
    'corsheaders',
]


REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',  # Nécessaire pour l'upload de fichiers
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Par défaut, authentification requise
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Coopec API',
    'DESCRIPTION': 'API de la COOPEC - Système de gestion de coopérative d\'épargne et de crédit',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentification', 'description': 'Endpoints pour l\'authentification et la gestion des utilisateurs'},
        {'name': 'Gestion des administrateurs', 'description': 'Gestion des administrateurs (ADMIN et SUPERADMIN) : liste et modification de mot de passe'},
        {'name': 'Profil Membre', 'description': 'Gestion du profil des membres connectés : consultation, modification et changement de mot de passe'},
        {'name': 'Profil Client', 'description': 'Gestion du profil des clients connectés : consultation, modification et changement de mot de passe'},
        {'name': 'Configuration SMTP', 'description': 'Configuration dynamique des paramètres SMTP pour l\'envoi d\'emails (stockage en mémoire, pas en BDD)'},
        {'name': 'Membres', 'description': 'Gestion des membres de la coopérative'},
        {'name': 'Clients', 'description': 'Gestion des clients de la coopérative'},
        {'name': 'Crédits', 'description': 'Gestion des crédits et remboursements'},
        {'name': 'Caisse', 'description': 'Gestion de la caisse et des transactions'},
        {'name': 'Types de Caisse', 'description': 'Gestion des types de caisse (Airtel Money, Orange Money, Banque, etc.)'},
        {'name': 'Mouvements de Type de Caisse', 'description': 'Gestion des mouvements de type de caisse (liaison type de caisse avec transactions/donations/remboursements)'},
        {'name': 'Rapports', 'description': 'Génération de rapports et reçus'},
    ],
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Token JWT obtenu via /api/auth/login/'
        }
    },
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # DOIT être en haut (avant CommonMiddleware)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]



ROOT_URLCONF = 'coopec.urls'
CORS_ALLOW_CREDENTIALS = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'coopec.wsgi.application'


# -------------------------------
# DATABASE — VERSION PAR DÉFAUT
# -------------------------------
# Mets tes vraies informations ici
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_coopec',      
        'USER': 'root',            
        'PASSWORD': '',          
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration Email
# Pour le développement : utiliser le backend console (affiche les emails dans la console)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Ou utiliser le backend fichier (sauvegarde les emails dans un fichier)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = BASE_DIR / 'emails'  # Dossier où sauvegarder les emails

# Pour envoyer de vrais emails, configurez avec un serveur SMTP :
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pima62016@gmail.com'  # Remplacez par l'email de la coopérative
EMAIL_HOST_PASSWORD = 'lhtgceewlrbfuwtw'  # Mettez le mot de passe d'application Gmail ici
DEFAULT_FROM_EMAIL = 'pima62016@gmail.com'  # Remplacez par l'email de la coopérative

# Note: Pour Gmail, vous devez utiliser un "Mot de passe d'application" et non votre mot de passe normal
# Pour créer un mot de passe d'application Gmail:
# 1. Allez sur https://myaccount.google.com/security
# 2. Activez la validation en 2 étapes si ce n'est pas déjà fait
# 3. Allez dans "Mots de passe des applications"
# 4. Créez un nouveau mot de passe d'application pour "Mail"
# 5. Utilisez ce mot de passe dans EMAIL_HOST_PASSWORD

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Note: 'corsheaders' is already included in INSTALLED_APPS above; removed duplicate block to avoid syntax errors.
# Pendant le développement, vous pouvez autoriser l'origine de votre front-end :
# Configuration CORS
CORS_ALLOW_ALL_ORIGINS = True
  


# Autoriser les méthodes HTTP pour CORS
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Autoriser les headers pour CORS
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# OU pour le développement uniquement (moins sécurisé)
# CORS_ALLOW_ALL_ORIGINS = True  # Utiliser uniquement en développement !

# **Alternative temporaire :**
# Si vous voulez juste que ça fonctionne en développement SANS RESTRICTION,
# vous pouvez temporairement faire ceci (DANGEREUX EN PRODUCTION) :
# CORS_ALLOW_ALL_ORIGINS = True
# Note: MIDDLEWARE is already defined above; ensure 'corsheaders.middleware.CorsMiddleware' is placed before other middleware in that definition.

# Configuration du modèle User personnalisé
AUTH_USER_MODEL = 'users.User'

# Configuration JWT (Simple JWT)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=48),  # Token valide 48h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Refresh token valide 7 jours
    'ROTATE_REFRESH_TOKENS': True,  # Générer un nouveau refresh token à chaque refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklister l'ancien refresh token
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}

# Configuration JWT (Simple JWT)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=48),  # Token valide 48h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Refresh token valide 7 jours
    'ROTATE_REFRESH_TOKENS': True,  # Générer un nouveau refresh token à chaque refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklister l'ancien refresh token
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}

