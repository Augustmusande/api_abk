from rest_framework import serializers
from decimal import Decimal
import os
from .models import Depenses, CaisseType, Caissetypemvt, DonDirect

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class DepensesSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Depenses.
    """
    pt = serializers.ReadOnlyField(help_text="Prix total (calculé dynamiquement : quantite × pu)")

    class Meta:
        model = Depenses
        fields = '__all__'
        read_only_fields = ('pt', 'created_at', 'updated_at')

    def validate(self, attrs):
        """
        Validation personnalisée pour s'assurer que les valeurs sont cohérentes
        et que le solde de la caisse est suffisant.
        """
        quantite = attrs.get('quantite')
        pu = attrs.get('pu')

        if quantite is not None and quantite <= 0:
            raise serializers.ValidationError({
                'quantite': 'La quantité doit être supérieure à 0.'
            })

        if pu is not None and pu < 0:
            raise serializers.ValidationError({
                'pu': 'Le prix unitaire ne peut pas être négatif.'
            })
        
        # Vérifier les frais de gestion disponibles avant de créer ou modifier une dépense
        # IMPORTANT : Les dépenses sont financées par les frais de gestion.
        # Le montant minimum qui doit rester dans les frais de gestion est de 5.
        if quantite and pu:
            montant_depense = Decimal(str(quantite)) * Decimal(str(pu))
            frais_gestion_disponible = self._calculer_frais_gestion_disponible()
            
            # Seuil minimum : 5 (montant minimum qui doit rester dans les frais de gestion)
            seuil_minimum = Decimal('5.00')
            
            # Vérifier que les frais de gestion disponibles sont suffisants
            if frais_gestion_disponible < seuil_minimum:
                raise serializers.ValidationError({
                    'non_field_errors': [
                        f"Opération refusée : Les frais de gestion disponibles ({frais_gestion_disponible:.2f}) sont insuffisants "
                        f"(seuil minimum requis : {seuil_minimum}). "
                        f"Vous ne pouvez pas effectuer cette dépense de {montant_depense:.2f}. "
                        f"Veuillez d'abord augmenter les frais de gestion (via les intérêts des crédits et les frais d'adhésion)."
                    ]
                })
            
            # Vérifier que le montant restant après la dépense sera >= seuil_minimum
            frais_gestion_apres_depense = frais_gestion_disponible - montant_depense
            if frais_gestion_apres_depense < seuil_minimum:
                raise serializers.ValidationError({
                    'non_field_errors': [
                        f"Opération refusée : Cette dépense de {montant_depense:.2f} ferait passer les frais de gestion disponibles "
                        f"en dessous du seuil minimum ({seuil_minimum}). "
                        f"Frais de gestion disponibles actuellement : {frais_gestion_disponible:.2f}, "
                        f"frais de gestion après dépense : {frais_gestion_apres_depense:.2f}. "
                        f"Le montant maximum que vous pouvez dépenser est de {frais_gestion_disponible - seuil_minimum:.2f}."
                    ]
                })

        return attrs
    
    def _calculer_frais_gestion_disponible(self):
        """
        Calcule les frais de gestion disponibles pour les dépenses.
        
        IMPORTANT : Utilise le total global (sans période) car les dépenses ne sont pas limitées à une période.
        Utilise le pourcentage par défaut de 20% (même que l'endpoint par défaut).
        
        Formule :
        frais_gestion_disponible = frais_gestion_total_global - total_depenses_existantes
        
        Où :
        - frais_gestion_total_global = frais_gestion_interets + total_frais_adhesion (TOUTES les années)
        - total_depenses_existantes = somme de toutes les dépenses existantes
        
        Returns:
            Decimal: Montant des frais de gestion disponibles
        """
        from caisse.services import calculer_frais_gestion
        
        # IMPORTANT : Utiliser periode_annee=None pour avoir le total global (toutes les années)
        # car les dépenses ne sont pas limitées à une période spécifique
        # Utiliser le pourcentage par défaut de 20% (même que l'endpoint par défaut)
        resultats_frais = calculer_frais_gestion(pourcentage=20, periode_annee=None)
        frais_gestion_total_global = Decimal(str(resultats_frais['frais_gestion_total_global']))
        
        # Calculer le total des dépenses existantes
        # Exclure la dépense actuelle si c'est une mise à jour
        depenses_query = Depenses.objects.all()
        if self.instance and self.instance.pk:
            # Si c'est une mise à jour, exclure la dépense actuelle du calcul
            depenses_query = depenses_query.exclude(pk=self.instance.pk)
        
        total_depenses_existantes = Decimal('0.00')
        for depense in depenses_query:
            total_depenses_existantes += Decimal(str(depense.pt))
        
        # Les frais de gestion disponibles = frais_gestion_total - dépenses existantes
        frais_gestion_disponible = frais_gestion_total_global - total_depenses_existantes
        
        # S'assurer que le montant ne soit pas négatif
        if frais_gestion_disponible < 0:
            frais_gestion_disponible = Decimal('0.00')
        
        return frais_gestion_disponible

class DonDirectSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle DonDirect.
    Permet de créer des dons directs de personnes qui ne sont ni membres ni clients.
    """
    class Meta:
        model = DonDirect
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def validate_montant(self, value):
        """Valide que le montant est positif"""
        if value <= 0:
            raise serializers.ValidationError("Le montant du don doit être supérieur à 0.")
        return value
    
    def create(self, validated_data):
        """
        Crée le DonDirect et le Caissetypemvt associé automatiquement.
        """
        # Extraire caissetype_id si fourni dans les données
        caissetype_id = None
        if hasattr(self.context.get('request', None), 'data'):
            caissetype_id = self.context['request'].data.get('caissetype_id')
        
        # Créer le DonDirect
        don_direct = super().create(validated_data)
        
        # Créer automatiquement le Caissetypemvt
        from caisse.models import Caissetypemvt, CaisseType
        
        # Récupérer le type de caisse (utiliser celui fourni ou le premier disponible)
        caissetype = None
        if caissetype_id:
            try:
                caissetype = CaisseType.objects.get(id=caissetype_id)
            except CaisseType.DoesNotExist:
                pass
        
        if not caissetype:
            caissetype = CaisseType.objects.first()
        
        if caissetype:
            # Utiliser get_or_create() pour éviter les doublons de manière atomique
            # Permet plusieurs Caissetypemvt pour le même DonDirect mais avec des caissetype différents
            try:
                date_don = don_direct.date_don
                if not date_don:
                    from datetime import date
                    date_don = date.today()
                
                # Inclure caissetype dans le lookup pour permettre plusieurs Caissetypemvt
                # pour le même DonDirect mais avec des caissetype différents
                mvt, created = Caissetypemvt.objects.get_or_create(
                    dondirect=don_direct,
                    caissetype=caissetype,
                    defaults={
                        'date': date_don
                    }
                )
            except Exception as e:
                # Logger l'erreur mais ne pas bloquer la création du DonDirect
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la création du Caissetypemvt pour DonDirect {don_direct.id}: {str(e)}")
        
        return don_direct

class CaisseTypeSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle CaisseType.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CaisseType
        fields = '__all__'
        extra_kwargs = {
            'image': {'write_only': False}
        }
        read_only_fields = ('last_updated', 'created_at')
    
    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image"""
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate_nom(self, value):
        """Valide que le nom est unique et non vide"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du type de caisse est obligatoire.")
        return value.strip()
    
    def validate_image(self, value):
        """Validation de l'image"""
        if value is None:
            return value
        
        # Si c'est une mise à jour et qu'on reçoit une chaîne vide, on garde l'ancienne image
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
        
        return value

class CaissetypemvtSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Caissetypemvt.
    Permet de lier un type de caisse à une donnation/remboursement/frais d'adhésion/dépense/retrait.
    """
    caissetype_nom = serializers.CharField(source='caissetype.nom', read_only=True)
    date = serializers.DateField(read_only=True, help_text="Date du mouvement (automatique, non modifiable)")
    
    class Meta:
        model = Caissetypemvt
        fields = '__all__'
        read_only_fields = ('date', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Valide qu'au moins une des 8 relations est spécifiée et empêche les doublons"""
        remboursement = attrs.get('remboursement') or (self.instance.remboursement if self.instance else None)
        credit = attrs.get('credit') or (self.instance.credit if self.instance else None)
        donnatepargne = attrs.get('donnatepargne') or (self.instance.donnatepargne if self.instance else None)
        donnatpartsocial = attrs.get('donnatpartsocial') or (self.instance.donnatpartsocial if self.instance else None)
        fraisadhesion = attrs.get('fraisadhesion') or (self.instance.fraisadhesion if self.instance else None)
        depense = attrs.get('depense') or (self.instance.depense if self.instance else None)
        retrait = attrs.get('retrait') or (self.instance.retrait if self.instance else None)
        dondirect = attrs.get('dondirect') or (self.instance.dondirect if self.instance else None)
        
        relations = [remboursement, credit, donnatepargne, donnatpartsocial, fraisadhesion, depense, retrait, dondirect]
        if not any(relations):
            raise serializers.ValidationError({
                'non_field_errors': [
                    "Au moins une relation (remboursement, credit, donnatepargne, donnatpartsocial, fraisadhesion, depense, retrait ou dondirect) doit être spécifiée."
                ]
            })
        
        # Empêcher les doublons : vérifier si un Caissetypemvt existe déjà pour cette relation
        # (sauf si c'est une mise à jour de l'instance existante)
        # Note: Les doublons sont gérés dans create() avec get_or_create()
        
        # S'assurer que date n'est pas fourni (sera rempli automatiquement)
        attrs.pop('date', None)
        
        return attrs
    
    def create(self, validated_data):
        """
        Crée un Caissetypemvt en utilisant get_or_create() pour éviter les doublons.
        Si un Caissetypemvt existe déjà pour la relation ET le caissetype spécifiés, retourne l'instance existante.
        Cette méthode est idempotente : appeler plusieurs fois avec les mêmes paramètres retourne la même instance.
        Permet plusieurs Caissetypemvt pour la même relation mais avec des caissetype différents.
        """
        # Déterminer quelle relation est fournie
        fraisadhesion = validated_data.get('fraisadhesion')
        remboursement = validated_data.get('remboursement')
        credit = validated_data.get('credit')
        depense = validated_data.get('depense')
        retrait = validated_data.get('retrait')
        donnatepargne = validated_data.get('donnatepargne')
        donnatpartsocial = validated_data.get('donnatpartsocial')
        dondirect = validated_data.get('dondirect')
        caissetype = validated_data.get('caissetype')
        
        # Utiliser get_or_create() pour éviter les doublons
        # Construire les filtres de recherche
        # IMPORTANT: Inclure caissetype dans le lookup pour permettre plusieurs Caissetypemvt
        # pour la même relation mais avec des caissetype différents
        lookup = {}
        if caissetype:
            lookup['caissetype'] = caissetype
        if fraisadhesion:
            lookup['fraisadhesion'] = fraisadhesion
        if remboursement:
            lookup['remboursement'] = remboursement
        if credit:
            lookup['credit'] = credit
        if depense:
            lookup['depense'] = depense
        if retrait:
            lookup['retrait'] = retrait
        if donnatepargne:
            lookup['donnatepargne'] = donnatepargne
        if donnatpartsocial:
            lookup['donnatpartsocial'] = donnatpartsocial
        if dondirect:
            lookup['dondirect'] = dondirect
        
        # Utiliser get_or_create() pour éviter les doublons
        # Cette méthode est atomique et idempotente
        try:
            instance, created = Caissetypemvt.objects.get_or_create(
                **lookup,
                defaults=validated_data
            )
            # Si l'instance existe déjà, on la retourne sans erreur
            # C'est le comportement attendu pour éviter les doublons
            return instance
        except Exception as e:
            # En cas d'erreur, essayer de récupérer l'instance existante
            # Cela peut arriver en cas de race condition
            try:
                instance = Caissetypemvt.objects.get(**lookup)
                return instance
            except Caissetypemvt.DoesNotExist:
                # Si l'instance n'existe pas, lever l'erreur originale
                raise

