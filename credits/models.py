from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone
from users import *
from users.models import *


def get_default_date():
    """Retourne la date du jour (sans heure)"""
    return timezone.now().date()



from django.core.mail import send_mail
from users.email_config import get_smtp_backend, get_default_from_email
from users.models import Cooperative

class Credit(models.Model):
    DUREE_TYPE_CHOICES = [
        ('JOURS', 'Jours'),
        ('SEMAINES', 'Semaines'),
        ('MOIS', 'Mois'),
    ]
    METHODE_INTERET_CHOICES = [
        ('PRECOMPTE', 'Intérêt précompté (coupé à la source)'),
        ('POSTCOMPTE', 'Intérêt postcompté (à l\'échéance)'),
    ]
    membre = models.ForeignKey(Membre, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    montant = models.DecimalField(max_digits=15, decimal_places=2, help_text="Montant demandé du crédit")
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, help_text="Taux d'intérêt (en pourcentage, ex: 5.00 = 5%)")
    duree = models.PositiveIntegerField(help_text="Durée du crédit (en fonction du type)")
    duree_type = models.CharField(max_length=10, choices=DUREE_TYPE_CHOICES, default='MOIS')
    methode_interet = models.CharField(
        max_length=12, 
        choices=METHODE_INTERET_CHOICES, 
        default='PRECOMPTE',
        help_text="Méthode de calcul de l'intérêt : PRECOMPTE (intérêt déduit à la source, méthode par défaut) ou POSTCOMPTE (intérêt non déduit, compté à l'échéance)"
    )
    date_octroi = models.DateField(default=get_default_date)
    date_fin = models.DateField(blank=True, null=True)
    solde_restant = models.DecimalField(max_digits=15, decimal_places=2, help_text="Solde restant à rembourser")
    statut = models.CharField(max_length=20, default='EN_COURS')
    score = models.DecimalField(max_digits=3, decimal_places=1, default=10.0, help_text="Score du crédit sur 10 (10 = excellent, 0 = très mauvais)")
    date_remboursement_final = models.DateField(blank=True, null=True, help_text="Date de remboursement complet du crédit (pour calcul du score)")

    def save(self, *args, **kwargs):
        # Calcul automatique de la date de fin
        if not self.date_fin:
            base_date = self.date_octroi
            if hasattr(base_date, 'date') and not isinstance(base_date, date):
                base_date = base_date.date()
            if self.duree_type == 'JOURS':
                self.date_fin = base_date + timedelta(days=self.duree)
            elif self.duree_type == 'SEMAINES':
                self.date_fin = base_date + timedelta(weeks=self.duree)
            else:
                # Approximation: 1 mois = 30 jours
                self.date_fin = base_date + timedelta(days=30*self.duree)
            # S'assurer que date_fin est bien un objet date
            if hasattr(self.date_fin, 'date') and not isinstance(self.date_fin, date):
                self.date_fin = self.date_fin.date()
        # Initialisation du solde restant à la création
        # IMPORTANT : 
        # - Si méthode PRECOMPTE (par défaut) : solde_restant = montant (montant total du crédit)
        #   L'intérêt est retenu à la source lors du versement, mais on rembourse le montant total du crédit
        #   Exemple : Crédit 10 USD, intérêt 5% (0.50) → On verse 9.50, on rembourse 10.00
        # - Si méthode POSTCOMPTE : solde_restant = montant + interet (l'intérêt est compté à l'échéance et doit être remboursé)
        if not self.pk:
            if self.methode_interet == 'POSTCOMPTE':
                # Pour POSTCOMPTE, l'intérêt doit être ajouté au montant à rembourser
                from decimal import Decimal
                interet_calcule = (self.montant * self.taux_interet) / Decimal('100')
                self.solde_restant = self.montant + interet_calcule
            else:
                # Pour PRECOMPTE, on rembourse le montant total du crédit (pas le montant net)
                # L'intérêt a été retenu à la source lors du versement, mais le remboursement se fait sur le montant total
                self.solde_restant = self.montant
        # Statut automatique
        if self.solde_restant <= 0:
            self.statut = 'TERMINE'
        else:
            # Vérifier si la date de fin est dépassée
            date_fin = self.date_fin
            if isinstance(date_fin, datetime):
                date_fin = date_fin.date()
            if timezone.now().date() > date_fin:
                self.statut = 'ECHEANCE_DEPASSEE'
            else:
                self.statut = 'EN_COURS'
        super().save(*args, **kwargs)
        # Envoi d'email à la création
        if kwargs.get('send_mail_on_create', True) and not self.pk:
            coop = Cooperative.objects.first()
            
            # Déterminer le destinataire (membre ou client)
            destinataire = None
            nom_destinataire = None
            if self.membre:
                destinataire = self.membre
                nom_destinataire = f"{self.membre.nom} {self.membre.prenom}"
            elif self.client:
                destinataire = self.client
                nom_destinataire = f"{self.client.nom} {self.client.prenom}"
            
            # Envoyer l'email seulement si on a un destinataire avec un email
            if destinataire and hasattr(destinataire, 'email') and destinataire.email:
                backend = get_smtp_backend()
                from_email = coop.email if coop and hasattr(coop, 'email') and coop.email else get_default_from_email()
                interet_calcule = self.interet
                montant_effectif = self.montant_effectif
                methode_display = self.get_methode_interet_display()
                
                if self.methode_interet == 'PRECOMPTE':
                    message_email = (
                        f"Bonjour {nom_destinataire}, votre crédit de {self.montant} FCFA a été octroyé "
                        f"pour une durée de {self.duree} {self.get_duree_type_display()} (fin prévue le {self.date_fin}).\n\n"
                        f"Méthode : {methode_display}\n"
                        f"Intérêt précompté retenu : {interet_calcule} FCFA\n"
                        f"Montant effectivement versé : {montant_effectif} FCFA\n\n"
                        f"Le montant à rembourser est de {montant_effectif} FCFA (montant demandé - intérêt retenu à la source)."
                    )
                else:  # POSTCOMPTE
                    montant_a_rembourser = self.montant + interet_calcule
                    message_email = (
                        f"Bonjour {nom_destinataire}, votre crédit de {self.montant} FCFA a été octroyé "
                        f"pour une durée de {self.duree} {self.get_duree_type_display()} (fin prévue le {self.date_fin}).\n\n"
                        f"Méthode : {methode_display}\n"
                        f"Intérêt calculé (à l'échéance) : {interet_calcule} FCFA\n"
                        f"Montant versé : {montant_effectif} FCFA\n\n"
                        f"Le montant à rembourser est de {montant_a_rembourser} FCFA (montant + intérêt)."
                    )
                
                send_mail(
                    subject="Votre demande de crédit a été acceptée",
                    message=message_email,
                    from_email=from_email,
                    recipient_list=[destinataire.email],
                    fail_silently=True,
                    connection=backend
                )

    @property
    def interet(self):
        """
        Calcule l'intérêt du crédit.
        Formule : interet = (montant * taux_interet) / 100
        
        Cette formule est la même pour les deux méthodes (PRECOMPTE et POSTCOMPTE).
        La différence réside dans le moment où l'intérêt est prélevé :
        - PRECOMPTE : l'intérêt est déduit du montant versé (coupé à la source, méthode par défaut)
        - POSTCOMPTE : l'intérêt n'est pas déduit du montant versé (compté à l'échéance)
        
        Returns:
            Decimal: Montant des intérêts calculés
        """
        from decimal import Decimal
        return (self.montant * self.taux_interet) / Decimal('100')
    
    @property
    def montant_effectif(self):
        """
        Calcule le montant effectif versé au client/membre.
        
        - Si méthode PRECOMPTE (par défaut) : montant_effectif = montant - interet (intérêt déduit à la source)
        - Si méthode POSTCOMPTE : montant_effectif = montant (intérêt non déduit, compté à l'échéance)
        
        Returns:
            Decimal: Montant effectivement versé
        """
        if self.methode_interet == 'PRECOMPTE':
            return self.montant - self.interet
        else:  # POSTCOMPTE
            return self.montant

    @property
    def jours_restants(self):
        if self.date_fin:
            date_fin = self.date_fin
            # Si c'est un datetime, convertir en date
            if isinstance(date_fin, datetime):
                date_fin = date_fin.date()
            elif not isinstance(date_fin, date):
                raise ValueError(f"date_fin doit être un objet date ou datetime, reçu: {type(date_fin)}")
            today = timezone.now().date()
            return max((date_fin - today).days, 0)
        return None

    def check_and_notify_echeance(self):
        if self.statut == 'EN_COURS' and self.jours_restants == 0:
            coop = Cooperative.objects.first()
            
            # Déterminer le destinataire (membre ou client)
            destinataire = None
            nom_destinataire = None
            if self.membre:
                destinataire = self.membre
                nom_destinataire = f"{self.membre.nom} {self.membre.prenom}"
            elif self.client:
                destinataire = self.client
                nom_destinataire = f"{self.client.nom} {self.client.prenom}"
            
            # Envoyer l'email seulement si on a un destinataire avec un email
            if destinataire and hasattr(destinataire, 'email') and destinataire.email:
                backend = get_smtp_backend()
                from_email = coop.email if coop and hasattr(coop, 'email') and coop.email else get_default_from_email()
                send_mail(
                    subject="Échéance de crédit atteinte",
                    message=f"Bonjour {nom_destinataire}, la durée de votre crédit ({self.duree} {self.get_duree_type_display()}) est atteinte. Merci de régulariser votre situation.",
                    from_email=from_email,
                    recipient_list=[destinataire.email],
                    fail_silently=True,
                    connection=backend
                )

    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"
        ordering = ['-date_octroi', '-id']  # Trier par date d'octroi décroissante, puis par ID décroissant


class Remboursement(models.Model):
    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    echeance = models.DateField(default=get_default_date)

    def save(self, *args, **kwargs):
        # Vérifier que le montant du remboursement ne dépasse pas le montant à rembourser
        # Pour PRECOMPTE : on rembourse le montant total du crédit (pas le montant net)
        # Pour POSTCOMPTE : on rembourse le montant + intérêt
        if self.credit.methode_interet == 'PRECOMPTE':
            # Pour PRECOMPTE, on peut rembourser jusqu'au montant total du crédit
            montant_max_remboursable = self.credit.montant
            # Calculer le montant total déjà remboursé (somme de tous les remboursements précédents)
            # Exclure le remboursement actuel si c'est une mise à jour
            remboursements_existants = self.credit.remboursements.all()
            if self.pk:
                remboursements_existants = remboursements_existants.exclude(pk=self.pk)
            montant_total_rembourse = sum([r.montant for r in remboursements_existants])
            montant_total_apres_remboursement = montant_total_rembourse + self.montant
            
            if montant_total_apres_remboursement > montant_max_remboursable:
                montant_restant_remboursable = montant_max_remboursable - montant_total_rembourse
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Le montant du remboursement ({self.montant} FCFA) est trop élevé. Pour un crédit PRECOMPTE, le montant total à rembourser est {montant_max_remboursable} FCFA (montant du crédit). Montant déjà remboursé : {montant_total_rembourse} FCFA, montant restant remboursable : {montant_restant_remboursable} FCFA. Vous pouvez rembourser au maximum {montant_restant_remboursable} FCFA."
                )
        else:
            # Pour POSTCOMPTE, on rembourse le montant + intérêt (solde_restant)
            if self.montant > self.credit.solde_restant:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Le montant du remboursement ({self.montant} FCFA) ne peut pas dépasser le solde restant ({self.credit.solde_restant} FCFA)."
                )
        
        # Mettre à jour le solde restant
        # Pour PRECOMPTE : solde_restant = montant - montant_total_rembourse (après ce remboursement)
        # Pour POSTCOMPTE : solde_restant = solde_restant - montant (comme avant)
        if self.credit.methode_interet == 'PRECOMPTE':
            # Calculer le nouveau montant total remboursé après ce remboursement
            remboursements_existants = self.credit.remboursements.all()
            if self.pk:
                remboursements_existants = remboursements_existants.exclude(pk=self.pk)
            montant_total_rembourse_apres = sum([r.montant for r in remboursements_existants]) + self.montant
            self.credit.solde_restant = self.credit.montant - montant_total_rembourse_apres
        else:
            # Pour POSTCOMPTE, logique normale
            self.credit.solde_restant -= self.montant
        if self.credit.solde_restant <= 0:
            self.credit.solde_restant = 0
            self.credit.statut = 'TERMINE'
            # Calculer le score basé sur la date de remboursement
            date_remboursement = self.echeance
            self.credit.date_remboursement_final = date_remboursement
            
            # Calculer le score selon la date de remboursement
            if self.credit.date_fin:
                # Calculer la différence en jours
                diff_jours = (date_remboursement - self.credit.date_fin).days
                
                if diff_jours < 0:
                    # Paiement avant la date : 10/10
                    self.credit.score = Decimal('10.0')
                elif diff_jours == 0:
                    # Paiement à la date exacte : 8/10
                    self.credit.score = Decimal('8.0')
                elif diff_jours <= 30:
                    # Paiement 1 mois après (jusqu'à 30 jours) : 5/10
                    self.credit.score = Decimal('5.0')
                elif diff_jours <= 60:
                    # Paiement 2 mois après (31 à 60 jours) : 2/10
                    self.credit.score = Decimal('2.0')
                else:
                    # Paiement plus de 2 mois après : 0/10
                    self.credit.score = Decimal('0.0')
            else:
                # Si pas de date_fin, score par défaut 10
                self.credit.score = Decimal('10.0')
            
            self.credit.save()
            # Envoi d'email de fin de remboursement
            from users.models import Cooperative
            coop = Cooperative.objects.first()
            
            # Déterminer le destinataire (membre ou client)
            destinataire = None
            nom_destinataire = None
            if self.credit.membre:
                destinataire = self.credit.membre
                nom_destinataire = f"{self.credit.membre.nom} {self.credit.membre.prenom}"
            elif self.credit.client:
                destinataire = self.credit.client
                nom_destinataire = f"{self.credit.client.nom} {self.credit.client.prenom}"
            
            # Envoyer l'email seulement si on a un destinataire avec un email
            if destinataire and hasattr(destinataire, 'email') and destinataire.email:
                backend = get_smtp_backend()
                from_email = coop.email if coop and hasattr(coop, 'email') and coop.email else get_default_from_email()
                send_mail(
                    subject="Crédit remboursé avec succès",
                    message=f"Bonjour {nom_destinataire}, vous avez terminé le remboursement de votre crédit de {self.credit.montant} FCFA. Félicitations !",
                    from_email=from_email,
                    recipient_list=[destinataire.email],
                    fail_silently=True,
                    connection=backend
                )
        else:
            self.credit.save()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-echeance', '-id']
        verbose_name = 'Remboursement'
        verbose_name_plural = 'Remboursements'