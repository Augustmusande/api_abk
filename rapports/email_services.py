"""
Services d'envoi automatique d'emails avec reçus PDF en pièce jointe
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from users.email_config import get_smtp_backend, get_default_from_email
from io import BytesIO
from decimal import Decimal
from users.models import Cooperative
from membres.models import DonnatEpargne, DonnatPartSocial, Retrait, FraisAdhesion
from credits.models import Credit, Remboursement
from rapports.models import EnvoiEmail, StatutEnvoi
from rapports.email_templates import (
    get_email_template_depot_epargne,
    get_email_template_versement_part_sociale,
    get_email_template_retrait,
    get_email_template_credit,
    get_email_template_remboursement,
    get_email_template_frais_adhesion
)
from rapports.receipts import (
    generate_receipt_depot_epargne,
    generate_receipt_versement_part_sociale,
    generate_receipt_retrait,
    generate_receipt_credit,
    generate_receipt_remboursement,
    generate_receipt_frais_adhesion
)


def envoyer_email_avec_receipt(template_html, sujet, destinataire_email, destinataire_type, destinataire_id, pdf_buffer, operation_type, operation_id):
    """
    Envoie un email HTML avec un reçu PDF en pièce jointe
    
    Args:
        template_html (str): Template HTML de l'email
        sujet (str): Sujet de l'email
        destinataire_email (str): Email du destinataire
        destinataire_type (str): Type de destinataire (MEMBRE, CLIENT, ADMIN)
        destinataire_id (int): ID du destinataire
        pdf_buffer (BytesIO): Buffer du PDF à joindre
        operation_type (str): Type d'opération (pour le nom du fichier)
        operation_id (int): ID de l'opération (pour le nom du fichier)
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    coop = Cooperative.objects.first()
    
    # Créer l'enregistrement d'envoi
    envoi = EnvoiEmail.objects.create(
        rapport=None,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id or 0,
        email_destinataire=destinataire_email,
        sujet=sujet,
        message=template_html,
        statut=StatutEnvoi.EN_COURS
    )
    
    try:
        # Utiliser la configuration SMTP dynamique ou celle par défaut
        backend = get_smtp_backend()
        from_email = coop.email if coop and coop.email else get_default_from_email()
        
        # Créer l'email avec HTML
        email = EmailMultiAlternatives(
            subject=sujet,
            body='',  # Version texte vide, on utilise HTML
            from_email=from_email,
            to=[destinataire_email],
            connection=backend
        )
        
        # Ajouter la version HTML
        email.attach_alternative(template_html, "text/html")
        
        # Ajouter le PDF en pièce jointe
        if pdf_buffer:
            pdf_buffer.seek(0)
            filename = f"receipt_{operation_type}_{operation_id}.pdf"
            email.attach(filename, pdf_buffer.read(), 'application/pdf')
        
        # Envoyer l'email
        email.send()
        
        # Marquer comme envoyé
        envoi.statut = StatutEnvoi.ENVOYE
        envoi.date_envoi = timezone.now()
        envoi.save()
        
        return envoi
        
    except Exception as e:
        # Marquer comme échec
        envoi.statut = StatutEnvoi.ECHEC
        envoi.erreur = str(e)
        envoi.save()
        return envoi


def envoyer_email_depot_epargne(donnat_epargne_id):
    """
    Envoie automatiquement un email avec reçu PDF après un dépôt d'épargne
    
    Args:
        donnat_epargne_id (int): ID du DonnatEpargne
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        donnat_epargne = DonnatEpargne.objects.get(id=donnat_epargne_id)
    except DonnatEpargne.DoesNotExist:
        return None
    
    # Récupérer le titulaire
    souscription = donnat_epargne.souscriptEpargne
    compte = souscription.compte
    titulaire = compte.titulaire_membre or compte.titulaire_client
    
    # Vérifier que le titulaire a un email
    if not titulaire or not hasattr(titulaire, 'email') or not titulaire.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_depot_epargne(donnat_epargne, titulaire)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_depot_epargne(donnat_epargne_id)
    
    # Déterminer le type de destinataire
    if compte.titulaire_membre:
        destinataire_type = 'MEMBRE'
        destinataire_id = compte.titulaire_membre.id
    else:
        destinataire_type = 'CLIENT'
        destinataire_id = compte.titulaire_client.id
    
    # Sujet de l'email
    sujet = f"Confirmation de votre dépôt d'épargne - {donnat_epargne.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=titulaire.email,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        pdf_buffer=pdf_buffer,
        operation_type='depot_epargne',
        operation_id=donnat_epargne_id
    )
    
    return envoi


def envoyer_email_versement_part_sociale(donnat_part_social_id):
    """
    Envoie automatiquement un email avec reçu PDF après un versement de part sociale
    
    Args:
        donnat_part_social_id (int): ID du DonnatPartSocial
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        donnat_part = DonnatPartSocial.objects.get(id=donnat_part_social_id)
    except DonnatPartSocial.DoesNotExist:
        return None
    
    # Récupérer le membre
    membre = donnat_part.souscription_part_social.membre
    
    # Vérifier que le membre a un email
    if not membre or not hasattr(membre, 'email') or not membre.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_versement_part_sociale(donnat_part, membre)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_versement_part_sociale(donnat_part_social_id)
    
    # Sujet de l'email
    sujet = f"Confirmation de votre versement de part sociale - {donnat_part.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=membre.email,
        destinataire_type='MEMBRE',
        destinataire_id=membre.id,
        pdf_buffer=pdf_buffer,
        operation_type='versement_part_sociale',
        operation_id=donnat_part_social_id
    )
    
    return envoi


def envoyer_email_retrait(retrait_id):
    """
    Envoie automatiquement un email avec reçu PDF après un retrait
    
    Args:
        retrait_id (int): ID du Retrait
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        retrait = Retrait.objects.get(id=retrait_id)
    except Retrait.DoesNotExist:
        return None
    
    # Récupérer le titulaire
    souscription = retrait.souscriptEpargne
    compte = souscription.compte
    titulaire = compte.titulaire_membre or compte.titulaire_client
    
    # Vérifier que le titulaire a un email
    if not titulaire or not hasattr(titulaire, 'email') or not titulaire.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_retrait(retrait, titulaire)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_retrait(retrait_id)
    
    # Déterminer le type de destinataire
    if compte.titulaire_membre:
        destinataire_type = 'MEMBRE'
        destinataire_id = compte.titulaire_membre.id
    else:
        destinataire_type = 'CLIENT'
        destinataire_id = compte.titulaire_client.id
    
    # Sujet de l'email
    sujet = f"Confirmation de votre retrait - {retrait.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=titulaire.email,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        pdf_buffer=pdf_buffer,
        operation_type='retrait',
        operation_id=retrait_id
    )
    
    return envoi


def envoyer_email_credit(credit_id):
    """
    Envoie automatiquement un email avec reçu PDF après l'octroi d'un crédit
    
    Args:
        credit_id (int): ID du Credit
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        credit = Credit.objects.get(id=credit_id)
    except Credit.DoesNotExist:
        return None
    
    # Récupérer le titulaire
    titulaire = credit.membre or credit.client
    
    # Vérifier que le titulaire a un email
    if not titulaire or not hasattr(titulaire, 'email') or not titulaire.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_credit(credit, titulaire)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_credit(credit_id)
    
    # Déterminer le type de destinataire
    if credit.membre:
        destinataire_type = 'MEMBRE'
        destinataire_id = credit.membre.id
    else:
        destinataire_type = 'CLIENT'
        destinataire_id = credit.client.id
    
    # Sujet de l'email
    sujet = f"Votre crédit a été octroyé - {credit.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=titulaire.email,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        pdf_buffer=pdf_buffer,
        operation_type='credit',
        operation_id=credit_id
    )
    
    return envoi


def envoyer_email_remboursement(remboursement_id):
    """
    Envoie automatiquement un email avec reçu PDF après un remboursement
    
    Args:
        remboursement_id (int): ID du Remboursement
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        remboursement = Remboursement.objects.get(id=remboursement_id)
    except Remboursement.DoesNotExist:
        return None
    
    # Récupérer le titulaire
    credit = remboursement.credit
    titulaire = credit.membre or credit.client
    
    # Vérifier que le titulaire a un email
    if not titulaire or not hasattr(titulaire, 'email') or not titulaire.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_remboursement(remboursement, titulaire)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_remboursement(remboursement_id)
    
    # Déterminer le type de destinataire
    if credit.membre:
        destinataire_type = 'MEMBRE'
        destinataire_id = credit.membre.id
    else:
        destinataire_type = 'CLIENT'
        destinataire_id = credit.client.id
    
    # Sujet de l'email
    sujet = f"Confirmation de votre remboursement - {remboursement.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=titulaire.email,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        pdf_buffer=pdf_buffer,
        operation_type='remboursement',
        operation_id=remboursement_id
    )
    
    return envoi


def envoyer_email_frais_adhesion(frais_adhesion_id):
    """
    Envoie automatiquement un email avec reçu PDF après le paiement de frais d'adhésion
    
    Args:
        frais_adhesion_id (int): ID du FraisAdhesion
    
    Returns:
        EnvoiEmail: Instance de l'envoi créé
    """
    try:
        frais_adhesion = FraisAdhesion.objects.get(id=frais_adhesion_id)
    except FraisAdhesion.DoesNotExist:
        return None
    
    # Récupérer le titulaire
    titulaire = frais_adhesion.titulaire_membre or frais_adhesion.titulaire_client
    
    # Vérifier que le titulaire a un email
    if not titulaire or not hasattr(titulaire, 'email') or not titulaire.email:
        return None
    
    # Générer le template HTML
    template_html = get_email_template_frais_adhesion(frais_adhesion, titulaire)
    
    # Générer le PDF
    pdf_buffer = generate_receipt_frais_adhesion(frais_adhesion_id)
    
    # Déterminer le type de destinataire
    if frais_adhesion.titulaire_membre:
        destinataire_type = 'MEMBRE'
        destinataire_id = frais_adhesion.titulaire_membre.id
    else:
        destinataire_type = 'CLIENT'
        destinataire_id = frais_adhesion.titulaire_client.id
    
    # Sujet de l'email
    sujet = f"Confirmation de votre paiement de frais d'adhésion - {frais_adhesion.montant} USD"
    
    # Envoyer l'email
    envoi = envoyer_email_avec_receipt(
        template_html=template_html,
        sujet=sujet,
        destinataire_email=titulaire.email,
        destinataire_type=destinataire_type,
        destinataire_id=destinataire_id,
        pdf_buffer=pdf_buffer,
        operation_type='frais_adhesion',
        operation_id=frais_adhesion_id
    )
    
    return envoi


