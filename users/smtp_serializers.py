"""
Serializers pour la configuration SMTP
"""
from rest_framework import serializers


class SMTPConfigSerializer(serializers.Serializer):
    """
    Serializer pour configurer les paramètres SMTP
    """
    host = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Serveur SMTP (ex: 'smtp.gmail.com', 'smtp-mail.outlook.com')"
    )
    port = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=65535,
        help_text="Port SMTP (ex: 587 pour TLS, 465 pour SSL)"
    )
    use_tls = serializers.BooleanField(
        required=False,
        help_text="Utiliser TLS (True pour le port 587)"
    )
    use_ssl = serializers.BooleanField(
        required=False,
        help_text="Utiliser SSL (True pour le port 465)"
    )
    host_user = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email d'envoi (ex: 'votre_email@gmail.com')"
    )
    host_password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Mot de passe d'application (ne sera jamais retourné pour la sécurité)"
    )
    default_from_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email expéditeur par défaut (ex: 'votre_email@gmail.com')"
    )
    
    def validate(self, attrs):
        """Valide que TLS ou SSL est spécifié si un port est fourni"""
        use_tls = attrs.get('use_tls')
        use_ssl = attrs.get('use_ssl')
        port = attrs.get('port')
        
        if port:
            if port == 587 and not use_tls:
                raise serializers.ValidationError(
                    "Le port 587 nécessite use_tls=True"
                )
            if port == 465 and not use_ssl:
                raise serializers.ValidationError(
                    "Le port 465 nécessite use_ssl=True"
                )
        
        if use_tls and use_ssl:
            raise serializers.ValidationError(
                "use_tls et use_ssl ne peuvent pas être tous les deux True"
            )
        
        return attrs


class SMTPConfigReadSerializer(serializers.Serializer):
    """
    Serializer pour lire la configuration SMTP (sans le mot de passe)
    """
    host = serializers.CharField(required=False, allow_null=True)
    port = serializers.IntegerField(required=False, allow_null=True)
    use_tls = serializers.BooleanField(required=False, allow_null=True)
    use_ssl = serializers.BooleanField(required=False, allow_null=True)
    host_user = serializers.EmailField(required=False, allow_null=True)
    host_password = serializers.CharField(required=False, allow_null=True, help_text="Toujours '***' pour la sécurité")
    default_from_email = serializers.EmailField(required=False, allow_null=True)
    using_default = serializers.BooleanField(help_text="True si la configuration par défaut du settings.py est utilisée")









