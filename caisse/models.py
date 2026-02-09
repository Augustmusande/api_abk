from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

def get_default_date():
    """Retourne la date du jour (sans heure)"""
    return timezone.now().date()

class CaisseType(models.Model):
    """
    Modèle pour définir les types de caisse (Airtel Money, Orange Money, Banque, etc.)
    Permet de catégoriser les OPERATIONS par type de caisse.
    """
    nom = models.CharField(max_length=100, unique=True, help_text="Nom du type de caisse (ex: Airtel Money, Orange Money, Banque)")
    description = models.TextField(blank=True, null=True, help_text="Description du type de caisse")
    image = models.ImageField(upload_to='caissetypes/logos/', blank=True, null=True, help_text="Logo/Image du type de caisse (formats acceptés: JPG, PNG, SVG)")
    last_updated = models.DateTimeField(auto_now=True, help_text="Date de dernière mise à jour")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date de création")
    
    class Meta:
        verbose_name = "Type de caisse"
        verbose_name_plural = "Types de caisse"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom

class Caissetypemvt(models.Model):
    """
    Modèle pour lier un type de caisse à une donnation/remboursement/dépense/retrait/crédit.
    Permet de suivre dans quelle caisse (Airtel Money, Orange Money, Banque, etc.) 
    chaque mouvement d'argent a été effectué.
    """
    caissetype = models.ForeignKey(CaisseType, on_delete=models.PROTECT, help_text="Type de caisse (obligatoire)", null=False, blank=False, related_name='mouvements')
    remboursement = models.ForeignKey('credits.Remboursement', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Remboursement lié (optionnel)")
    credit = models.ForeignKey('credits.Credit', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Crédit lié (optionnel)")
    donnatepargne = models.ForeignKey('membres.DonnatEpargne', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Don d'épargne lié (optionnel)")
    donnatpartsocial = models.ForeignKey('membres.DonnatPartSocial', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Don de part sociale lié (optionnel)")
    fraisadhesion = models.ForeignKey('membres.FraisAdhesion', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Frais d'adhésion lié (optionnel)")
    depense = models.ForeignKey('Depenses', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Dépense liée (optionnel)")
    retrait = models.ForeignKey('membres.Retrait', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Retrait lié (optionnel)")
    dondirect = models.ForeignKey('DonDirect', on_delete=models.CASCADE, null=True, blank=True, related_name='caissetype_mouvements', help_text="Don direct lié (optionnel)")
    date = models.DateField(default=get_default_date, help_text="Date du mouvement (automatique)", auto_now_add=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mouvement de type de caisse"
        verbose_name_plural = "Mouvements de type de caisse"
        ordering = ['-date', '-created_at']
    
    def clean(self):
        """Valide qu'au moins une des 8 relations est remplie"""
        from django.core.exceptions import ValidationError
        relations = [self.remboursement, self.credit, self.donnatepargne, self.donnatpartsocial, self.fraisadhesion, self.depense, self.retrait, self.dondirect]
        if not any(relations):
            raise ValidationError("Au moins une relation (remboursement, credit, donnatepargne, donnatpartsocial, fraisadhesion, depense, retrait ou dondirect) doit être spécifiée.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        mouvement = self.remboursement or self.credit or self.donnatepargne or self.donnatpartsocial or self.fraisadhesion or self.depense or self.retrait or self.dondirect
        return f"{self.caissetype} - {mouvement} - {self.date}"

class DonDirect(models.Model):
    """
    Modèle pour gérer les dons directs de personnes qui ne sont ni membres ni clients.
    Ce sont des entrées directes en caisse (pas liées à des parts sociales, épargnes ou remboursements).
    """
    montant = models.DecimalField(max_digits=15, decimal_places=2, help_text="Montant du don")
    date_don = models.DateField(default=get_default_date, help_text="Date du don")
    libelle = models.CharField(max_length=200, blank=True, null=True, help_text="Description/libellé du don (optionnel)")
    donateur_nom = models.CharField(max_length=200, blank=True, null=True, help_text="Nom du donateur (optionnel)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Don direct"
        verbose_name_plural = "Dons directs"
        ordering = ['-date_don', '-created_at']

    def __str__(self):
        donateur = self.donateur_nom or "Anonyme"
        libelle = f" - {self.libelle}" if self.libelle else ""
        return f"Don direct de {donateur}{libelle} - {self.montant} - {self.date_don}"

class Depenses(models.Model):
    """
    Modèle pour gérer les dépenses de la coopérative.
    Les dépenses sont financées par les frais de gestion.
    """
    libelle = models.CharField(max_length=200, help_text="Libellé de la dépense")
    uniter = models.CharField(max_length=50, help_text="Unité de mesure (ex: kg, litre, pièce, etc.)")
    quantite = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantité")
    pu = models.DecimalField(max_digits=15, decimal_places=2, help_text="Prix unitaire")
    date_depense = models.DateField(default=timezone.now, help_text="Date de la dépense")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-date_depense', '-created_at']

    @property
    def pt(self):
        """
        Calcule dynamiquement le prix total.
        pt = quantite × pu
        Cette valeur n'est pas stockée dans la base de données.
        """
        if self.quantite and self.pu:
            return Decimal(str(self.quantite)) * Decimal(str(self.pu))
        return Decimal('0.00')

    def __str__(self):
        return f"{self.libelle} - {self.quantite} {self.uniter} - {self.pt} "
