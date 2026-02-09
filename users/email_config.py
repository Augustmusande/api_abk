"""
Gestion dynamique de la configuration SMTP
Les paramètres sont stockés en mémoire (pas en base de données)
"""
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
import threading

# Stockage thread-safe des paramètres SMTP dynamiques
_smtp_config = {}
_config_lock = threading.Lock()


def set_smtp_config(host=None, port=None, use_tls=None, use_ssl=None, 
                    host_user=None, host_password=None, default_from_email=None):
    """
    Configure les paramètres SMTP dynamiquement
    
    Args:
        host (str): Serveur SMTP (ex: 'smtp.gmail.com')
        port (int): Port SMTP (ex: 587 pour TLS, 465 pour SSL)
        use_tls (bool): Utiliser TLS
        use_ssl (bool): Utiliser SSL
        host_user (str): Email d'envoi
        host_password (str): Mot de passe d'application
        default_from_email (str): Email par défaut pour l'expéditeur
    """
    global _smtp_config
    
    with _config_lock:
        if host is not None:
            _smtp_config['host'] = host
        if port is not None:
            _smtp_config['port'] = port
        if use_tls is not None:
            _smtp_config['use_tls'] = use_tls
        if use_ssl is not None:
            _smtp_config['use_ssl'] = use_ssl
        if host_user is not None:
            _smtp_config['host_user'] = host_user
        if host_password is not None:
            _smtp_config['host_password'] = host_password
        if default_from_email is not None:
            _smtp_config['default_from_email'] = default_from_email


def get_smtp_config():
    """
    Récupère la configuration SMTP actuelle (sans le mot de passe)
    
    Returns:
        dict: Configuration SMTP (sans le mot de passe pour la sécurité)
    """
    global _smtp_config
    
    with _config_lock:
        config = _smtp_config.copy()
        # Ne pas retourner le mot de passe pour la sécurité
        if 'host_password' in config:
            config['host_password'] = '***' if config['host_password'] else None
        return config


def get_smtp_backend():
    """
    Retourne une instance de EmailBackend configurée avec les paramètres dynamiques
    ou les paramètres par défaut du settings.py
    
    Returns:
        EmailBackend: Backend SMTP configuré
    """
    global _smtp_config
    
    with _config_lock:
        # Utiliser la configuration dynamique si elle existe, sinon utiliser settings.py
        host = _smtp_config.get('host', getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'))
        port = _smtp_config.get('port', getattr(settings, 'EMAIL_PORT', 587))
        use_tls = _smtp_config.get('use_tls', getattr(settings, 'EMAIL_USE_TLS', True))
        use_ssl = _smtp_config.get('use_ssl', getattr(settings, 'EMAIL_USE_SSL', False))
        host_user = _smtp_config.get('host_user', getattr(settings, 'EMAIL_HOST_USER', ''))
        host_password = _smtp_config.get('host_password', getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
    
    return EmailBackend(
        host=host,
        port=port,
        username=host_user,
        password=host_password,
        use_tls=use_tls,
        use_ssl=use_ssl,
        fail_silently=False
    )


def get_default_from_email():
    """
    Retourne l'email expéditeur par défaut (configuration dynamique ou settings.py)
    
    Returns:
        str: Email expéditeur
    """
    global _smtp_config
    
    with _config_lock:
        return _smtp_config.get('default_from_email', getattr(settings, 'DEFAULT_FROM_EMAIL', ''))


def clear_smtp_config():
    """
    Réinitialise la configuration SMTP (retour aux paramètres par défaut du settings.py)
    """
    global _smtp_config
    
    with _config_lock:
        _smtp_config.clear()









