"""
Service de génération de reçus PDF similaires au reçu bancaire TMB
Utilise reportlab pour créer des PDFs professionnels
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from users.models import Cooperative
from membres.models import DonnatEpargne, DonnatPartSocial, Retrait, FraisAdhesion
from credits.models import Credit, Remboursement

# Couleurs bleues du logo COOPEC
BLUE_LIGHT = HexColor('#4A90E2')  # Bleu clair
BLUE_DARK = HexColor('#2E5C8A')   # Bleu foncé
BLUE_MEDIUM = HexColor('#357ABD') # Bleu moyen

def get_cooperative_info():
    """Récupère les informations de la coopérative"""
    coop = Cooperative.objects.first()
    if not coop:
        return None
    
    return {
        'nom': coop.nom,
        'sigle': coop.sigle or '',
        'adresse': coop.adresse or '',
        'ville': coop.ville or '',
        'province': coop.province or '',
        'pays': coop.pays or 'RDC',
        'telephone': coop.telephone or '',
        'email': coop.email or '',
        'site_web': coop.site_web or '',
        'numero_rccm': coop.numero_rccm or '',
        'numero_id_nat': coop.numero_id_nat or '',
        'agrement': coop.agrement or '',
        'logo': coop.logo if coop.logo else None
    }

def format_currency(amount):
    """Formate un montant en devise USD"""
    return f"{float(amount):,.2f}".replace(',', ' ').replace('.', ',')

def generate_receipt_header(canvas_obj, doc, coop_info):
    """Génère l'en-tête du reçu (logo, nom, informations complètes)"""
    width, height = A4
    canvas_obj.saveState()
    
    # Ligne bleue horizontale en haut (comme le logo)
    canvas_obj.setStrokeColor(BLUE_MEDIUM)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(20*mm, height - 25*mm, width - 20*mm, height - 25*mm)
    
    # Logo à droite (si disponible)
    logo_x = width - 50*mm
    logo_y = height - 40*mm
    if coop_info and coop_info.get('logo'):
        try:
            logo_path = coop_info['logo'].path
            if os.path.exists(logo_path):
                canvas_obj.drawImage(logo_path, logo_x, logo_y, width=25*mm, height=25*mm, preserveAspectRatio=True)
        except:
            pass
    
    # Nom de la coopérative en bleu (comme le logo) - à gauche
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.setFillColor(BLUE_MEDIUM)
    nom = coop_info['nom'] if coop_info else "COOPEC"
    canvas_obj.drawString(20*mm, height - 35*mm, nom)
    
    # Sigle ou sous-titre
    if coop_info and coop_info.get('sigle'):
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(20*mm, height - 42*mm, coop_info['sigle'])
    
    # Informations complètes de la coopérative
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.black)
    y_pos = height - 50*mm
    
    if coop_info:
        # Siège social
        siege_parts = []
        if coop_info.get('adresse'):
            siege_parts.append(coop_info['adresse'])
        if coop_info.get('ville'):
            siege_parts.append(coop_info['ville'])
        if coop_info.get('province'):
            siege_parts.append(coop_info['province'])
        if coop_info.get('pays'):
            siege_parts.append(coop_info['pays'])
        
        if siege_parts:
            siege = f"Siège Social: {', '.join(siege_parts)}"
            canvas_obj.drawString(20*mm, y_pos, siege)
            y_pos -= 5*mm
        
        # RCCM
        if coop_info.get('numero_rccm'):
            rccm = f"R.C.C.M.: {coop_info['numero_rccm']}"
            canvas_obj.drawString(20*mm, y_pos, rccm)
            y_pos -= 5*mm
        
        # ID National
        if coop_info.get('numero_id_nat'):
            id_nat = f"Id. Nat.: {coop_info['numero_id_nat']}"
            canvas_obj.drawString(20*mm, y_pos, id_nat)
            y_pos -= 5*mm
        
        # Agrément
        if coop_info.get('agrement'):
            agrement = f"N° Agrément: {coop_info['agrement']}"
            canvas_obj.drawString(20*mm, y_pos, agrement)
            y_pos -= 5*mm
        
        # Contact
        contact_parts = []
        if coop_info.get('telephone'):
            contact_parts.append(f"Tél.: {coop_info['telephone']}")
        if coop_info.get('email'):
            contact_parts.append(f"E-mail: {coop_info['email']}")
        if coop_info.get('site_web'):
            site = coop_info['site_web'].replace('http://', '').replace('https://', '')
            contact_parts.append(f"www.{site}")
        
        if contact_parts:
            contact = " - ".join(contact_parts)
            canvas_obj.drawString(20*mm, y_pos, contact)
            y_pos -= 5*mm
        
        # Date en bas de l'en-tête
        date_str = datetime.now().strftime("%d.%m.%Y")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(BLUE_MEDIUM)
        canvas_obj.drawString(20*mm, y_pos, f"Date: {date_str}")
    
    canvas_obj.restoreState()

def generate_receipt_footer(canvas_obj, doc):
    """Génère le pied de page du reçu (signatures)"""
    width, height = A4
    canvas_obj.saveState()
    
    # Ligne de séparation bleue
    canvas_obj.setStrokeColor(BLUE_MEDIUM)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(20*mm, 50*mm, width - 20*mm, 50*mm)
    
    # Zone de signatures
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.black)
    
    # Signature client
    canvas_obj.drawString(20*mm, 45*mm, "SIGNATURE DU CLIENT")
    
    # Signature opérateur
    canvas_obj.drawString(width - 80*mm, 45*mm, "SIGNATURE DE L'OPERATEUR")
    
    # Pas de cachet - enlevé comme demandé
    
    canvas_obj.restoreState()

def generate_receipt_depot_epargne(donnat_epargne_id):
    """Génère un reçu PDF pour un dépôt d'épargne"""
    try:
        donnat_epargne = DonnatEpargne.objects.get(id=donnat_epargne_id)
    except DonnatEpargne.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU DE DÉPÔT D'ÉPARGNE", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations de l'opération
    souscription = donnat_epargne.souscriptEpargne
    compte = souscription.compte
    titulaire = compte.titulaire_membre or compte.titulaire_client
    
    # Calculer le total des dépôts après ce dépôt
    total_depots = souscription.total_donne
    
    # Numéro de référence
    ref = f"REF-{donnat_epargne.id:08d}"
    date_operation = datetime.now().strftime("%d-%m-%Y")
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'VERSEMENT SUR COMPTE ÉPARGNE'],
        ['ENTREE:', f"{format_currency(donnat_epargne.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Compte crédité
    story.append(Paragraph("<b>COMPTE CRÉDITÉ:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    compte_data = [
        ['NUMÉRO:', str(compte.id)],
        ['TYPE COMPTE:', compte.get_type_compte_display()],
        ['INTITULÉ:', str(titulaire)],
        ['MONTANT:', f"{format_currency(donnat_epargne.montant)} USD"],
        ['MOIS:', donnat_epargne.mois],
        ['TOTAL DÉPÔTS:', f"{format_currency(total_depots)} USD"],
    ]
    
    if titulaire:
        if hasattr(titulaire, 'numero_compte'):
            compte_data.insert(1, ['NUMÉRO COMPTE:', titulaire.numero_compte])
    
    compte_table = Table(compte_data, colWidths=[50*mm, 120*mm])
    compte_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(compte_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: DÉPÔT D'ÉPARGNE - {souscription.designation}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_versement_part_sociale(donnat_part_social_id):
    """Génère un reçu PDF pour un versement de part sociale"""
    try:
        donnat_part = DonnatPartSocial.objects.get(id=donnat_part_social_id)
    except DonnatPartSocial.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU DE VERSEMENT DE PART SOCIALE", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations de l'opération
    souscription = donnat_part.souscription_part_social
    membre = souscription.membre
    
    ref = f"REF-{donnat_part.id:08d}"
    date_operation = donnat_part.date_donnat.strftime("%d-%m-%Y")
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'VERSEMENT PART SOCIALE'],
        ['ENTREE:', f"{format_currency(donnat_part.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Membre
    story.append(Paragraph("<b>MEMBRE:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    membre_data = [
        ['NUMÉRO COMPTE:', membre.numero_compte],
        ['NOM:', str(membre)],
        ['MONTANT:', f"{format_currency(donnat_part.montant)} USD"],
        ['MOIS:', donnat_part.mois],
        ['PART SOCIALE:', f"{souscription.partSocial.annee}"],
        ['TOTAL VERSÉ:', f"{format_currency(souscription.montant_total_verse)} USD"],
    ]
    
    membre_table = Table(membre_data, colWidths=[50*mm, 120*mm])
    membre_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(membre_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: VERSEMENT PART SOCIALE {souscription.partSocial.annee}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_retrait(retrait_id):
    """Génère un reçu PDF pour un retrait"""
    try:
        retrait = Retrait.objects.get(id=retrait_id)
    except Retrait.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU DE RETRAIT", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations de l'opération
    souscription = retrait.souscriptEpargne
    compte = souscription.compte
    titulaire = compte.titulaire_membre or compte.titulaire_client
    
    # Calculer le solde restant après ce retrait
    solde_restant = souscription.solde_epargne
    
    ref = f"REF-{retrait.id:08d}"
    if hasattr(retrait.date_operation, 'strftime'):
        date_operation = retrait.date_operation.strftime("%d-%m-%Y")
    else:
        date_operation = str(retrait.date_operation)
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'RETRAIT SUR COMPTE ÉPARGNE'],
        ['SORTIE:', f"{format_currency(retrait.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Compte débité
    story.append(Paragraph("<b>COMPTE DÉBITÉ:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    compte_data = [
        ['NUMÉRO:', str(compte.id)],
        ['TYPE COMPTE:', compte.get_type_compte_display()],
        ['INTITULÉ:', str(titulaire)],
        ['MONTANT:', f"{format_currency(retrait.montant)} USD"],
        ['SOLDE RESTANT:', f"{format_currency(solde_restant)} USD"],
    ]
    
    if titulaire and hasattr(titulaire, 'numero_compte'):
        compte_data.insert(1, ['NUMÉRO COMPTE:', titulaire.numero_compte])
    
    compte_table = Table(compte_data, colWidths=[50*mm, 120*mm])
    compte_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(compte_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: RETRAIT - {souscription.designation}"
    if retrait.motif:
        libelle += f" - {retrait.motif}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_credit(credit_id):
    """Génère un reçu PDF pour un crédit octroyé"""
    try:
        credit = Credit.objects.get(id=credit_id)
    except Credit.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU D'OCTROI DE CRÉDIT", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations de l'opération
    titulaire = credit.membre or credit.client
    
    ref = f"REF-{credit.id:08d}"
    if hasattr(credit.date_octroi, 'strftime'):
        date_operation = credit.date_octroi.strftime("%d-%m-%Y")
    else:
        date_operation = str(credit.date_octroi)
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'OCTROI DE CRÉDIT'],
        ['SORTIE:', f"{format_currency(credit.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Bénéficiaire
    story.append(Paragraph("<b>BÉNÉFICIAIRE:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    benef_data = [
        ['NUMÉRO COMPTE:', titulaire.numero_compte if titulaire else ''],
        ['NOM:', str(titulaire) if titulaire else ''],
        ['MONTANT:', f"{format_currency(credit.montant)} USD"],
        ['TAUX INTÉRÊT:', f"{credit.taux_interet}%"],
        ['INTÉRÊT:', f"{format_currency(credit.interet)} USD"],
        ['DURÉE:', f"{credit.duree} {credit.get_duree_type_display()}"],
        ['DATE FIN:', credit.date_fin.strftime("%d-%m-%Y") if credit.date_fin else ''],
        ['SOLDE RESTANT:', f"{format_currency(credit.solde_restant)} USD"],
    ]
    
    benef_table = Table(benef_data, colWidths=[50*mm, 120*mm])
    benef_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(benef_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: OCTROI DE CRÉDIT N° {credit.id}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_remboursement(remboursement_id):
    """Génère un reçu PDF pour un remboursement"""
    try:
        remboursement = Remboursement.objects.get(id=remboursement_id)
    except Remboursement.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU DE REMBOURSEMENT", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations de l'opération
    credit = remboursement.credit
    titulaire = credit.membre or credit.client
    
    ref = f"REF-{remboursement.id:08d}"
    if hasattr(remboursement.echeance, 'strftime'):
        date_operation = remboursement.echeance.strftime("%d-%m-%Y")
    else:
        date_operation = str(remboursement.echeance)
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'REMBOURSEMENT DE CRÉDIT'],
        ['ENTREE:', f"{format_currency(remboursement.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Informations du crédit
    story.append(Paragraph("<b>CRÉDIT:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    credit_data = [
        ['NUMÉRO COMPTE:', titulaire.numero_compte if titulaire else ''],
        ['NOM:', str(titulaire) if titulaire else ''],
        ['CRÉDIT N°:', str(credit.id)],
        ['MONTANT REMBOURSÉ:', f"{format_currency(remboursement.montant)} USD"],
        ['SOLDE RESTANT:', f"{format_currency(credit.solde_restant)} USD"],
    ]
    
    credit_table = Table(credit_data, colWidths=[50*mm, 120*mm])
    credit_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(credit_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: REMBOURSEMENT CRÉDIT N° {credit.id}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_frais_adhesion(frais_adhesion_id):
    """Génère un reçu PDF pour un paiement de frais d'adhésion"""
    try:
        frais_adhesion = FraisAdhesion.objects.get(id=frais_adhesion_id)
    except FraisAdhesion.DoesNotExist:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=80*mm, bottomMargin=20*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre en bleu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("REÇU DE PAIEMENT DE FRAIS D'ADHÉSION", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Récupérer le titulaire (membre ou client)
    titulaire = frais_adhesion.titulaire_membre or frais_adhesion.titulaire_client
    
    ref = f"REF-{frais_adhesion.id:08d}"
    if hasattr(frais_adhesion.date_paiement, 'strftime'):
        date_operation = frais_adhesion.date_paiement.strftime("%d-%m-%Y")
    else:
        date_operation = str(frais_adhesion.date_paiement)
    
    data = [
        ['N/REF:', ref],
        ['DATE:', date_operation],
        ['TYPE D\'OPÉRATION:', 'PAIEMENT FRAIS D\'ADHÉSION'],
        ['ENTREE:', f"{format_currency(frais_adhesion.montant)} USD"],
    ]
    
    table = Table(data, colWidths=[50*mm, 120*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Informations du titulaire
    if frais_adhesion.titulaire_membre:
        type_titulaire = 'MEMBRE'
    else:
        type_titulaire = 'CLIENT'
    
    story.append(Paragraph(f"<b>{type_titulaire}:</b>", styles['Normal']))
    story.append(Spacer(1, 2*mm))
    
    titulaire_data = [
        ['NUMÉRO COMPTE:', titulaire.numero_compte if titulaire and hasattr(titulaire, 'numero_compte') else ''],
        ['NOM:', str(titulaire) if titulaire else ''],
        ['MONTANT:', f"{format_currency(frais_adhesion.montant)} USD"],
        ['DATE PAIEMENT:', date_operation],
    ]
    
    # Ajouter des informations supplémentaires si disponibles
    if titulaire:
        if hasattr(titulaire, 'email') and titulaire.email:
            titulaire_data.append(['EMAIL:', titulaire.email])
        if hasattr(titulaire, 'telephone') and titulaire.telephone:
            titulaire_data.append(['TÉLÉPHONE:', titulaire.telephone])
    
    titulaire_table = Table(titulaire_data, colWidths=[50*mm, 120*mm])
    titulaire_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE_MEDIUM),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(titulaire_table)
    story.append(Spacer(1, 5*mm))
    
    # Libellé
    libelle = f"LIBELLÉ: PAIEMENT FRAIS D'ADHÉSION - {type_titulaire}"
    story.append(Paragraph(libelle, styles['Normal']))
    
    # Message de confirmation
    story.append(Spacer(1, 5*mm))
    message_style = ParagraphStyle(
        'MessageStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph(
        "<b>Merci pour votre adhésion ! Votre paiement a été enregistré avec succès.</b>",
        message_style
    ))
    
    # Fonction callback pour header et footer
    def on_first_page(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    def on_later_pages(canvas_obj, doc):
        generate_receipt_header(canvas_obj, doc, coop_info)
        generate_receipt_footer(canvas_obj, doc)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer

def generate_receipt_transaction(operation_id):
    """
    TODO: Réimplémenter avec Caissetypemvt
    Cette fonction sera réimplémentée pour utiliser Caissetypemvt
    """
    return None
