"""
Service de génération de relevés de compte pour membres et clients
Format similaire au relevé bancaire TMB
"""
import os
from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
from users.models import Membre, Client, Cooperative
from membres.models import (
    FraisAdhesion, DonnatEpargne, DonnatPartSocial, 
    Retrait, Compte, SouscriptEpargne, SouscriptionPartSocial
)
from credits.models import Credit, Remboursement
# Utiliser Caissetypemvt pour tous les mouvements

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

def collecter_toutes_OPERATIONS_membre(membre, date_debut=None, date_fin=None):
    """
    Collecte toutes les OPERATIONS d'un membre dans la coopérative
    
    Args:
        membre: Instance du Membre
        date_debut: Date de début (optionnel)
        date_fin: Date de fin (optionnel)
    
    Returns:
        list: Liste de toutes les OPERATIONS triées par date
    """
    OPERATIONS = []
    
    # 1. Versements de parts sociales (ENTREE)
    # Récupérer toutes les souscriptions de parts sociales
    souscriptions_parts = SouscriptionPartSocial.objects.filter(membre=membre)
    
    for souscription in souscriptions_parts:
        donnats = DonnatPartSocial.objects.filter(souscription_part_social=souscription)
        if date_debut:
            donnats = donnats.filter(date_donnat__gte=date_debut)
        if date_fin:
            donnats = donnats.filter(date_donnat__lte=date_fin)
        
        for donnat in donnats:
            OPERATIONS.append({
                'date_trans': donnat.date_donnat,
                'date_val': donnat.date_donnat,
                'libelle': f'VERSEMENT PART SOCIALE {souscription.partSocial.annee}',
                'entree': donnat.montant,
                'sortie': Decimal('0.00'),
                'opn_no': f'PS-{donnat.id:08d}',
                'opr': 'SYSTEM',
                'type': 'VERSEMENT_PART_SOCIALE',
                'reference_id': donnat.id
            })
    
    # 3. Dépôts d'épargne (ENTREE)
    # Récupérer tous les comptes du membre
    comptes = Compte.objects.filter(titulaire_membre=membre)
    
    for compte in comptes:
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription in souscriptions_epargne:
            donnats = DonnatEpargne.objects.filter(souscriptEpargne=souscription)
            if date_debut:
                # Filtrer par date de souscription
                donnats = donnats.filter(souscriptEpargne__date_souscription__gte=date_debut)
            if date_fin:
                donnats = donnats.filter(souscriptEpargne__date_souscription__lte=date_fin)
            
            for donnat in donnats:
                # Utiliser la date de souscription comme date d'opération
                date_txn = souscription.date_souscription
                OPERATIONS.append({
                    'date_trans': date_txn,
                    'date_val': date_txn,
                    'libelle': f'DÉPÔT ÉPARGNE - {souscription.designation}',
                    'entree': donnat.montant,
                    'sortie': Decimal('0.00'),
                    'opn_no': f'DE-{donnat.id:08d}',
                    'opr': 'SYSTEM',
                    'type': 'DEPOT_EPARGNE',
                    'reference_id': donnat.id
                })
    
    # 2. Retraits (SORTIE)
    for compte in comptes:
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription in souscriptions_epargne:
            retraits = Retrait.objects.filter(souscriptEpargne=souscription)
            if date_debut:
                retraits = retraits.filter(date_operation__date__gte=date_debut)
            if date_fin:
                retraits = retraits.filter(date_operation__date__lte=date_fin)
            
            for retrait in retraits:
                OPERATIONS.append({
                    'date_trans': retrait.date_operation.date() if hasattr(retrait.date_operation, 'date') else retrait.date_operation,
                    'date_val': retrait.date_operation.date() if hasattr(retrait.date_operation, 'date') else retrait.date_operation,
                    'libelle': f'RETRAIT - {souscription.designation}',
                    'entree': Decimal('0.00'),
                    'sortie': retrait.montant,
                    'opn_no': f'RT-{retrait.id:08d}',
                    'opr': 'SYSTEM',
                    'type': 'RETRAIT',
                    'reference_id': retrait.id
                })
    
    # 3. Crédits octroyés (SORTIE)
    credits = Credit.objects.filter(membre=membre)
    if date_debut:
        credits = credits.filter(date_octroi__gte=date_debut)
    if date_fin:
        credits = credits.filter(date_octroi__lte=date_fin)
    
    for credit in credits:
        OPERATIONS.append({
            'date_trans': credit.date_octroi if credit.date_octroi else date.today(),
            'date_val': credit.date_octroi if credit.date_octroi else date.today(),
            'libelle': f'OCTROI CRÉDIT N° {credit.id}',
            'entree': Decimal('0.00'),
            'sortie': credit.montant,
            'opn_no': f'CR-{credit.id:08d}',
            'opr': 'SYSTEM',
            'type': 'CREDIT',
            'reference_id': credit.id
        })
    
    # 4. Remboursements (ENTREE)
    for credit in Credit.objects.filter(membre=membre):
        remboursements = Remboursement.objects.filter(credit=credit)
        if date_debut:
            remboursements = remboursements.filter(echeance__gte=date_debut)
        if date_fin:
            remboursements = remboursements.filter(echeance__lte=date_fin)
        
        for remboursement in remboursements:
            OPERATIONS.append({
                'date_trans': remboursement.echeance if remboursement.echeance else date.today(),
                'date_val': remboursement.echeance if remboursement.echeance else date.today(),
                'libelle': f'REMBOURSEMENT CRÉDIT N° {credit.id}',
                'entree': remboursement.montant,
                'sortie': Decimal('0.00'),
                'opn_no': f'RB-{remboursement.id:08d}',
                'opr': 'SYSTEM',
                'type': 'REMBOURSEMENT',
                'reference_id': remboursement.id
            })
    
    # 5. TODO: OPERATIONS de caisse liées (via FraisAdhesion) - Réimplémenter avec Caissetypemvt
    # Les OPERATIONS sont maintenant gérées via Caissetypemvt
    # Cette section sera réimplémentée pour utiliser Caissetypemvt
    
    # Trier par date (plus ancien en premier pour calculer le solde)
    OPERATIONS.sort(key=lambda x: (x['date_trans'], x['date_val']))
    
    return OPERATIONS

def collecter_toutes_OPERATIONS_client(client, date_debut=None, date_fin=None):
    """
    Collecte toutes les OPERATIONS d'un client dans la coopérative
    
    Args:
        client: Instance du Client
        date_debut: Date de début (optionnel)
        date_fin: Date de fin (optionnel)
    
    Returns:
        list: Liste de toutes les OPERATIONS triées par date
    """
    OPERATIONS = []
    
    # 1. Dépôts d'épargne (ENTREE)
    comptes = Compte.objects.filter(titulaire_client=client)
    
    for compte in comptes:
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription in souscriptions_epargne:
            donnats = DonnatEpargne.objects.filter(souscriptEpargne=souscription)
            if date_debut:
                donnats = donnats.filter(souscriptEpargne__date_souscription__gte=date_debut)
            if date_fin:
                donnats = donnats.filter(souscriptEpargne__date_souscription__lte=date_fin)
            
            for donnat in donnats:
                # Utiliser la date de souscription comme date d'opération
                date_txn = souscription.date_souscription
                OPERATIONS.append({
                    'date_trans': date_txn,
                    'date_val': date_txn,
                    'libelle': f'DÉPÔT ÉPARGNE - {souscription.designation}',
                    'entree': donnat.montant,
                    'sortie': Decimal('0.00'),
                    'opn_no': f'DE-{donnat.id:08d}',
                    'opr': 'SYSTEM',
                    'type': 'DEPOT_EPARGNE',
                    'reference_id': donnat.id
                })
    
    # 3. Retraits (SORTIE)
    for compte in comptes:
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription in souscriptions_epargne:
            retraits = Retrait.objects.filter(souscriptEpargne=souscription)
            if date_debut:
                retraits = retraits.filter(date_operation__date__gte=date_debut)
            if date_fin:
                retraits = retraits.filter(date_operation__date__lte=date_fin)
            
            for retrait in retraits:
                OPERATIONS.append({
                    'date_trans': retrait.date_operation.date() if hasattr(retrait.date_operation, 'date') else retrait.date_operation,
                    'date_val': retrait.date_operation.date() if hasattr(retrait.date_operation, 'date') else retrait.date_operation,
                    'libelle': f'RETRAIT - {souscription.designation}',
                    'entree': Decimal('0.00'),
                    'sortie': retrait.montant,
                    'opn_no': f'RT-{retrait.id:08d}',
                    'opr': 'SYSTEM',
                    'type': 'RETRAIT',
                    'reference_id': retrait.id
                })
    
    # 4. Crédits octroyés (SORTIE)
    credits = Credit.objects.filter(client=client)
    if date_debut:
        credits = credits.filter(date_octroi__gte=date_debut)
    if date_fin:
        credits = credits.filter(date_octroi__lte=date_fin)
    
    for credit in credits:
        OPERATIONS.append({
            'date_trans': credit.date_octroi if credit.date_octroi else date.today(),
            'date_val': credit.date_octroi if credit.date_octroi else date.today(),
            'libelle': f'OCTROI CRÉDIT N° {credit.id}',
            'entree': Decimal('0.00'),
            'sortie': credit.montant,
            'opn_no': f'CR-{credit.id:08d}',
            'opr': 'SYSTEM',
            'type': 'CREDIT',
            'reference_id': credit.id
        })
    
    # 5. Remboursements (ENTREE)
    for credit in Credit.objects.filter(client=client):
        remboursements = Remboursement.objects.filter(credit=credit)
        if date_debut:
            remboursements = remboursements.filter(echeance__gte=date_debut)
        if date_fin:
            remboursements = remboursements.filter(echeance__lte=date_fin)
        
        for remboursement in remboursements:
            OPERATIONS.append({
                'date_trans': remboursement.echeance if remboursement.echeance else date.today(),
                'date_val': remboursement.echeance if remboursement.echeance else date.today(),
                'libelle': f'REMBOURSEMENT CRÉDIT N° {credit.id}',
                'entree': remboursement.montant,
                'sortie': Decimal('0.00'),
                'opn_no': f'RB-{remboursement.id:08d}',
                'opr': 'SYSTEM',
                'type': 'REMBOURSEMENT',
                'reference_id': remboursement.id
            })
    
    # 6. TODO: OPERATIONS de caisse liées - Réimplémenter avec Caissetypemvt
    # Les OPERATIONS sont maintenant gérées via Caissetypemvt
    # Cette section sera réimplémentée pour utiliser Caissetypemvt
    
    # Trier par date
    OPERATIONS.sort(key=lambda x: (x['date_trans'], x['date_val']))
    
    return OPERATIONS

def generate_account_statement_header(canvas_obj, doc, coop_info, numero_compte=None, intitule=None, type_titulaire=None, is_continuation=False):
    """Génère l'en-tête du relevé de compte"""
    width, height = A4  # Format PORTRAIT
    canvas_obj.saveState()
    
    # Ligne bleue horizontale en haut
    canvas_obj.setStrokeColor(BLUE_MEDIUM)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(20*mm, height - 20*mm, width - 20*mm, height - 20*mm)
    
    # Logo à droite (si disponible)
    logo_x = width - 50*mm
    logo_y = height - 35*mm
    if coop_info and coop_info.get('logo'):
        try:
            logo_path = coop_info['logo'].path
            if os.path.exists(logo_path):
                canvas_obj.drawImage(logo_path, logo_x, logo_y, width=25*mm, height=25*mm, preserveAspectRatio=True)
        except:
            pass
    
    # Nom de la coopérative en bleu - à gauche
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.setFillColor(BLUE_MEDIUM)
    nom = coop_info['nom'] if coop_info else "COOPEC"
    canvas_obj.drawString(20*mm, height - 30*mm, nom)
    
    # Sigle
    if coop_info and coop_info.get('sigle'):
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(20*mm, height - 36*mm, coop_info['sigle'])
    
    # Informations de la coopérative
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.black)
    y_pos = height - 45*mm
    
    if coop_info:
        # RCCM
        if coop_info.get('numero_rccm'):
            rccm = f"R.C.C.M.: {coop_info['numero_rccm']}"
            canvas_obj.drawString(20*mm, y_pos, rccm)
            y_pos -= 4*mm
        
        # ID National
        if coop_info.get('numero_id_nat'):
            id_nat = f"Id. Nat.: {coop_info['numero_id_nat']}"
            canvas_obj.drawString(20*mm, y_pos, id_nat)
            y_pos -= 4*mm
        
        # Pays
        if coop_info.get('pays'):
            pays = f"{coop_info['pays']}"
            canvas_obj.drawString(20*mm, y_pos, pays)
    
    # Si c'est une page de continuation, afficher les infos du compte
    if is_continuation and numero_compte and intitule:
        y_pos -= 6*mm
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.setFillColor(BLUE_MEDIUM)
        canvas_obj.drawString(20*mm, y_pos, f"N° Compte: {numero_compte} | {intitule} ({type_titulaire})")
    
    canvas_obj.restoreState()

def generate_account_statement_footer(canvas_obj, doc, total_pages=None):
    """Génère le pied de page du relevé avec pagination"""
    width, height = A4  # Format PORTRAIT
    canvas_obj.saveState()
    
    # Numéro de page
    page_num = canvas_obj.getPageNumber()
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.black)
    
    # Afficher "Page X sur Y" si total_pages est fourni, sinon juste "Page X"
    if total_pages:
        page_text = f"Page {page_num} sur {total_pages}"
    else:
        page_text = f"Page {page_num}"
    
    # Centrer le texte en bas de page
    text_width = canvas_obj.stringWidth(page_text, "Helvetica", 9)
    x_position = (width - text_width) / 2
    canvas_obj.drawString(x_position, 15*mm, page_text)
    
    canvas_obj.restoreState()

def generate_account_statement(membre_id=None, client_id=None, date_debut=None, date_fin=None):
    """
    Génère un relevé de compte PDF pour un membre ou un client
    
    Args:
        membre_id: ID du membre (optionnel)
        client_id: ID du client (optionnel)
        date_debut: Date de début (optionnel)
        date_fin: Date de fin (optionnel)
    
    Returns:
        BytesIO: Buffer contenant le PDF
    """
    # Récupérer le membre ou client
    if membre_id:
        try:
            titulaire = Membre.objects.get(id=membre_id)
            OPERATIONS = collecter_toutes_OPERATIONS_membre(titulaire, date_debut, date_fin)
            type_titulaire = 'MEMBRE'
            numero_compte = titulaire.numero_compte
            intitule = str(titulaire)
        except Membre.DoesNotExist:
            return None
    elif client_id:
        try:
            titulaire = Client.objects.get(id=client_id)
            OPERATIONS = collecter_toutes_OPERATIONS_client(titulaire, date_debut, date_fin)
            type_titulaire = 'CLIENT'
            numero_compte = titulaire.numero_compte
            intitule = str(titulaire)
        except Client.DoesNotExist:
            return None
    else:
        return None
    
    # Si pas de OPERATIONS, retourner None
    if not OPERATIONS:
        return None
    
    # Calculer le solde initial (avant la première opération)
    solde_initial = Decimal('0.00')
    
    # Calculer les soldes pour chaque opération
    solde_courant = solde_initial
    for txn in OPERATIONS:
        solde_courant = solde_courant + txn['entree'] - txn['sortie']
        txn['solde'] = solde_courant
    
    # Créer le PDF en format PORTRAIT avec marges plus grandes
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=20*mm, leftMargin=20*mm,
                          topMargin=60*mm, bottomMargin=30*mm)
    
    story = []
    styles = getSampleStyleSheet()
    coop_info = get_cooperative_info()
    
    # Titre du document
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=BLUE_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph("RELEVE DE COMPTE CLIENT", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Informations du compte
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3
    )
    
    # Période du relevé
    if date_debut and date_fin:
        periode = f"Du {date_debut.strftime('%d-%m-%Y')} au {date_fin.strftime('%d-%m-%Y')}"
    elif date_debut:
        periode = f"À partir du {date_debut.strftime('%d-%m-%Y')}"
    elif date_fin:
        periode = f"Jusqu'au {date_fin.strftime('%d-%m-%Y')}"
    else:
        periode = "Toutes les OPERATIONS"
    
    story.append(Paragraph(f"<b>Période:</b> {periode}", info_style))
    story.append(Spacer(1, 2*mm))
    
    # Informations du titulaire
    story.append(Paragraph(f"<b>N° Compte:</b> {numero_compte}", info_style))
    story.append(Paragraph(f"<b>Intitulé:</b> {intitule}", info_style))
    story.append(Paragraph(f"<b>Type:</b> {type_titulaire}", info_style))
    story.append(Spacer(1, 5*mm))
    
    # En-tête du tableau (sans OPR)
    header_data = [
        ['OPN NO', 'LIBELLE OPERATION', 'DATE TRANS', 'DATE VAL', 'ENTREES', 'SORTIES', 'SOLDE']
    ]
    
    # Données du tableau
    table_data = [header_data[0]]
    
    for txn in OPERATIONS:
        date_trans_str = txn['date_trans'].strftime('%d-%m-%Y') if isinstance(txn['date_trans'], date) else str(txn['date_trans'])
        date_val_str = txn['date_val'].strftime('%d-%m-%Y') if isinstance(txn['date_val'], date) else str(txn['date_val'])
        
        entree_str = format_currency(txn['entree']) if txn['entree'] > 0 else ''
        sortie_str = format_currency(txn['sortie']) if txn['sortie'] > 0 else ''
        solde_str = format_currency(txn['solde'])
        
        # Utiliser Paragraph pour permettre le retour à la ligne automatique
        libelle_para = Paragraph(txn['libelle'], styles['Normal'])
        
        table_data.append([
            txn['opn_no'],
            libelle_para,  # Permet le retour à la ligne automatique
            date_trans_str,
            date_val_str,
            entree_str,
            sortie_str,
            solde_str
        ])
    
    # Créer le tableau avec largeurs ajustées pour format PORTRAIT (sans OPR)
    # Calculer la largeur disponible en format portrait A4 (210mm) moins les marges (40mm total)
    # Largeur disponible: 210mm - 40mm = 170mm
    col_widths = [25*mm, 50*mm, 22*mm, 22*mm, 20*mm, 20*mm, 20*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style du tableau avec padding pour éviter les coupures
    table_style = TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_MEDIUM),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        
        # Corps du tableau
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 1), (-1, -1), 5),
        ('RIGHTPADDING', (0, 1), (-1, -1), 5),
    ])
    
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 5*mm))
    
    # Totaux
    total_entrees = sum([txn['entree'] for txn in OPERATIONS])
    total_sorties = sum([txn['sortie'] for txn in OPERATIONS])
    solde_final = OPERATIONS[-1]['solde'] if OPERATIONS else solde_initial
    
    totals_data = [
        ['TOTAL ENTREES:', format_currency(total_entrees)],
        ['TOTAL SORTIES:', format_currency(total_sorties)],
        ['SOLDE FINAL:', format_currency(solde_final)]
    ]
    
    totals_table = Table(totals_data, colWidths=[50*mm, 50*mm])
    totals_style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), BLUE_MEDIUM),
    ])
    totals_table.setStyle(totals_style)
    story.append(totals_table)
    
    # Date de génération
    story.append(Spacer(1, 5*mm))
    date_gen = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    story.append(Paragraph(f"<i>Généré le {date_gen}</i>", info_style))
    
    # Estimation du nombre de pages basée sur le nombre de OPERATIONS
    # Environ 20-25 lignes par page avec nos marges en format portrait
    estimated_pages = max(1, (len(OPERATIONS) + 15) // 20)
    
    def on_first_page(canvas_obj, doc):
        generate_account_statement_header(canvas_obj, doc, coop_info, numero_compte, intitule, type_titulaire, False)
        # Utiliser l'estimation pour afficher "Page X sur Y"
        generate_account_statement_footer(canvas_obj, doc, estimated_pages)
    
    def on_later_pages(canvas_obj, doc):
        generate_account_statement_header(canvas_obj, doc, coop_info, numero_compte, intitule, type_titulaire, True)
        generate_account_statement_footer(canvas_obj, doc, estimated_pages)
    
    # Construire le PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return buffer
