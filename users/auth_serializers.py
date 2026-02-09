"""
Serializers pour l'authentification
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password, make_password
from .models import User, Membre, Client
from .validators import validate_password_strength, validate_email_exists
from django.core.exceptions import ValidationError


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion
    Accepte username ou email + password
    """
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not password:
            raise serializers.ValidationError('Le mot de passe est requis.')
        
        # Vérifier qu'au moins username ou email est fourni
        if not username and not email:
            raise serializers.ValidationError('Username ou email est requis.')
        
        user = None
        
        # Pour MEMBRE et CLIENT : connexion avec email uniquement
        # Pour ADMIN et SUPERADMIN : connexion avec username ou email
        if email:
            try:
                user = User.objects.get(email=email)
                # Si c'est un membre ou client, utiliser l'email pour l'authentification
                if user.user_type in ['MEMBRE', 'CLIENT']:
                    # Vérifier le mot de passe directement depuis le modèle Membre/Client
                    if user.user_type == 'MEMBRE' and user.membre:
                        if not check_password(password, user.membre.password):
                            raise serializers.ValidationError('Identifiants invalides.')
                    elif user.user_type == 'CLIENT' and user.client:
                        if not check_password(password, user.client.password):
                            raise serializers.ValidationError('Identifiants invalides.')
                    else:
                        raise serializers.ValidationError('Compte membre/client non lié correctement.')
                else:
                    # Pour ADMIN et SUPERADMIN, utiliser l'authentification Django standard
                    username = user.username
                    user = authenticate(username=username, password=password)
                    if not user:
                        raise serializers.ValidationError('Identifiants invalides.')
            except User.DoesNotExist:
                # Si pas de compte User, chercher dans Membre ou Client
                # et créer le compte User automatiquement
                try:
                    membre = Membre.objects.get(email=email)
                    if check_password(password, membre.password):
                        # Créer le compte User automatiquement
                        username = f"membre_{membre.numero_compte}"
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"membre_{membre.numero_compte}_{counter}"
                            counter += 1
                        
                        user = User.objects.create(
                            username=username,
                            email=email,
                            password='',  # Pas de password dans User
                            user_type='MEMBRE',
                            membre=membre,
                            is_active=True
                        )
                    else:
                        raise serializers.ValidationError('Identifiants invalides.')
                except Membre.DoesNotExist:
                    try:
                        client = Client.objects.get(email=email)
                        if check_password(password, client.password):
                            # Créer le compte User automatiquement
                            username = f"client_{client.numero_compte}"
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"client_{client.numero_compte}_{counter}"
                                counter += 1
                            
                            user = User.objects.create(
                                username=username,
                                email=email,
                                password='',  # Pas de password dans User
                                user_type='CLIENT',
                                client=client,
                                is_active=True
                            )
                        else:
                            raise serializers.ValidationError('Identifiants invalides.')
                    except Client.DoesNotExist:
                        raise serializers.ValidationError('Identifiants invalides.')
        elif username:
            # Authentification par username (pour ADMIN et SUPERADMIN)
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides.')
        
        if not user:
            raise serializers.ValidationError('Identifiants invalides.')
        
        if not user.is_active:
            raise serializers.ValidationError('Ce compte est désactivé.')
        
        attrs['user'] = user
        return attrs


class RegisterMembreSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription d'un membre
    Crée automatiquement le Membre ET le compte User lié
    """
    # Champs communs obligatoires
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    telephone = serializers.CharField(max_length=50)
    type_membre = serializers.ChoiceField(choices=[('PHYSIQUE', 'Personne physique'), ('MORALE', 'Personne morale (Entreprise)')], default='PHYSIQUE')
    
    # Champs optionnels communs
    adresse = serializers.CharField(max_length=255, required=False, allow_blank=True)
    annee_adhesion = serializers.IntegerField(required=False, allow_null=True, min_value=1900, max_value=2100, help_text="Année d'adhésion (optionnel, utilise l'année courante si non renseigné)")
    ville = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    photo_profil = serializers.ImageField(required=False, allow_null=True)
    
    # Champs pour personne physique
    nom = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postnom = serializers.CharField(max_length=100, required=False, allow_blank=True)
    prenom = serializers.CharField(max_length=100, required=False, allow_blank=True)
    sexe = serializers.ChoiceField(choices=[('M', 'Masculin'), ('F', 'Féminin')], required=False, allow_null=True)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    
    # Champs pour personne morale
    raison_sociale = serializers.CharField(max_length=255, required=False, allow_blank=True)
    sigle = serializers.CharField(max_length=50, required=False, allow_blank=True)
    numero_immatriculation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    forme_juridique = serializers.CharField(max_length=100, required=False, allow_blank=True)
    representant_legal = serializers.CharField(max_length=255, required=False, allow_blank=True)
    secteur_activite = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Valide l'email"""
        if not value:
            raise serializers.ValidationError("L'adresse email est obligatoire.")
        
        try:
            value = validate_email_exists(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Vérifier que l'email n'est pas déjà utilisé
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée.")
        if Membre.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée par un membre.")
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée par un client.")
        
        return value
    
    def validate_password(self, value):
        """Valide le mot de passe"""
        if not value:
            raise serializers.ValidationError("Le mot de passe est obligatoire.")
        
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate(self, attrs):
        """Valide que les champs sont cohérents selon le type de membre"""
        type_membre = attrs.get('type_membre', 'PHYSIQUE')
        
        if type_membre == 'PHYSIQUE':
            # Personne physique : valider les champs requis
            if not attrs.get('nom'):
                raise serializers.ValidationError({'nom': 'Le nom est requis pour une personne physique.'})
            if not attrs.get('prenom'):
                raise serializers.ValidationError({'prenom': 'Le prénom est requis pour une personne physique.'})
            if not attrs.get('sexe'):
                raise serializers.ValidationError({'sexe': 'Le sexe est requis pour une personne physique.'})
        elif type_membre == 'MORALE':
            # Personne morale : valider les champs requis
            if not attrs.get('raison_sociale') and not attrs.get('sigle'):
                raise serializers.ValidationError({
                    'raison_sociale': 'La raison sociale ou le sigle est requis pour une personne morale.',
                    'sigle': 'La raison sociale ou le sigle est requis pour une personne morale.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Crée le Membre et le compte User"""
        from django.contrib.auth.hashers import make_password
        
        password = validated_data.pop('password')
        email = validated_data['email']
        
        # Hash le mot de passe
        validated_data['password'] = make_password(password)
        
        # Créer le membre
        membre = Membre.objects.create(**validated_data)
        
        # Générer un username unique
        username = f"membre_{membre.numero_compte}"
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"membre_{membre.numero_compte}_{counter}"
            counter += 1
        
        # Créer l'utilisateur
        user = User.objects.create(
            username=username,
            email=email,
            password='',  # Pas de password dans User, on utilise celui du Membre
            user_type='MEMBRE',
            membre=membre,
            is_active=True
        )
        
        return user


class RegisterClientSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription d'un client
    Crée automatiquement le Client ET le compte User lié
    """
    # Champs obligatoires
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    sexe = serializers.ChoiceField(choices=[('M', 'Masculin'), ('F', 'Féminin')])
    telephone = serializers.CharField(max_length=50)
    
    # Champs optionnels
    postnom = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    adresse = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    annee_adhesion = serializers.IntegerField(required=False, allow_null=True, min_value=1900, max_value=2100, help_text="Année d'adhésion (optionnel, utilise l'année courante si non renseigné)")
    ville = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    photo_profil = serializers.ImageField(required=False, allow_null=True)
    parrain_id = serializers.IntegerField(required=False, allow_null=True, help_text="ID du membre parrain (optionnel)")
    
    def validate_email(self, value):
        """Valide l'email"""
        if not value:
            raise serializers.ValidationError("L'adresse email est obligatoire.")
        
        try:
            value = validate_email_exists(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Vérifier que l'email n'est pas déjà utilisé
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée.")
        if Membre.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée par un membre.")
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée par un client.")
        
        return value
    
    def validate_password(self, value):
        """Valide le mot de passe"""
        if not value:
            raise serializers.ValidationError("Le mot de passe est obligatoire.")
        
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_parrain_id(self, value):
        """Vérifie que le parrain existe si fourni"""
        if value is not None:
            try:
                Membre.objects.get(id=value)
            except Membre.DoesNotExist:
                raise serializers.ValidationError("Le membre parrain spécifié n'existe pas.")
        return value
    
    def create(self, validated_data):
        """Crée le Client et le compte User"""
        from django.contrib.auth.hashers import make_password
        
        password = validated_data.pop('password')
        email = validated_data['email']
        parrain_id = validated_data.pop('parrain_id', None)
        
        # Hash le mot de passe
        validated_data['password'] = make_password(password)
        
        # Ajouter le parrain si fourni
        if parrain_id:
            validated_data['parrain_id'] = parrain_id
        
        # Créer le client
        client = Client.objects.create(**validated_data)
        
        # Générer un username unique
        username = f"client_{client.numero_compte}"
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"client_{client.numero_compte}_{counter}"
            counter += 1
        
        # Créer l'utilisateur
        user = User.objects.create(
            username=username,
            email=email,
            password='',  # Pas de password dans User, on utilise celui du Client
            user_type='CLIENT',
            client=client,
            is_active=True
        )
        
        return user


class RegisterAdminSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription d'un ADMIN
    Seul un SUPERADMIN ou un ADMIN peut créer un ADMIN
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    user_type = serializers.ChoiceField(choices=[('ADMIN', 'Administrateur'), ('SUPERADMIN', 'Super Administrateur')], default='ADMIN')
    
    def validate_username(self, value):
        """Vérifie que le username est unique"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value
    
    def validate_email(self, value):
        """Valide l'email si fourni"""
        if value:
            try:
                value = validate_email_exists(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
            
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Cette adresse email est déjà utilisée.")
        return value
    
    def validate_password(self, value):
        """Valide le mot de passe"""
        if not value:
            raise serializers.ValidationError("Le mot de passe est obligatoire.")
        
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_user_type(self, value):
        """Valide le type d'utilisateur"""
        # Seul un SUPERADMIN peut créer un SUPERADMIN
        # Cette validation sera faite dans la vue
        return value
    
    def create(self, validated_data):
        """Crée le compte User pour l'admin"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = validated_data['username']
        email = validated_data.get('email', '')
        password = validated_data['password']
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        user_type = validated_data.get('user_type', 'ADMIN')
        
        # Créer l'utilisateur avec le password hashé
        user = User.objects.create_user(
            username=username,
            email=email if email else None,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            is_staff=True if user_type == 'SUPERADMIN' else False,
            is_superuser=True if user_type == 'SUPERADMIN' else False,
            is_active=True
        )
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe d'un utilisateur ADMIN/SUPERADMIN
    """
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Nouveau mot de passe (minimum 6 caractères avec lettres, chiffres et caractères spéciaux)"
    )
    
    def validate_new_password(self, value):
        """Valide la force du nouveau mot de passe"""
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value


class ChangeMembreClientPasswordSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe d'un membre ou client
    Nécessite l'ancien mot de passe pour vérification
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Ancien mot de passe (pour vérification)"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Nouveau mot de passe (minimum 6 caractères avec lettres, chiffres et caractères spéciaux)"
    )
    
    def validate_new_password(self, value):
        """Valide la force du nouveau mot de passe"""
        try:
            validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate(self, attrs):
        """Valide que l'ancien mot de passe est correct"""
        old_password = attrs.get('old_password')
        user = self.context.get('user')
        
        if not user:
            raise serializers.ValidationError("Utilisateur non trouvé.")
        
        # Vérifier l'ancien mot de passe selon le type d'utilisateur
        if user.user_type == 'MEMBRE' and user.membre:
            if not check_password(old_password, user.membre.password):
                raise serializers.ValidationError({'old_password': 'L\'ancien mot de passe est incorrect.'})
        elif user.user_type == 'CLIENT' and user.client:
            if not check_password(old_password, user.client.password):
                raise serializers.ValidationError({'old_password': 'L\'ancien mot de passe est incorrect.'})
        else:
            raise serializers.ValidationError("Type d'utilisateur non supporté pour ce changement de mot de passe.")
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations de l'utilisateur connecté
    """
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'user_type_display', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'email', 'user_type', 'is_active', 'date_joined', 'last_login']

