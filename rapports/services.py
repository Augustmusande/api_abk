"""
Services pour la génération de rapports et l'envoi d'emails
"""
from decimal import Decimal
from datetime import date, datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from users.email_config import get_smtp_backend, get_default_from_email
from users.models import Cooperative
from caisse.services import (
    calculer_apports_tous_membres,
    calculer_interets_tous_credits,
    calculer_frais_gestion,
    repartir_interets_aux_membres
)
from credits.models import Credit
# Utiliser Caissetypemvt pour tous les mouvements
from rapports.models import Rapport, EnvoiEmail, TypeRapport, StatutEnvoi

def generer_rapport_apports(periode_mois=None, periode_annee=None):
    """
    Génère un rapport des apports des membres
    
    Args:
        periode_mois (int, optional): Mois pour filtrer (1-12)
        periode_annee (int, optional): Année pour filtrer
    
    Returns:
        dict: Données du rapport
    """
    apports = calculer_apports_tous_membres(periode_mois, periode_annee)
    
    return {
        'type': 'APPORTS',
        'periode_mois': periode_mois,
        'periode_annee': periode_annee,
        'date_generation': datetime.now().isoformat(),
        'donnees': apports
    }

def generer_rapport_interets(pourcentage_frais_gestion=20, periode_mois=None, periode_annee=None):
    """
    Génère un rapport de répartition des intérêts
    
    Args:
        pourcentage_frais_gestion (float): Pourcentage des frais de gestion
        periode_mois (int, optional): Mois pour filtrer (1-12)
        periode_annee (int, optional): Année pour filtrer
    
    Returns:
        dict: Données du rapport
    """
    repartition = repartir_interets_aux_membres(
        pourcentage_frais_gestion,
        periode_mois,
        periode_annee
    )
    
    return {
        'type': 'INTERETS',
        'pourcentage_frais_gestion': pourcentage_frais_gestion,
        'periode_mois': periode_mois,
        'periode_annee': periode_annee,
        'date_generation': datetime.now().isoformat(),
        'donnees': repartition
    }

def generer_rapport_caisse():
    """
    Génère un rapport de situation de la caisse
    
    Returns:
        dict: Données du rapport
    """
    # TODO: Calculer le solde de caisse - Réimplémenter avec Caissetypemvt
    # Les OPERATIONS sont maintenant gérées via Caissetypemvt
    total_entrees = Decimal('0.00')
    total_entrees_frais = Decimal('0.00')
    total_sorties = Decimal('0.00')
    solde_caisse = Decimal('0.00')
    
    # Calculer les apports
    apports = calculer_apports_tous_membres()
    
    # Calculer les crédits actifs
    credits_actifs = Credit.objects.filter(statut__in=['EN_COURS', 'ECHEANCE_DEPASSEE'])
    total_credits_actifs = sum([c.solde_restant for c in credits_actifs])
    
    return {
        'type': 'CAISSE',
        'date_generation': datetime.now().isoformat(),
        'donnees': {
            'solde_caisse': float(solde_caisse),
            'total_entrees': float(total_entrees),
            'total_entrees_frais_gestion': float(total_entrees_frais),
            'total_sorties': float(total_sorties),
            'apports': apports,
            'total_credits_actifs': float(total_credits_actifs)
        }
    }

def generer_rapport_credits():
    """
    Génère un rapport des crédits
    
    Returns:
        dict: Données du rapport
    """
    credits = Credit.objects.all()
    credits_actifs = credits.filter(statut__in=['EN_COURS', 'ECHEANCE_DEPASSEE'])
    credits_termines = credits.filter(statut='TERMINE')
    
    total_credits_actifs = sum([c.solde_restant for c in credits_actifs])
    total_credits_termines = sum([c.montant for c in credits_termines])
    
    return {
        'type': 'CREDITS',
        'date_generation': datetime.now().isoformat(),
        'donnees': {
            'nombre_credits_actifs': credits_actifs.count(),
            'nombre_credits_termines': credits_termines.count(),
            'total_credits_actifs': float(total_credits_actifs),
            'total_credits_termines': float(total_credits_termines),
            'credits_actifs': [
                {
                    'id': c.id,
                    'membre_id': c.membre_id,
                    'client_id': c.client_id,
                    'montant': float(c.montant),
                    'solde_restant': float(c.solde_restant),
                    'statut': c.statut,
                    'date_octroi': c.date_octroi.isoformat() if c.date_octroi else None
                }
                for c in credits_actifs
            ]
        }
    }

def generer_rapport_operations(periode_mois=None, periode_annee=None, type_operation=None):
    """
    TODO: Réimplémenter avec Caissetypemvt
    Cette fonction sera réimplémentée pour utiliser Caissetypemvt
    """
    from datetime import date
    
    # TODO: Réimplémenter avec Caissetypemvt
    OPERATIONS = []
    
    # TODO: Réimplémenter avec Caissetypemvt
    total_entrees = Decimal('0.00')
    total_frais_gestion = Decimal('0.00')
    total_sorties = Decimal('0.00')
    solde = Decimal('0.00')
    
    return {
        'type': 'OPERATIONS',
        'periode_mois': periode_mois,
        'periode_annee': periode_annee or date.today().year,
        'type_operation': type_operation,
        'date_generation': datetime.now().isoformat(),
        'donnees': {
            'total_entrees': float(total_entrees),
            'total_frais_gestion': float(total_frais_gestion),
            'total_sorties': float(total_sorties),
            'solde_caisse': float(solde),
            'nombre_OPERATIONS': 0,
            'nombre_entrees': 0,
            'nombre_frais_gestion': 0,
            'nombre_sorties': 0,
            'OPERATIONS': []
        }
    }

def generer_rapport_mensuel(periode_mois, periode_annee):
    """
    Génère un rapport mensuel complet
    
    Args:
        periode_mois (int): Mois (1-12)
        periode_annee (int): Année
    
    Returns:
        dict: Données du rapport mensuel
    """
    return {
        'type': 'MENSUEL',
        'periode_mois': periode_mois,
        'periode_annee': periode_annee,
        'date_generation': datetime.now().isoformat(),
        'donnees': {
            'apports': generer_rapport_apports(periode_mois, periode_annee)['donnees'],
            'interets': generer_rapport_interets(periode_mois=periode_mois, periode_annee=periode_annee)['donnees'],
            'caisse': generer_rapport_caisse()['donnees'],
            'credits': generer_rapport_credits()['donnees']
        }
    }

def generer_rapport_annuel(periode_annee):
    """
    Génère un rapport annuel complet
    
    Args:
        periode_annee (int): Année
    
    Returns:
        dict: Données du rapport annuel
    """
    return {
        'type': 'ANNUEL',
        'periode_annee': periode_annee,
        'date_generation': datetime.now().isoformat(),
        'donnees': {
            'apports': generer_rapport_apports(periode_annee=periode_annee)['donnees'],
            'interets': generer_rapport_interets(periode_annee=periode_annee)['donnees'],
            'caisse': generer_rapport_caisse()['donnees'],
            'credits': generer_rapport_credits()['donnees']
        }
    }

def sauvegarder_rapport(type_rapport, contenu, periode_mois=None, periode_annee=None):
    """
    Sauvegarde un rapport dans la base de données
    
    Args:
        type_rapport (str): Type de rapport
        contenu (dict): Contenu du rapport
        periode_mois (int, optional): Mois
        periode_annee (int, optional): Année
    
    Returns:
        Rapport: Instance du rapport sauvegardé
    """
    rapport = Rapport.objects.create(
        type_rapport=type_rapport,
        periode_mois=periode_mois,
        periode_annee=periode_annee or date.today().year,
        contenu=contenu
    )
    return rapport

def envoyer_email_rapport(rapport, destinataire_email, destinataire_type='ADMIN', destinataire_id=None):
    """
    Envoie un rapport par email
    
    Args:
        rapport (Rapport): Rapport à envoyer
        destinataire_email (str): Email du destinataire
        destinataire_type (str): Type de destinataire (MEMBRE, CLIENT, ADMIN)
        destinataire_id (int, optional): ID du destinataire
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    coop = Cooperative.objects.first()
    
    # Préparer le sujet et le message
    sujet = f"Rapport {rapport.get_type_rapport_display()} - COOPEC"
    
    # Générer le message HTML/text
    message = f"""
Bonjour,

Veuillez trouver ci-joint le rapport {rapport.get_type_rapport_display()} pour la période {rapport.periode_annee}.
    
Cordialement,
COOPEC
"""
    
    # Créer l'enregistrement d'envoi
    envoi = EnvoiEmail.objects.create(
        rapport=rapport,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id or 0,
        email_destinataire=destinataire_email,
        sujet=sujet,
        message=message,
        statut=StatutEnvoi.EN_COURS
    )
    
    try:
        # Utiliser la configuration SMTP dynamique
        backend = get_smtp_backend()
        from_email = coop.email if coop and hasattr(coop, 'email') and coop.email else get_default_from_email()
        
        # Envoyer l'email avec le backend configuré
        send_mail(
            subject=sujet,
            message=message,
            from_email=from_email,
            recipient_list=[destinataire_email],
            fail_silently=False,
            connection=backend
        )
        
        # Marquer comme envoyé
        envoi.statut = StatutEnvoi.ENVOYE
        envoi.date_envoi = timezone.now()
        envoi.save()
        
        # Marquer le rapport comme envoyé
        rapport.envoye = True
        rapport.date_envoi = timezone.now()
        rapport.save()
        
    except Exception as e:
        # Marquer comme échec
        envoi.statut = StatutEnvoi.ECHEC
        envoi.erreur = str(e)
        envoi.save()
    
    return envoi

def envoyer_rapport_membre(membre, type_rapport='MENSUEL', periode_mois=None, periode_annee=None):
    """
    Génère et envoie un rapport à un membre
    
    Args:
        membre: Instance du membre
        type_rapport (str): Type de rapport
        periode_mois (int, optional): Mois
        periode_annee (int, optional): Année
    
    Returns:
        tuple: (Rapport, EnvoiEmail)
    """
    if not membre.email:
        raise ValueError(f"Le membre {membre.numero_compte} n'a pas d'email")
    
    # Générer le rapport selon le type
    if type_rapport == 'MENSUEL':
        contenu = generer_rapport_mensuel(periode_mois, periode_annee)
    elif type_rapport == 'ANNUEL':
        contenu = generer_rapport_annuel(periode_annee)
    elif type_rapport == 'APPORTS':
        contenu = generer_rapport_apports(periode_mois, periode_annee)
    else:
        raise ValueError(f"Type de rapport non supporté: {type_rapport}")
    
    # Sauvegarder le rapport
    rapport = sauvegarder_rapport(type_rapport, contenu, periode_mois, periode_annee)
    
    # Envoyer l'email
    envoi = envoyer_email_rapport(rapport, membre.email, 'MEMBRE', membre.id)
    
    return rapport, envoi

