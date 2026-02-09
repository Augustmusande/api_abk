from rest_framework import serializers
from decimal import Decimal
from .models import  Credit, Remboursement
from caisse.models import CaisseType

# --- Serializers pour Credit et Remboursement ---
class CreditSerializer(serializers.ModelSerializer):
    jours_restants = serializers.ReadOnlyField()
    solde_restant = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    interet = serializers.ReadOnlyField(help_text="Intérêt calculé : (montant * taux_interet) / 100 (même formule pour les deux méthodes)")
    interet_retenu = serializers.SerializerMethodField(help_text="Intérêt retenu (alias de interet, pour clarté dans le formulaire)")
    montant_effectif = serializers.ReadOnlyField(help_text="Montant effectivement versé : montant (si POSTCOMPTE) ou montant - interet (si PRECOMPTE)")
    date_octroi = serializers.DateField(read_only=True, help_text="Date d'octroi (automatique, non modifiable)")
    statut = serializers.CharField(read_only=True, help_text="Statut du crédit (automatique, non modifiable)")
    from users.models import Membre, Client
    
    # Champs pour la lecture (GET) - retournent les IDs
    membre = serializers.IntegerField(source='membre_id', read_only=True, allow_null=True, help_text="ID du membre (nombre ou null)")
    client = serializers.IntegerField(source='client_id', read_only=True, allow_null=True, help_text="ID du client (nombre ou null)")
    numero_compte = serializers.SerializerMethodField(help_text="Numéro de compte du membre ou client")
    caissetype = serializers.SerializerMethodField(help_text="Type de caisse associé au crédit")
    
    # Champs pour l'écriture (POST/PUT) - utilisés lors de la création/modification
    membre_id = serializers.PrimaryKeyRelatedField(
        queryset=Membre.objects.all(), 
        required=False, 
        allow_null=True,
        write_only=True,
        source='membre'
    )
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), 
        required=False, 
        allow_null=True,
        write_only=True,
        source='client'
    )
    caissetype_id = serializers.PrimaryKeyRelatedField(
        queryset=CaisseType.objects.all(),
        required=True,
        write_only=True,
        help_text="ID du type de caisse (obligatoire)",
        allow_null=False
    )

    class Meta:
        model = Credit
        fields = [
            'id', 'membre', 'client', 'numero_compte', 'caissetype',
            'jours_restants', 'solde_restant', 'interet', 'interet_retenu', 'montant_effectif',
            'montant', 'taux_interet', 'duree', 'duree_type', 'methode_interet',
            'date_octroi', 'date_fin', 'statut', 'score', 'date_remboursement_final',
            'membre_id', 'client_id', 'caissetype_id'  # Pour l'écriture
        ]
        extra_kwargs = {
            'membre': {'required': False, 'allow_null': True},
            'client': {'required': False, 'allow_null': True},
        }

    def get_numero_compte(self, obj):
        """Retourne le numéro de compte du membre ou du client"""
        if obj.membre:
            return obj.membre.numero_compte
        elif obj.client:
            return obj.client.numero_compte
        return None
    
    def get_caissetype(self, obj):
        """Retourne le type de caisse associé au crédit"""
        from caisse.models import Caissetypemvt
        caissetypemvt = Caissetypemvt.objects.filter(credit=obj).first()
        if caissetypemvt:
            return {
                'id': caissetypemvt.caissetype.id,
                'nom': caissetypemvt.caissetype.nom
            }
        return None
    
    def get_interet_retenu(self, obj):
        """Retourne l'intérêt retenu (alias de interet pour clarté dans le formulaire)"""
        return float(obj.interet)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import Membre, Client
        from caisse.models import CaisseType
        # Mettre à jour les querysets pour les champs d'écriture
        if 'membre_id' in self.fields:
            self.fields['membre_id'].queryset = Membre.objects.all()
        if 'client_id' in self.fields:
            self.fields['client_id'].queryset = Client.objects.all()
        if 'caissetype_id' in self.fields:
            self.fields['caissetype_id'].queryset = CaisseType.objects.all()

    def validate(self, attrs):
        # Utiliser membre_id et client_id pour la validation (champs d'écriture)
        membre = attrs.get('membre', None)  # source='membre' donc c'est l'objet Membre
        client = attrs.get('client', None)   # source='client' donc c'est l'objet Client
        caissetype = attrs.get('caissetype_id', None)  # caissetype_id est le champ d'écriture
        from users.models import Membre, Client
        from caisse.models import CaisseType
        
        # Validation du type de caisse (obligatoire)
        if not caissetype:
            raise serializers.ValidationError({
                "caissetype_id": "Le type de caisse est obligatoire. Veuillez spécifier caissetype_id."
            })
        
        # Vérifier que le type de caisse existe
        if not CaisseType.objects.filter(pk=caissetype.pk).exists():
            raise serializers.ValidationError({
                "caissetype_id": f"Aucun type de caisse trouvé avec l'ID {caissetype.pk}."
            })
        
        # Stocker caissetype pour la création du Caissetypemvt
        attrs['_caissetype'] = caissetype
        # Retirer caissetype_id de validated_data car ce n'est pas un champ du modèle Credit
        attrs.pop('caissetype_id', None)
        
        # Nettoyer les valeurs None explicites
        if membre is None:
            attrs.pop('membre', None)
        if client is None:
            attrs.pop('client', None)
        
        if membre:
            if not Membre.objects.filter(pk=membre.pk).exists():
                raise serializers.ValidationError({"membre_id": "Aucun membre trouvé avec cet id."})
            attrs['client'] = None
        elif client:
            if not Client.objects.filter(pk=client.pk).exists():
                raise serializers.ValidationError({"client_id": "Aucun client trouvé avec cet id."})
            attrs['membre'] = None
        else:
            raise serializers.ValidationError({
                "membre_id": "Le membre ou client doit être précisé (via membre_id ou client_id).",
                "client_id": "Le membre ou client doit être précisé (via membre_id ou client_id)."
            })
        
        # Vérifier qu'on n'a pas les deux en même temps
        if attrs.get('membre') and attrs.get('client'):
            raise serializers.ValidationError({
                "membre_id": "Vous ne pouvez pas fournir membre_id et client_id en même temps.",
                "client_id": "Vous ne pouvez pas fournir membre_id et client_id en même temps."
            })
        
        # S'assurer que date_octroi n'est pas fourni (sera rempli automatiquement)
        attrs.pop('date_octroi', None)
        # S'assurer que statut n'est pas fourni (sera géré automatiquement)
        attrs.pop('statut', None)
        
        # Validation : Vérifier que le montant du crédit ne dépasse pas les fonds disponibles
        # IMPORTANT : La validation se fait PAR TYPE DE CAISSE, pas sur le total global.
        # Chaque type de caisse doit avoir un solde suffisant pour octroyer le crédit.
        montant = attrs.get('montant')
        caissetype = attrs.get('_caissetype')  # Récupérer le type de caisse stocké précédemment
        
        if montant and caissetype:
            from caisse.services import calculer_solde_caissetype_disponible
            
            # Calculer le solde disponible pour ce type de caisse spécifique
            solde_data = calculer_solde_caissetype_disponible(caissetype)
            solde_disponible = solde_data['solde_disponible']
            
            montant_decimal = Decimal(str(montant))
            seuil_minimum = Decimal('1.00')  # Seuil minimum de 1$ par type de caisse
            
            # Vérifier que le montant du crédit n'est pas supérieur ou égal au solde disponible
            if montant_decimal >= solde_disponible:
                raise serializers.ValidationError({
                    "montant": f"Impossible d'octroyer ce crédit de {montant} sur {caissetype.nom}. Le montant demandé ({montant}) est supérieur ou égal au solde disponible ({solde_disponible}) dans ce type de caisse. Solde disponible sur {caissetype.nom} : {solde_disponible}."
                })
            
            # Vérifier qu'il reste au moins 1$ dans ce type de caisse après l'octroi du crédit
            solde_apres_credit = solde_disponible - montant_decimal
            if solde_apres_credit < seuil_minimum:
                raise serializers.ValidationError({
                    "montant": f"Impossible d'octroyer ce crédit de {montant} sur {caissetype.nom}. Après l'octroi, il ne resterait que {solde_apres_credit} dans {caissetype.nom}, ce qui est inférieur au seuil minimum de {seuil_minimum}. Le solde disponible actuel sur {caissetype.nom} est de {solde_disponible}."
                })
        
        return attrs
    
    def create(self, validated_data):
        """
        Crée le crédit et le Caissetypemvt associé automatiquement
        """
        # Extraire caissetype de validated_data
        caissetype = validated_data.pop('_caissetype', None)
        
        # Créer le crédit
        credit = super().create(validated_data)
        
        # Créer automatiquement le Caissetypemvt pour lier le crédit au type de caisse
        if caissetype:
            from caisse.models import Caissetypemvt
            
            # Créer le Caissetypemvt pour le crédit
            # TODO: Ajouter les champs nécessaires (type, montant, motif) à Caissetypemvt
            caissetypemvt = Caissetypemvt.objects.create(
                caissetype=caissetype,
                credit=credit,
                date=credit.date_octroi
            )
        
        return credit
    
    def to_representation(self, instance):
        """
        Convertit les champs datetime en date pour l'affichage.
        """
        from datetime import date, datetime
        
        representation = super().to_representation(instance)
        
        # Retirer les champs d'écriture (membre_id, client_id, caissetype_id) de la représentation
        representation.pop('membre_id', None)
        representation.pop('client_id', None)
        representation.pop('caissetype_id', None)
        
        # Convertir date_octroi de datetime à date si nécessaire
        if 'date_octroi' in representation and instance.date_octroi:
            date_octroi = instance.date_octroi
            if isinstance(date_octroi, datetime):
                # C'est un datetime, convertir en date
                representation['date_octroi'] = date_octroi.date().isoformat()
            elif isinstance(date_octroi, date):
                # C'est déjà une date
                representation['date_octroi'] = date_octroi.isoformat()
            elif isinstance(date_octroi, str):
                # Déjà une string, garder tel quel
                representation['date_octroi'] = date_octroi
            else:
                # Fallback
                representation['date_octroi'] = str(date_octroi)
        
        # Convertir date_fin de datetime à date si nécessaire
        if 'date_fin' in representation and instance.date_fin:
            date_fin = instance.date_fin
            if isinstance(date_fin, datetime):
                # C'est un datetime, convertir en date
                representation['date_fin'] = date_fin.date().isoformat()
            elif isinstance(date_fin, date):
                # C'est déjà une date
                representation['date_fin'] = date_fin.isoformat()
            elif isinstance(date_fin, str):
                # Déjà une string, garder tel quel
                representation['date_fin'] = date_fin
            else:
                # Fallback
                representation['date_fin'] = str(date_fin)
        
        return representation

class RemboursementSerializer(serializers.ModelSerializer):

    credit = CreditSerializer(read_only=True)
    credit_id = serializers.PrimaryKeyRelatedField(
        queryset=Credit.objects.all(),  # Permettre tous les crédits, la validation se fera dans validate()
        write_only=True, 
        source='credit', 
        required=True,
        help_text="ID du crédit"
    )
    echeance = serializers.DateField(read_only=True, help_text="Date d'échéance (automatique, non modifiable)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permettre tous les crédits, la validation se fera dans validate()
        self.fields['credit_id'].queryset = Credit.objects.all()

    def validate(self, attrs):
        credit = attrs.get('credit', None)
        montant = attrs.get('montant', None)
        
        if not credit:
            raise serializers.ValidationError({"credit": "Le crédit doit être précisé (via credit_id)."})
        
        # Vérifier si le crédit peut encore être remboursé
        # Pour PRECOMPTE : vérifier si le montant total remboursé est inférieur au montant du crédit
        # Pour POSTCOMPTE : vérifier si le solde_restant est supérieur à 0
        if credit.methode_interet == 'PRECOMPTE':
            montant_total_rembourse = sum([r.montant for r in credit.remboursements.all()])
            if montant_total_rembourse >= credit.montant:
                raise serializers.ValidationError({
                    "credit": f"Ce crédit PRECOMPTE est déjà entièrement remboursé. Montant total du crédit: {credit.montant}, montant déjà remboursé: {montant_total_rembourse}."
                })
        else:  # POSTCOMPTE
            if credit.solde_restant <= 0:
                raise serializers.ValidationError({
                    "credit": f"Ce crédit POSTCOMPTE est déjà entièrement remboursé. Solde restant: {credit.solde_restant}."
                })
        
        # Vérifier que le crédit n'est pas annulé ou rejeté
        if credit.statut in ['ANNULE', 'REJETE']:
            raise serializers.ValidationError({
                "credit": f"Ce crédit a le statut '{credit.statut}'. Impossible de créer un remboursement pour ce crédit."
            })
        
        # Vérifier que le montant du remboursement ne dépasse pas le montant à rembourser
        # Pour PRECOMPTE : on rembourse le montant total du crédit (pas le montant net)
        # Pour POSTCOMPTE : on rembourse le montant + intérêt
        if montant:
            if credit.methode_interet == 'PRECOMPTE':
                # Pour PRECOMPTE, on peut rembourser jusqu'au montant total du crédit
                montant_max_remboursable = credit.montant
                # Calculer le montant total déjà remboursé (somme de tous les remboursements précédents)
                montant_total_rembourse = sum([r.montant for r in credit.remboursements.all()])
                montant_total_apres_remboursement = montant_total_rembourse + montant
                
                if montant_total_apres_remboursement > montant_max_remboursable:
                    montant_restant_remboursable = montant_max_remboursable - montant_total_rembourse
                    raise serializers.ValidationError({
                        "montant": f"Le montant du remboursement ({montant}) est trop élevé. Pour un crédit PRECOMPTE, le montant total à rembourser est {montant_max_remboursable} (montant du crédit). Montant déjà remboursé : {montant_total_rembourse}, montant restant remboursable : {montant_restant_remboursable}. Vous pouvez rembourser au maximum {montant_restant_remboursable}."
                    })
            else:
                # Pour POSTCOMPTE, on rembourse le montant + intérêt (solde_restant)
                if montant > credit.solde_restant:
                    raise serializers.ValidationError({
                        "montant": f"Le montant du remboursement ({montant}) ne peut pas dépasser le solde restant ({credit.solde_restant})."
                    })
        
        # S'assurer que echeance n'est pas fourni (sera rempli automatiquement)
        attrs.pop('echeance', None)
        
        return attrs

    class Meta:
        model = Remboursement
        fields = '__all__'
        extra_kwargs = {
            'echeance': {'read_only': True},
        }
from users.serializers import MembreSerializer, ClientSerializer

