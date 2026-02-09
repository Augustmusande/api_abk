# --- Modèle FraisAdhesion ---
from users.models import Membre


from datetime import date
from django.db import models
from django.utils import timezone
from decimal import Decimal
from users import *
from users.models import *


def get_default_date():
    """Retourne la date du jour (sans heure)"""
    return timezone.now().date()
class Compte(models.Model):
    TYPE_CHOIX = [
        ('VUE', 'Compte en vue'),
        ('BLOQUE', 'Compte bloqué'),
    ]


    titulaire_membre = models.ForeignKey(Membre, on_delete=models.SET_NULL, null=True, blank=True)
    titulaire_client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    type_compte = models.CharField(max_length=10, choices=TYPE_CHOIX)
    
    class Meta:
        verbose_name = "Compte"
        verbose_name_plural = "Comptes"
        ordering = ['-id']  # Trier par ID décroissant pour la pagination

class FraisAdhesion(models.Model):
    titulaire_membre = models.ForeignKey(Membre, on_delete=models.CASCADE, null=True, blank=True)
    titulaire_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    from datetime import date
    date_paiement = models.DateField(default=date.today)

    class Meta:
        ordering = ['-date_paiement', '-id']
        verbose_name = "Frais d'adhésion"
        verbose_name_plural = "Frais d'adhésion"

    def __str__(self):
        if self.titulaire_membre:
            return f"FraisAdhesion({self.titulaire_membre}, {self.montant}, {self.date_paiement})"
        elif self.titulaire_client:
            return f"FraisAdhesion({self.titulaire_client}, {self.montant}, {self.date_paiement})"
        return f"FraisAdhesion({self.montant}, {self.date_paiement})"

# Create your models here.
class SouscriptEpargne(models.Model):
    designation = models.CharField(max_length=100)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE)
    date_souscription = models.DateField(default=get_default_date, help_text="Date de souscription (automatique)")
    montant_souscrit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Montant cible (optionnel, null = épargne illimitée)")
    
    @property
    def total_donne(self):
        """
        Calcule le montant total déjà donné sur cette souscription.
        
        Returns:
            Decimal: Montant total des donations
        """
        return sum([d.montant for d in self.donnatepargne_set.all()])
    
    @property
    def total_retire(self):
        """
        Calcule le montant total retiré sur cette souscription.
        
        Returns:
            Decimal: Montant total des retraits
        """
        return sum([r.montant for r in self.retrait_set.all()])
    
    @property
    def solde_epargne(self):
        """
        Calcule le solde actuel de l'épargne (dons - retraits).
        
        Returns:
            Decimal: Solde actuel (total_donne - total_retire)
        """
        return self.total_donne - self.total_retire
    
    @property
    def montant_restant(self):
        """
        Calcule le montant restant à verser pour atteindre le montant souscrit.
        Si montant_souscrit est None (épargne illimitée), retourne None.
        
        Returns:
            Decimal ou None: Montant restant (montant_souscrit - total_donne) ou None si illimité
        """
        if self.montant_souscrit is None:
            # Épargne illimitée
            return None
        return max(Decimal('0.00'), self.montant_souscrit - self.total_donne)

class DonnatEpargne(models.Model):
    MOIS = [
        ('JANVIER', 'Janvier'),
        ('FEVRIER', 'Février'),
        ('MARS', 'Mars'),
        ('AVRIL', 'Avril'),
        ('MAI', 'Mai'),
        ('JUIN', 'Juin'),
        ('JUILLET', 'Juillet'),
        ('AOUT', 'Août'),
        ('SEPTEMBRE', 'Septembre'),
        ('OCTOBRE', 'Octobre'),
        ('NOVEMBRE', 'Novembre'),
        ('DECEMBRE', 'Décembre'),
    ]
    souscriptEpargne = models.ForeignKey(SouscriptEpargne, on_delete=models.CASCADE)
    mois = models.CharField(max_length=100,choices=MOIS)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['-id']
        verbose_name = "Don d'épargne"
        verbose_name_plural = "Dons d'épargne"

class Retrait(models.Model):
    """
    Modèle pour gérer les retraits d'argent sur les souscriptions d'épargne.
    Seules les épargnes peuvent être retirées.
    - Comptes VUE: retrait possible à tout moment
    - Comptes BLOQUE: retrait possible uniquement avec confirmation par mot d'engagement
    """
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    date_operation = models.DateTimeField(default=timezone.now)
    souscriptEpargne = models.ForeignKey(SouscriptEpargne, on_delete=models.SET_NULL, null=True, blank=True, related_name='retrait_set')
    motif = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = "Retrait"
        verbose_name_plural = "Retraits"
        ordering = ['-date_operation']
    
    def __str__(self):
        return f"Retrait({self.souscriptEpargne}, {self.montant}, {self.date_operation.date()})"

class PartSocial(models.Model):
    annee = models.PositiveIntegerField()
    montant_souscrit = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"PartSocial {self.annee} - {self.montant_souscrit} FCFA"

class SouscriptionPartSocial(models.Model):
    """
    Table intermédiaire entre PartSocial et DonnatPartSocial.
    Lie un membre à une part sociale et spécifie le nombre de versements prévus.
    """
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE)
    partSocial = models.ForeignKey(PartSocial, on_delete=models.CASCADE)
    nombre_versements_prevu = models.PositiveIntegerField(help_text="Nombre de fois que le membre va payer cette part sociale")
    date_souscription = models.DateField(default=date.today)
    
    class Meta:
        unique_together = ['membre', 'partSocial']  # Un membre ne peut souscrire qu'une fois à une part sociale
    
    def __str__(self):
        return f"{self.membre} - PartSocial {self.partSocial.annee} ({self.nombre_versements_prevu} versements)"
    
    @property
    def nombre_versements_effectues(self):
        """Retourne le nombre de versements déjà effectués"""
        return self.donnatpartsocial_set.count()
    
    @property
    def montant_total_verse(self):
        """Retourne le montant total déjà versé"""
        return sum([d.montant for d in self.donnatpartsocial_set.all()])
    
    @property
    def montant_cible(self):
        """Retourne le montant cible à atteindre (montant_souscrit * nombre_versements_prevu)"""
        return self.partSocial.montant_souscrit * self.nombre_versements_prevu
    
    @property
    def est_complete(self):
        """
        Vérifie si la souscription est complète.
        est_complete = true si le montant_total_verse >= montant_cible (montant_souscrit * nombre_versements_prevu)
        Peu importe le nombre de versements effectués.
        """
        return self.montant_total_verse >= self.montant_cible
    
    @property
    def montant_restant(self):
        """Retourne le montant restant à verser pour atteindre le montant cible"""
        return max(0, self.montant_cible - self.montant_total_verse)

class DonnatPartSocial(models.Model):
    MOIS = [
        ('JANVIER', 'Janvier'),
        ('FEVRIER', 'Février'),
        ('MARS', 'Mars'),
        ('AVRIL', 'Avril'),
        ('MAI', 'Mai'),
        ('JUIN', 'Juin'),
        ('JUILLET', 'Juillet'),
        ('AOUT', 'Août'),
        ('SEPTEMBRE', 'Septembre'),
        ('OCTOBRE', 'Octobre'),
        ('NOVEMBRE', 'Novembre'),
        ('DECEMBRE', 'Décembre'),
    ]
        
    souscription_part_social = models.ForeignKey(SouscriptionPartSocial, on_delete=models.CASCADE, related_name='donnatpartsocial_set', null=True, blank=True)
    date_donnat = models.DateField(default=date.today)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    mois = models.CharField(max_length=100, choices=MOIS)
    
    def save(self, *args, **kwargs):
        # Validation avant sauvegarde
        if self.pk is None and self.souscription_part_social:  # Nouvelle création avec souscription
            souscription = self.souscription_part_social
            montant_cible = souscription.montant_cible
            
            # Vérifier le montant total (le montant cible = montant_souscrit * nombre_versements_prevu)
            montant_total_actuel = souscription.montant_total_verse
            montant_apres = montant_total_actuel + self.montant
            
            # Si le montant cible est déjà atteint, on ne peut plus ajouter de versements
            if montant_total_actuel >= montant_cible:
                raise ValueError(
                    f"Le montant cible ({montant_cible} FCFA) a déjà été atteint. La souscription est complète."
                )
            
            # Vérifier que le montant après ne dépasse pas le montant cible
            if montant_apres > montant_cible:
                raise ValueError(
                    f"Le montant total des versements ({montant_apres} FCFA) dépasse le montant cible "
                    f"({montant_cible} FCFA = {souscription.partSocial.montant_souscrit} FCFA × {souscription.nombre_versements_prevu}). "
                    f"Montant restant: {souscription.montant_restant} FCFA"
                )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.souscription_part_social:
            return f"DonnatPartSocial({self.souscription_part_social.membre}, {self.montant}, {self.mois})"
        return f"DonnatPartSocial({self.montant}, {self.mois})"





