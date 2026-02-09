from django.utils import timezone
from .models import Credit

def notifier_credits_echeance():
    for credit in Credit.objects.filter(statut='EN_COURS'):
        if credit.jours_restants == 0:
            credit.check_and_notify_echeance()
