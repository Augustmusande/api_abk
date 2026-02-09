"""
Validateurs personnalisés pour les modèles User
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_password_strength(password):
    """
    Valide que le mot de passe respecte les critères :
    - Minimum 6 caractères
    - Contient au moins une lettre
    - Contient au moins un chiffre
    - Contient au moins un caractère spécial
    """
    if len(password) < 6:
        raise ValidationError(
            _("Le mot de passe doit contenir au minimum 6 caractères."),
            code='password_too_short',
        )
    
    # Vérifier qu'il y a au moins une lettre
    if not re.search(r'[a-zA-Z]', password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins une lettre."),
            code='password_no_letter',
        )
    
    # Vérifier qu'il y a au moins un chiffre
    if not re.search(r'\d', password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins un chiffre."),
            code='password_no_digit',
        )
    
    # Vérifier qu'il y a au moins un caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*(),.?\":{}|<>)."),
            code='password_no_special',
        )
    
    return password


def validate_email_exists(email):
    """
    Valide que l'email existe vraiment en vérifiant :
    1. Le format de l'email
    2. L'existence du domaine (vérification DNS)
    3. L'existence des enregistrements MX pour le domaine
    4. Vérification que le domaine peut recevoir des emails
    
    Note: Cette fonction vérifie que le domaine existe et peut recevoir des emails,
    mais ne peut pas vérifier si l'adresse email spécifique existe sans envoyer un email de test.
    """
    if not email:
        raise ValidationError(
            _("L'adresse email est obligatoire."),
            code='email_required',
        )
    
    try:
        from email_validator import validate_email as validate_email_format, EmailNotValidError
    except ImportError:
        # Si email-validator n'est pas installé, on fait juste une validation basique
        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            django_validate_email(email)
            # Avertir que la vérification complète n'est pas disponible
            import warnings
            warnings.warn("email-validator n'est pas installé. Installation recommandée: pip install email-validator")
            return email
        except DjangoValidationError as e:
            raise ValidationError(
                _("L'adresse email n'est pas valide. Veuillez entrer une adresse email valide."),
                code='email_invalid',
            ) from e
    
    # Vérifier le format et l'existence du domaine avec email-validator
    # check_deliverability=True vérifie que le domaine existe et a des enregistrements MX
    try:
        validated = validate_email_format(
            email, 
            check_deliverability=True,  # Vérifie que le domaine peut recevoir des emails
            allow_smtputf8=False,  # Désactiver SMTPUTF8 pour simplifier
        )
        email = validated.email
    except EmailNotValidError as e:
        # Message d'erreur plus détaillé
        error_msg = str(e)
        if "domain" in error_msg.lower() or "mx" in error_msg.lower():
            raise ValidationError(
                _("Le domaine de cette adresse email n'existe pas ou ne peut pas recevoir d'emails. Veuillez entrer une adresse email réelle qui existe."),
                code='email_domain_invalid',
            ) from e
        else:
            raise ValidationError(
                _("L'adresse email n'est pas valide ou n'existe pas. Veuillez entrer une adresse email réelle qui existe (exemple: nom@domaine.com)."),
                code='email_invalid',
            ) from e
    
    # La bibliothèque email-validator avec check_deliverability=True
    # vérifie déjà l'existence du domaine et des enregistrements MX
    # Cela empêche les emails comme "test@nonexistentdomain12345.com"
    # Note: On ne peut pas vérifier si l'adresse spécifique existe sans envoyer un email de test
    
    return email

