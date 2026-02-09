from rest_framework.routers import DefaultRouter
from django.urls import path
from drf_spectacular.utils import extend_schema
from .views import MembreViewSet, ClientViewSet, CooperativeViewSet
from .token_views import CustomTokenRefreshView
from .auth_views import (
    login_view,
    register_membre_view,
    register_client_view,
    register_admin_view,
    logout_view,
    me_view,
    list_admins_view,
    change_admin_password_view
)
from .profile_views import (
    membre_profile_view,
    client_profile_view,
    change_membre_password_view,
    change_client_password_view
)
from .smtp_views import (
    smtp_config_view,
    reset_smtp_config_view,
    test_smtp_config_view
)

router = DefaultRouter()
router.register(r'cooperatives', CooperativeViewSet, basename='cooperative')
router.register(r'membres', MembreViewSet)
router.register(r'clients', ClientViewSet)

urlpatterns = [
    # Authentification
    path('auth/login/', login_view, name='login'),
    path('auth/register/membre/', register_membre_view, name='register_membre'),
    path('auth/register/client/', register_client_view, name='register_client'),
    path('auth/register/admin/', register_admin_view, name='register_admin'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/me/', me_view, name='me'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Gestion des administrateurs
    path('auth/admins/', list_admins_view, name='list_admins'),
    path('auth/admins/<int:user_id>/change-password/', change_admin_password_view, name='change_admin_password'),
    
    # Gestion du profil membre/client
    path('auth/membre/profile/', membre_profile_view, name='membre_profile'),
    path('auth/membre/change-password/', change_membre_password_view, name='change_membre_password'),
    path('auth/client/profile/', client_profile_view, name='client_profile'),
    path('auth/client/change-password/', change_client_password_view, name='change_client_password'),
    
    # Configuration SMTP dynamique
    path('smtp/config/', smtp_config_view, name='smtp_config'),  # GET, POST, PUT, PATCH
    path('smtp/config/reset/', reset_smtp_config_view, name='reset_smtp_config'),  # DELETE
    path('smtp/test/', test_smtp_config_view, name='test_smtp_config'),
] + router.urls
