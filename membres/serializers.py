
from rest_framework import serializers
from .models import FraisAdhesion, PartSocial, Compte, SouscriptEpargne, DonnatEpargne, DonnatPartSocial, SouscriptionPartSocial, Retrait
from users.models import *
from caisse.models import CaisseType



from users.serializers import MembreSerializer, ClientSerializer


# Serializer pour FraisAdhesion
class FraisAdhesionSerializer(serializers.ModelSerializer):
    membre_numero = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    client_numero = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    titulaire_membre = MembreSerializer(read_only=True)
    titulaire_client = ClientSerializer(read_only=True)

    class Meta:
        model = FraisAdhesion
        fields = '__all__'
        extra_kwargs = {
            'titulaire_membre': {'read_only': True},
            'titulaire_client': {'read_only': True},
        }

    def validate(self, data):
        membre_num = data.pop('membre_numero', None)
        client_num = data.pop('client_numero', None)
        
        # Nettoyer les valeurs vides
        if membre_num == '' or membre_num is None:
            membre_num = None
        if client_num == '' or client_num is None:
            client_num = None
        
        # Vérifier qu'au moins un des deux est fourni
        if not membre_num and not client_num:
            raise serializers.ValidationError(
                "Vous devez fournir soit 'membre_numero' soit 'client_numero' (au moins un des deux est requis)."
            )
        
        # Vérifier qu'ils ne sont pas tous les deux fournis en même temps
        if membre_num and client_num:
            raise serializers.ValidationError(
                "Vous ne pouvez pas fournir 'membre_numero' et 'client_numero' en même temps. Choisissez l'un ou l'autre."
            )
        
        membre_obj = None
        client_obj = None
        
        if membre_num:
            try:
                from users.models import Membre
                membre_obj = Membre.objects.get(numero_compte=membre_num)
            except Membre.DoesNotExist:
                raise serializers.ValidationError({"membre_numero": "Aucun membre avec ce numero_compte."})
            data['titulaire_membre'] = membre_obj
            data['titulaire_client'] = None
        
        if client_num:
            try:
                from users.models import Client
                client_obj = Client.objects.get(numero_compte=client_num)
            except Client.DoesNotExist:
                raise serializers.ValidationError({"client_numero": "Aucun client avec ce numero_compte."})
            data['titulaire_client'] = client_obj
            data['titulaire_membre'] = None
        
        return data
    
    def create(self, validated_data):
        """
        Crée le FraisAdhesion et le Caissetypemvt associé automatiquement.
        Les frais d'adhésion sont ajoutés au compte frais de gestion.
        """
        # Extraire caissetype_id si fourni dans les données
        caissetype_id = None
        if hasattr(self.context.get('request', None), 'data'):
            caissetype_id = self.context['request'].data.get('caissetype_id')
        
        # Créer le FraisAdhesion
        frais_adhesion = super().create(validated_data)
        
        # Créer automatiquement le Caissetypemvt pour ajouter au compte frais de gestion
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
            # Permet plusieurs Caissetypemvt pour le même FraisAdhesion mais avec des caissetype différents
            try:
                # Vérifier que date_paiement est valide
                date_paiement = frais_adhesion.date_paiement
                if not date_paiement:
                    from datetime import date
                    date_paiement = date.today()
                
                # Inclure caissetype dans le lookup pour permettre plusieurs Caissetypemvt
                # pour le même FraisAdhesion mais avec des caissetype différents
                mvt, created = Caissetypemvt.objects.get_or_create(
                    fraisadhesion=frais_adhesion,
                    caissetype=caissetype,
                    defaults={
                        'date': date_paiement
                    }
                )
            except Exception as e:
                # Logger l'erreur mais ne pas bloquer la création du FraisAdhesion
                import logging
                import traceback
                logger = logging.getLogger(__name__)
                error_msg = f"Erreur lors de la création du Caissetypemvt pour FraisAdhesion {frais_adhesion.id}: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                print(f"Frais d'adhésion créé mais erreur lors de la création du mouvement de caisse : {str(e)}")
                # Ne pas lever l'exception pour ne pas bloquer la création du FraisAdhesion
        else:
            # Logger un avertissement si aucun type de caisse n'est disponible
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Aucun type de caisse disponible pour créer le Caissetypemvt pour FraisAdhesion {frais_adhesion.id}")
        
        return frais_adhesion
# Serializer pour PartSocial
class PartSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartSocial
        fields = '__all__'

# Serializer pour SouscriptionPartSocial
class SouscriptionPartSocialSerializer(serializers.ModelSerializer):
    membre = MembreSerializer(read_only=True)
    membre_numero = serializers.CharField(write_only=True, required=True)
    partSocial = PartSocialSerializer(read_only=True)
    partSocial_id = serializers.PrimaryKeyRelatedField(queryset=PartSocial.objects.all(), write_only=True, source='partSocial')
    nombre_versements_effectues = serializers.ReadOnlyField()
    montant_total_verse = serializers.ReadOnlyField()
    montant_cible = serializers.ReadOnlyField()
    est_complete = serializers.ReadOnlyField()
    montant_restant = serializers.ReadOnlyField()
    
    class Meta:
        model = SouscriptionPartSocial
        fields = '__all__'
    
    def validate(self, data):
        membre_num = data.pop('membre_numero', None)
        if not membre_num:
            raise serializers.ValidationError({"membre_numero": "Le numéro du membre est requis."})
        
        try:
            from users.models import Membre
            membre_obj = Membre.objects.get(numero_compte=membre_num)
        except Membre.DoesNotExist:
            raise serializers.ValidationError({"membre_numero": "Aucun membre avec ce numero_compte."})
        
        data['membre'] = membre_obj
        
        # Vérifier qu'un membre ne souscrit qu'une fois à une part sociale
        part_social = data.get('partSocial')
        if part_social and SouscriptionPartSocial.objects.filter(membre=membre_obj, partSocial=part_social).exists():
            raise serializers.ValidationError(
                f"Ce membre a déjà souscrit à cette part sociale ({part_social.annee})."
            )
        
        return data


class CompteSerializer(serializers.ModelSerializer):
    titulaire_membre = MembreSerializer(read_only=True)
    titulaire_client = ClientSerializer(read_only=True)
    titulaire_membre_numero = serializers.CharField(write_only=True, required=False, allow_null=True)
    titulaire_client_numero = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Compte
        fields = '__all__'
        extra_kwargs = {
            'titulaire_membre': {'read_only': True},
            'titulaire_client': {'read_only': True},
        }

    def validate(self, data):
        membre_num = data.pop('titulaire_membre_numero', None)
        client_num = data.pop('titulaire_client_numero', None)
        membre_obj = None
        client_obj = None
        if membre_num:
            try:
                membre_obj = Membre.objects.get(numero_compte=membre_num)
            except Membre.DoesNotExist:
                raise serializers.ValidationError({"titulaire_membre_numero": "Aucun membre avec ce numero_compte."})
        if client_num:
            try:
                client_obj = Client.objects.get(numero_compte=client_num)
            except Client.DoesNotExist:
                raise serializers.ValidationError({"titulaire_client_numero": "Aucun client avec ce numero_compte."})
        if not membre_obj and not client_obj:
            raise serializers.ValidationError("Un compte doit être lié à un membre ou un client.")
        data['titulaire_membre'] = membre_obj
        data['titulaire_client'] = client_obj
        return data






# --- Déclaration de SouscriptEpargneSerializer avant DonnatEpargneSerializer ---
class SouscriptEpargneSerializer(serializers.ModelSerializer):
    total_donne = serializers.ReadOnlyField(help_text="Montant total déjà donné")
    total_retire = serializers.ReadOnlyField(help_text="Montant total retiré")
    solde_epargne = serializers.ReadOnlyField(help_text="Solde actuel de l'épargne (dons - retraits)")
    montant_restant = serializers.ReadOnlyField(help_text="Montant restant à verser (None si épargne illimitée)")
    date_souscription = serializers.DateField(read_only=True, help_text="Date de souscription (automatique, non modifiable)")
    compte = CompteSerializer(read_only=True)
    compte_numero = serializers.CharField(write_only=True, required=False, allow_null=True)
    montant_souscrit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, help_text="Montant cible (optionnel, null = épargne illimitée)")

    class Meta:
        model = SouscriptEpargne
        fields = '__all__'
        extra_kwargs = {
            'montant_souscrit': {'required': False, 'allow_null': True},
            'date_souscription': {'read_only': True},
        }

    def validate(self, data):
        compte_num = data.pop('compte_numero', None)
        if compte_num:
            from .models import Compte
            # Le compte peut être identifié par l'ID ou via le membre/client
            try:
                # Essayer d'abord par ID
                compte_obj = Compte.objects.get(id=compte_num)
            except (Compte.DoesNotExist, ValueError):
                # Si ce n'est pas un ID, essayer de trouver via le membre ou client
                try:
                    from users.models import Membre, Client
                    # Chercher via le numéro de compte du membre
                    membre = Membre.objects.get(numero_compte=compte_num)
                    compte_obj = Compte.objects.filter(titulaire_membre=membre).first()
                    if not compte_obj:
                        raise Compte.DoesNotExist
                except (Membre.DoesNotExist, Compte.DoesNotExist):
                    try:
                        # Chercher via le numéro de compte du client
                        client = Client.objects.get(numero_compte=compte_num)
                        compte_obj = Compte.objects.filter(titulaire_client=client).first()
                        if not compte_obj:
                            raise Compte.DoesNotExist
                    except (Client.DoesNotExist, Compte.DoesNotExist):
                        raise serializers.ValidationError({
                            "compte_numero": "Aucun compte trouvé avec cet identifiant ou ce numéro de membre/client."
                        })
            data['compte'] = compte_obj
        
        # S'assurer que date_souscription n'est pas fourni (sera rempli automatiquement)
        data.pop('date_souscription', None)
        
        return data

# --- DonnatEpargneSerializer avec inner join sur souscriptEpargne ---
class DonnatEpargneSerializer(serializers.ModelSerializer):
    souscriptEpargne = SouscriptEpargneSerializer(read_only=True)
    souscriptEpargne_id = serializers.PrimaryKeyRelatedField(
        queryset=SouscriptEpargne.objects.all(), 
        write_only=True, 
        source='souscriptEpargne',
        help_text="ID de la souscription d'épargne (seules les souscriptions non complètes sont disponibles)"
    )
    montant_restant = serializers.SerializerMethodField(help_text="Montant restant à verser sur la souscription")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from decimal import Decimal
        from .models import SouscriptEpargne
        
        # Filtrer les souscriptions qui ont atteint leur montant souscrit
        # On garde seulement :
        # - Les souscriptions avec montant_souscrit=None (illimitées)
        # - Les souscriptions où montant_restant > 0
        queryset = SouscriptEpargne.objects.all()
        
        # Filtrer manuellement pour exclure celles qui ont atteint leur but
        souscriptions_valides = []
        for souscription in queryset:
            if souscription.montant_souscrit is None:
                # Épargne illimitée, toujours valide
                souscriptions_valides.append(souscription.id)
            else:
                # Vérifier si le montant restant > 0
                montant_restant = souscription.montant_restant
                if montant_restant is not None and montant_restant > Decimal('0.00'):
                    souscriptions_valides.append(souscription.id)
        
        # Mettre à jour le queryset
        if souscriptions_valides:
            self.fields['souscriptEpargne_id'].queryset = SouscriptEpargne.objects.filter(id__in=souscriptions_valides)
        else:
            # Si aucune souscription valide, utiliser un queryset vide
            self.fields['souscriptEpargne_id'].queryset = SouscriptEpargne.objects.none()

    class Meta:
        model = DonnatEpargne
        fields = '__all__'
    
    def validate(self, attrs):
        """
        Valide que le montant souscrit n'est pas dépassé.
        """
        from decimal import Decimal
        
        souscript_epargne = attrs.get('souscriptEpargne')
        montant = attrs.get('montant')
        
        if souscript_epargne and montant:
            # Si montant_souscrit est None, c'est une épargne illimitée, on accepte
            if souscript_epargne.montant_souscrit is None:
                return attrs
            
            # Calculer le montant total après cette donation
            total_actuel = souscript_epargne.total_donne
            montant_decimal = Decimal(str(montant))
            total_apres_donation = total_actuel + montant_decimal
            montant_souscrit = Decimal(str(souscript_epargne.montant_souscrit))
            
            # Vérifier si le montant souscrit serait dépassé
            if total_apres_donation > montant_souscrit:
                montant_restant = montant_souscrit - total_actuel
                raise serializers.ValidationError({
                    "montant": f"Le montant souscrit ({souscript_epargne.montant_souscrit}) est déjà atteint ou serait dépassé. "
                               f"Montant total déjà versé: {total_actuel}. "
                               f"Montant restant autorisé: {max(Decimal('0.00'), montant_restant)}. "
                               f"Vous essayez d'ajouter {montant}, ce qui dépasserait le montant souscrit."
                })
        
        return attrs
    
    def get_montant_restant(self, obj):
        """
        Retourne le montant restant à verser sur la souscription d'épargne.
        Retourne None si l'épargne est illimitée (montant_souscrit est None).
        """
        if obj.souscriptEpargne:
            montant_restant = obj.souscriptEpargne.montant_restant
            if montant_restant is None:
                return None  # Épargne illimitée
            return float(montant_restant)
        return None









class DonnatPartSocialSerializer(serializers.ModelSerializer):
    souscription_part_social = SouscriptionPartSocialSerializer(read_only=True)
    souscription_part_social_id = serializers.PrimaryKeyRelatedField(
        queryset=SouscriptionPartSocial.objects.all(), 
        write_only=True, 
        source='souscription_part_social',
        required=True,
        allow_null=False
    )
    
    class Meta:
        model = DonnatPartSocial
        fields = '__all__'
    
    def validate(self, data):
        souscription = data.get('souscription_part_social')
        montant = data.get('montant')
        
        if souscription and montant:
            montant_cible = souscription.montant_cible
            
            # Si le montant cible est déjà atteint, on ne peut plus ajouter de versements
            montant_total_actuel = souscription.montant_total_verse
            if montant_total_actuel >= montant_cible:
                raise serializers.ValidationError(
                    f"Le montant cible ({montant_cible} FCFA) a déjà été atteint. La souscription est complète."
                )
            
            # Vérifier que le montant après ne dépasse pas le montant cible
            montant_apres = montant_total_actuel + montant
            if montant_apres > montant_cible:
                raise serializers.ValidationError(
                    f"Le montant total des versements ({montant_apres} FCFA) dépasse le montant cible "
                    f"({montant_cible} FCFA = {souscription.partSocial.montant_souscrit} FCFA × {souscription.nombre_versements_prevu}). "
                    f"Montant restant: {souscription.montant_restant} FCFA"
                )
        
        return data


class RetraitSerializer(serializers.ModelSerializer):
    """
    Serializer pour les retraits d'argent sur les souscriptions d'épargne.
    
    Règles de validation:
    - Seules les épargnes peuvent être retirées
    - Vérifier que le membre/client a des souscriptions
    - Vérifier que la souscription appartient bien au membre/client
    - Vérifier que le solde après retrait ne soit pas <= 0
    - Pour comptes BLOQUE: mot d'engagement requis (sensible à la casse)
    - Pour comptes VUE: pas besoin de mot d'engagement
    """
    souscriptEpargne = SouscriptEpargneSerializer(read_only=True)
    souscriptEpargne_id = serializers.PrimaryKeyRelatedField(
        queryset=SouscriptEpargne.objects.all(),
        write_only=True,
        source='souscriptEpargne',
        help_text="ID de la souscription d'épargne"
    )
    date_operation = serializers.DateTimeField(read_only=True, help_text="Date de l'opération (automatique)")
    solde_epargne = serializers.SerializerMethodField(help_text="Solde actuel de l'épargne (dons - retraits)")
    mot_engagement = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Mot d'engagement requis pour les comptes bloqués (sensible à la casse)"
    )
    membre_numero = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Numéro du membre (pour vérifier la propriété de la souscription)"
    )
    client_numero = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Numéro du client (pour vérifier la propriété de la souscription)"
    )
    caissetype_id = serializers.PrimaryKeyRelatedField(
        queryset=CaisseType.objects.all(),
        required=True,
        write_only=True,
        help_text="ID du type de caisse (obligatoire)",
        allow_null=False
    )
    
    # Mot d'engagement exact pour les comptes bloqués
    MOT_ENGAGEMENT_BLOQUE = "Je suis conscient de la gravité que cela implique de retirer l'argent sur le compte bloqué avant les dates prévues qui sont juin et décembre"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from caisse.models import CaisseType
        if 'caissetype_id' in self.fields:
            self.fields['caissetype_id'].queryset = CaisseType.objects.all()
    
    class Meta:
        model = Retrait
        fields = [
            'id', 'montant', 'date_operation', 'souscriptEpargne', 'souscriptEpargne_id',
            'motif', 'solde_epargne', 'mot_engagement', 'membre_numero', 'client_numero', 'caissetype_id'
        ]
        read_only_fields = ['date_operation']
    
    def get_solde_epargne(self, obj):
        """Retourne le solde actuel de l'épargne"""
        if obj.souscriptEpargne:
            return float(obj.souscriptEpargne.solde_epargne)
        return None
    
    def validate(self, attrs):
        """
        Valide le retrait selon les règles métier.
        """
        from decimal import Decimal
        
        souscript_epargne = attrs.get('souscriptEpargne')
        montant = attrs.get('montant')
        mot_engagement = attrs.pop('mot_engagement', None)
        membre_numero = attrs.pop('membre_numero', None)
        client_numero = attrs.pop('client_numero', None)
        
        if not souscript_epargne:
            raise serializers.ValidationError({
                'souscriptEpargne_id': "La souscription d'épargne est requise."
            })
        
        if not montant or montant <= 0:
            raise serializers.ValidationError({
                'montant': "Le montant doit être supérieur à 0."
            })
        
        # Vérifier que le membre/client a des souscriptions
        compte = souscript_epargne.compte
        
        # Vérifier la propriété de la souscription
        if membre_numero:
            try:
                membre = Membre.objects.get(numero_compte=membre_numero)
                if compte.titulaire_membre != membre:
                    raise serializers.ValidationError({
                        'membre_numero': "Cette souscription n'appartient pas à ce membre."
                    })
            except Membre.DoesNotExist:
                raise serializers.ValidationError({
                    'membre_numero': "Aucun membre avec ce numéro de compte."
                })
        elif client_numero:
            try:
                client = Client.objects.get(numero_compte=client_numero)
                if compte.titulaire_client != client:
                    raise serializers.ValidationError({
                        'client_numero': "Cette souscription n'appartient pas à ce client."
                    })
            except Client.DoesNotExist:
                raise serializers.ValidationError({
                    'client_numero': "Aucun client avec ce numéro de compte."
                })
        else:
            # Si aucun numéro n'est fourni, vérifier que le compte a un titulaire
            if not compte.titulaire_membre and not compte.titulaire_client:
                raise serializers.ValidationError({
                    'non_field_errors': "Vous devez fournir soit 'membre_numero' soit 'client_numero' pour vérifier la propriété de la souscription."
                })
        
        # Vérifier le type de compte et les règles spécifiques
        type_compte = compte.type_compte
        
        if type_compte == 'BLOQUE':
            # Pour les comptes bloqués, le mot d'engagement est obligatoire
            if not mot_engagement or not mot_engagement.strip():
                raise serializers.ValidationError({
                    'mot_engagement': "Le mot d'engagement est obligatoire pour retirer sur un compte bloqué."
                })
            
            # Vérifier que le mot d'engagement est exact (sensible à la casse)
            if mot_engagement.strip() != self.MOT_ENGAGEMENT_BLOQUE:
                raise serializers.ValidationError({
                    'mot_engagement': f"Le mot d'engagement est incorrect. Vous devez écrire exactement: \"{self.MOT_ENGAGEMENT_BLOQUE}\" (sensible à la casse, espaces inclus)."
                })
        
        # Calculer le solde actuel
        solde_actuel = souscript_epargne.solde_epargne
        montant_decimal = Decimal(str(montant))
        
        # Vérifier que le solde après retrait ne soit pas <= 0
        solde_apres_retrait = solde_actuel - montant_decimal
        
        if solde_apres_retrait < Decimal('0.00'):
            raise serializers.ValidationError({
                'montant': f"Solde insuffisant. Solde actuel: {solde_actuel:.2f}, montant du retrait: {montant_decimal:.2f}. "
                          f"Le solde après retrait serait: {solde_apres_retrait:.2f} (négatif, non autorisé)."
            })
        
        if solde_apres_retrait == Decimal('0.00'):
            raise serializers.ValidationError({
                'montant': f"Le retrait de {montant_decimal:.2f} ferait passer le solde à 0. Le solde ne peut pas être égal à 0 après un retrait. "
                          f"Solde actuel: {solde_actuel:.2f}."
            })
        
        # Validation par type de caisse : vérifier que le type de caisse a assez de fonds
        caissetype = attrs.get('caissetype_id')
        if caissetype:
            from caisse.services import calculer_solde_caissetype_disponible
            from caisse.models import CaisseType
            
            # Vérifier que le type de caisse existe
            if not CaisseType.objects.filter(pk=caissetype.pk).exists():
                raise serializers.ValidationError({
                    "caissetype_id": f"Aucun type de caisse trouvé avec l'ID {caissetype.pk}."
                })
            
            # Calculer le solde disponible pour ce type de caisse spécifique
            solde_data = calculer_solde_caissetype_disponible(caissetype)
            solde_disponible = solde_data['solde_disponible']
            seuil_minimum = Decimal('1.00')  # Seuil minimum de 1$ par type de caisse
            
            # Vérifier que le montant du retrait n'est pas supérieur ou égal au solde disponible
            if montant_decimal >= solde_disponible:
                raise serializers.ValidationError({
                    "montant": f"Impossible d'effectuer ce retrait de {montant} sur {caissetype.nom}. Le montant demandé ({montant}) est supérieur ou égal au solde disponible ({solde_disponible}) dans ce type de caisse. Solde disponible sur {caissetype.nom} : {solde_disponible}."
                })
            
            # Vérifier qu'il reste au moins 1$ dans ce type de caisse après le retrait
            solde_apres_retrait_caisse = solde_disponible - montant_decimal
            if solde_apres_retrait_caisse < seuil_minimum:
                raise serializers.ValidationError({
                    "montant": f"Impossible d'effectuer ce retrait de {montant} sur {caissetype.nom}. Après le retrait, il ne resterait que {solde_apres_retrait_caisse} dans {caissetype.nom}, ce qui est inférieur au seuil minimum de {seuil_minimum}. Le solde disponible actuel sur {caissetype.nom} est de {solde_disponible}."
                })
            
            # Stocker caissetype pour la création du Caissetypemvt
            attrs['_caissetype'] = caissetype
            attrs.pop('caissetype_id', None)
        else:
            raise serializers.ValidationError({
                "caissetype_id": "Le type de caisse est obligatoire. Veuillez spécifier caissetype_id."
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Crée le retrait et le Caissetypemvt associé automatiquement
        """
        # Extraire caissetype de validated_data
        caissetype = validated_data.pop('_caissetype', None)
        
        # Créer le retrait
        retrait = super().create(validated_data)
        
        # Créer automatiquement le Caissetypemvt pour lier le retrait au type de caisse
        if caissetype:
            from caisse.models import Caissetypemvt
            from django.utils import timezone
            Caissetypemvt.objects.create(
                caissetype=caissetype,
                retrait=retrait,
                date=retrait.date_operation.date() if hasattr(retrait.date_operation, 'date') else timezone.now().date()
            )
        
        return retrait


