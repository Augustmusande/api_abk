from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import Membre, Client, Cooperative
from .validators import validate_password_strength, validate_email_exists
import os

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class CooperativeSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Cooperative
        fields = '__all__'
        extra_kwargs = {
            'logo': {'write_only': False}
        }
    
    def get_logo_url(self, obj):
        """Retourne l'URL complète du logo"""
        if obj.logo and hasattr(obj.logo, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def validate_logo(self, value):
        """Validation professionnelle du logo"""
        # Si value est None ou vide, c'est une mise à jour partielle sans changement de logo
        if value is None:
            return value
        
        # Si c'est une mise à jour et qu'on reçoit une chaîne vide, on garde l'ancien logo
        if hasattr(value, 'name') and not value.name:
            return value
            
        if value:
            # Vérifier l'extension du fichier
            valid_extensions = ['.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Format de fichier non supporté. Formats acceptés: {', '.join(valid_extensions)}"
                )
            
            # Vérifier la taille du fichier (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"Le fichier est trop volumineux. Taille maximale: 5MB"
                )
            
            # Vérifier les dimensions pour les images (sauf SVG)
            if ext != '.svg' and PIL_AVAILABLE:
                try:
                    # Réinitialiser le pointeur du fichier
                    value.seek(0)
                    img = Image.open(value)
                    width, height = img.size
                    
                    # Vérifier les dimensions minimales
                    if width < 100 or height < 100:
                        raise serializers.ValidationError(
                            "Les dimensions minimales du logo sont 100x100 pixels"
                        )
                    
                    # Vérifier les dimensions maximales (3048x1420)
                    if width > 3048 or height > 1420:
                        raise serializers.ValidationError(
                            "Les dimensions maximales du logo sont 3048x1420 pixels (largeur x hauteur)"
                        )
                    
                    # Vérifier le ratio (adapté pour le format 3048x1420, ratio ≈ 2.15)
                    ratio = width / height
                    if ratio < 0.5 or ratio > 2.5:
                        raise serializers.ValidationError(
                            "Le ratio largeur/hauteur doit être entre 0.5 et 2.5"
                        )
                    
                    # Réinitialiser le pointeur pour que Django puisse sauvegarder le fichier
                    value.seek(0)
                except Exception as e:
                    if isinstance(e, serializers.ValidationError):
                        raise
                    raise serializers.ValidationError(
                        "Le fichier n'est pas une image valide"
                    )
            elif ext != '.svg' and not PIL_AVAILABLE:
                # Si PIL n'est pas disponible, on accepte le fichier mais on ne peut pas valider les dimensions
                pass
        
        return value

class MembreSerializer(serializers.ModelSerializer):
    photo_profil_url = serializers.SerializerMethodField()
    score_moyen = serializers.SerializerMethodField(help_text="Score moyen basé sur tous les crédits (sur 10)")
    pourcentage_score = serializers.SerializerMethodField(help_text="Pourcentage du score (sur 100)")
    mention_score = serializers.SerializerMethodField(help_text="Mention du score (A+, A, B, C, D)")
    nombre_credits = serializers.SerializerMethodField(help_text="Nombre total de crédits du membre")
    
    class Meta:
        model = Membre
        fields = '__all__'
        extra_kwargs = {
            'numero_compte': {'read_only': True},
            'date_adhesion': {'read_only': True},
            'actif': {'read_only': True},
            'password': {'write_only': True},
        }
    
    def get_photo_profil_url(self, obj):
        """Retourne l'URL complète de la photo de profil"""
        if obj.photo_profil and hasattr(obj.photo_profil, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo_profil.url)
            return obj.photo_profil.url
        return None
    
    def get_score_moyen(self, obj):
        """Retourne le score moyen du membre"""
        score_data = obj.calculer_score_moyen()
        return score_data['score_moyen']
    
    def get_pourcentage_score(self, obj):
        """Retourne le pourcentage du score"""
        score_data = obj.calculer_score_moyen()
        return score_data['pourcentage']
    
    def get_mention_score(self, obj):
        """Retourne la mention du score"""
        score_data = obj.calculer_score_moyen()
        return score_data['mention']
    
    def get_nombre_credits(self, obj):
        """Retourne le nombre de crédits du membre"""
        score_data = obj.calculer_score_moyen()
        return score_data['nombre_credits']
    
    def validate_photo_profil(self, value):
        """Validation de la photo de profil"""
        if value is None:
            return value
        
        # Si c'est une mise à jour et qu'on reçoit une chaîne vide, on garde l'ancienne photo
        if hasattr(value, 'name') and not value.name:
            return value
        
        if value:
            # Vérifier l'extension du fichier
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Format de fichier non supporté. Formats acceptés: {', '.join(valid_extensions)}"
                )
            
            # Vérifier la taille du fichier (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"Le fichier est trop volumineux. Taille maximale: 5MB"
                )
        
        return value
    
    def validate_annee_adhesion(self, value):
        """Validation de l'année d'adhésion"""
        if value is not None:
            if value < 1900 or value > 2100:
                raise serializers.ValidationError(
                    "L'année d'adhésion doit être entre 1900 et 2100."
                )
        return value
    
    def validate_email(self, value):
        """
        Valide que l'email est valide, existe vraiment et est unique
        """
        # L'email est obligatoire
        if not value:
            raise serializers.ValidationError(
                "L'adresse email est obligatoire."
            )
        
        # Vérifier que l'email existe vraiment (vérification DNS/MX)
        try:
            value = validate_email_exists(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Vérifier l'unicité de l'email dans Membre
        queryset = Membre.objects.filter(email=value)
        # Si c'est une mise à jour, exclure l'instance actuelle
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée par un autre membre. Veuillez utiliser une autre adresse email."
            )
        
        # Vérifier l'unicité de l'email dans Client
        from .models import Client
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée par un client. Veuillez utiliser une autre adresse email."
            )
        
        return value
    
    def validate_password(self, value):
        """
        Valide la force du mot de passe
        """
        if not value:
            raise serializers.ValidationError(
                "Le mot de passe est obligatoire."
            )
        
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def create(self, validated_data):
        """
        Hash le mot de passe avant de créer l'instance
        Crée automatiquement un compte User pour le membre
        """
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        
        membre = super().create(validated_data)
        
        # Créer automatiquement un compte User pour le membre
        from .models import User
        email = membre.email
        
        # Générer un username unique
        username = f"membre_{membre.numero_compte}"
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"membre_{membre.numero_compte}_{counter}"
            counter += 1
        
        # Créer l'utilisateur (sans password dans User, on utilise celui du Membre)
        User.objects.create(
            username=username,
            email=email,
            password='',  # Pas de password dans User pour membres/clients
            user_type='MEMBRE',
            membre=membre,
            is_active=True
        )
        
        return membre
    
    def update(self, instance, validated_data):
        """
        Hash le mot de passe avant de mettre à jour l'instance
        """
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        return super().update(instance, validated_data)
    
    def validate(self, attrs):
        """
        Valide que les champs sont cohérents selon le type de membre.
        - Si personne physique : champs physique requis, champs morale null
        - Si personne morale : champs morale requis, champs physique null
        """
        type_membre = attrs.get('type_membre', self.instance.type_membre if self.instance else 'PHYSIQUE')
        
        if type_membre == 'PHYSIQUE':
            # Personne physique : valider les champs requis
            if not attrs.get('nom'):
                raise serializers.ValidationError({
                    'nom': 'Le nom est requis pour une personne physique.'
                })
            if not attrs.get('prenom'):
                raise serializers.ValidationError({
                    'prenom': 'Le prénom est requis pour une personne physique.'
                })
            if not attrs.get('sexe'):
                raise serializers.ValidationError({
                    'sexe': 'Le sexe est requis pour une personne physique.'
                })
            
            # S'assurer que les champs de personne morale sont null
            attrs['raison_sociale'] = None
            attrs['sigle'] = None
            attrs['numero_immatriculation'] = None
            attrs['forme_juridique'] = None
            attrs['representant_legal'] = None
            attrs['secteur_activite'] = None
            
        elif type_membre == 'MORALE':
            # Personne morale : valider les champs requis
            if not attrs.get('raison_sociale') and not attrs.get('sigle'):
                raise serializers.ValidationError({
                    'raison_sociale': 'La raison sociale ou le sigle est requis pour une personne morale.',
                    'sigle': 'La raison sociale ou le sigle est requis pour une personne morale.'
                })
            
            # S'assurer que les champs de personne physique sont null
            attrs['nom'] = None
            attrs['postnom'] = None
            attrs['prenom'] = None
            attrs['sexe'] = None
            attrs['date_naissance'] = None
        
        return attrs

class ClientSerializer(serializers.ModelSerializer):
    photo_profil_url = serializers.SerializerMethodField()
    score_moyen = serializers.SerializerMethodField(help_text="Score moyen basé sur tous les crédits (sur 10)")
    pourcentage_score = serializers.SerializerMethodField(help_text="Pourcentage du score (sur 100)")
    mention_score = serializers.SerializerMethodField(help_text="Mention du score (A+, A, B, C, D)")
    nombre_credits = serializers.SerializerMethodField(help_text="Nombre total de crédits du client")
    
    class Meta:
        model = Client
        fields = '__all__'
        extra_kwargs = {
            'numero_compte': {'read_only': True},
            'date_inscription': {'read_only': True},
            'actif': {'read_only': True},
            'password': {'write_only': True},
        }
    
    def get_photo_profil_url(self, obj):
        """Retourne l'URL complète de la photo de profil"""
        if obj.photo_profil and hasattr(obj.photo_profil, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo_profil.url)
            return obj.photo_profil.url
        return None
    
    def get_score_moyen(self, obj):
        """Retourne le score moyen du client"""
        score_data = obj.calculer_score_moyen()
        return score_data['score_moyen']
    
    def get_pourcentage_score(self, obj):
        """Retourne le pourcentage du score"""
        score_data = obj.calculer_score_moyen()
        return score_data['pourcentage']
    
    def get_mention_score(self, obj):
        """Retourne la mention du score"""
        score_data = obj.calculer_score_moyen()
        return score_data['mention']
    
    def get_nombre_credits(self, obj):
        """Retourne le nombre de crédits du client"""
        score_data = obj.calculer_score_moyen()
        return score_data['nombre_credits']
    
    def validate_photo_profil(self, value):
        """Validation de la photo de profil"""
        if value is None:
            return value
        
        # Si c'est une mise à jour et qu'on reçoit une chaîne vide, on garde l'ancienne photo
        if hasattr(value, 'name') and not value.name:
            return value
        
        if value:
            # Vérifier l'extension du fichier
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Format de fichier non supporté. Formats acceptés: {', '.join(valid_extensions)}"
                )
            
            # Vérifier la taille du fichier (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"Le fichier est trop volumineux. Taille maximale: 5MB"
                )
        
        return value
    
    def validate_annee_adhesion(self, value):
        """Validation de l'année d'adhésion"""
        if value is not None:
            if value < 1900 or value > 2100:
                raise serializers.ValidationError(
                    "L'année d'adhésion doit être entre 1900 et 2100."
                )
        return value
    
    def validate_email(self, value):
        """
        Valide que l'email est valide, existe vraiment et est unique
        """
        # L'email est obligatoire
        if not value:
            raise serializers.ValidationError(
                "L'adresse email est obligatoire."
            )
        
        # Vérifier que l'email existe vraiment (vérification DNS/MX)
        try:
            value = validate_email_exists(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Vérifier l'unicité de l'email dans Client
        queryset = Client.objects.filter(email=value)
        # Si c'est une mise à jour, exclure l'instance actuelle
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée par un autre client. Veuillez utiliser une autre adresse email."
            )
        
        # Vérifier l'unicité de l'email dans Membre
        from .models import Membre
        if Membre.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée par un membre. Veuillez utiliser une autre adresse email."
            )
        
        return value
    
    def validate_password(self, value):
        """
        Valide la force du mot de passe
        """
        if not value:
            raise serializers.ValidationError(
                "Le mot de passe est obligatoire."
            )
        
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def create(self, validated_data):
        """
        Hash le mot de passe avant de créer l'instance
        Crée automatiquement un compte User pour le client
        """
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        
        client = super().create(validated_data)
        
        # Créer automatiquement un compte User pour le client
        from .models import User
        email = client.email
        
        # Générer un username unique
        username = f"client_{client.numero_compte}"
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"client_{client.numero_compte}_{counter}"
            counter += 1
        
        # Créer l'utilisateur (sans password dans User, on utilise celui du Client)
        User.objects.create(
            username=username,
            email=email,
            password='',  # Pas de password dans User pour membres/clients
            user_type='CLIENT',
            client=client,
            is_active=True
        )
        
        return client
    
    def update(self, instance, validated_data):
        """
        Hash le mot de passe avant de mettre à jour l'instance
        """
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        return super().update(instance, validated_data)
