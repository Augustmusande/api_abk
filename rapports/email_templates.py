"""
Templates HTML pour les emails de reçus
"""
from django.template.loader import render_to_string
from users.models import Cooperative


def get_email_template_context():
    """Récupère le contexte commun pour tous les templates d'email"""
    coop = Cooperative.objects.first()
    return {
        'coop_nom': coop.nom if coop else 'COOPEC',
        'coop_sigle': coop.sigle if coop else '',
        'coop_email': coop.email if coop else '',
        'coop_telephone': coop.telephone if coop else '',
        'coop_site_web': coop.site_web if coop else '',
        'coop_logo_url': coop.logo.url if coop and coop.logo else None,
    }


def get_email_template_depot_epargne(donnat_epargne, titulaire):
    """Template HTML pour l'email de dépôt d'épargne"""
    context = get_email_template_context()
    context.update({
        'titulaire_nom': str(titulaire),
        'montant': donnat_epargne.montant,
        'mois': donnat_epargne.mois,
        'designation': donnat_epargne.souscriptEpargne.designation,
        'total_depots': donnat_epargne.souscriptEpargne.total_donne,
        'type_operation': 'Dépôt d\'épargne',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Merci pour votre dépôt d'épargne !</h2>
        
        <p>Bonjour <strong>{context['titulaire_nom']}</strong>,</p>
        
        <p>Nous vous remercions pour votre dépôt d'épargne effectué avec succès.</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Montant déposé :</strong> {context['montant']:,.2f} USD</p>
            <p><strong>Mois :</strong> {context['mois']}</p>
            <p><strong>Désignation :</strong> {context['designation']}</p>
            <p><strong>Total des dépôts :</strong> {context['total_depots']:,.2f} USD</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous vous remercions de votre confiance et restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""


def get_email_template_versement_part_sociale(donnat_part, membre):
    """Template HTML pour l'email de versement de part sociale"""
    context = get_email_template_context()
    context.update({
        'membre_nom': str(membre),
        'montant': donnat_part.montant,
        'mois': donnat_part.mois,
        'part_sociale': donnat_part.souscription_part_social.partSocial.annee,
        'total_verse': donnat_part.souscription_part_social.montant_total_verse,
        'type_operation': 'Versement de part sociale',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Merci pour votre versement de part sociale !</h2>
        
        <p>Bonjour <strong>{context['membre_nom']}</strong>,</p>
        
        <p>Nous vous remercions pour votre versement de part sociale effectué avec succès.</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Montant versé :</strong> {context['montant']:,.2f} USD</p>
            <p><strong>Mois :</strong> {context['mois']}</p>
            <p><strong>Part sociale :</strong> {context['part_sociale']}</p>
            <p><strong>Total versé :</strong> {context['total_verse']:,.2f} USD</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous vous remercions de votre confiance et restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""


def get_email_template_retrait(retrait, titulaire):
    """Template HTML pour l'email de retrait"""
    context = get_email_template_context()
    context.update({
        'titulaire_nom': str(titulaire),
        'montant': retrait.montant,
        'designation': retrait.souscriptEpargne.designation,
        'solde_restant': retrait.souscriptEpargne.solde_epargne,
        'motif': retrait.motif or 'Non spécifié',
        'type_operation': 'Retrait',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Confirmation de votre retrait</h2>
        
        <p>Bonjour <strong>{context['titulaire_nom']}</strong>,</p>
        
        <p>Votre demande de retrait a été traitée avec succès.</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Montant retiré :</strong> {context['montant']:,.2f} USD</p>
            <p><strong>Désignation :</strong> {context['designation']}</p>
            <p><strong>Motif :</strong> {context['motif']}</p>
            <p><strong>Solde restant :</strong> {context['solde_restant']:,.2f} USD</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""


def get_email_template_credit(credit, titulaire):
    """Template HTML pour l'email d'octroi de crédit"""
    context = get_email_template_context()
    context.update({
        'titulaire_nom': str(titulaire),
        'montant': credit.montant,
        'taux_interet': credit.taux_interet,
        'interet': credit.interet,
        'duree': credit.duree,
        'duree_type': credit.get_duree_type_display(),
        'date_fin': credit.date_fin.strftime("%d/%m/%Y") if credit.date_fin else '',
        'solde_restant': credit.solde_restant,
        'type_operation': 'Octroi de crédit',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Félicitations ! Votre crédit a été octroyé</h2>
        
        <p>Bonjour <strong>{context['titulaire_nom']}</strong>,</p>
        
        <p>Nous avons le plaisir de vous informer que votre demande de crédit a été approuvée et octroyée avec succès.</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Montant du crédit :</strong> {context['montant']:,.2f} USD</p>
            <p><strong>Taux d'intérêt :</strong> {context['taux_interet']}%</p>
            <p><strong>Intérêt total :</strong> {context['interet']:,.2f} USD</p>
            <p><strong>Durée :</strong> {context['duree']} {context['duree_type']}</p>
            <p><strong>Date de fin prévue :</strong> {context['date_fin']}</p>
            <p><strong>Solde restant :</strong> {context['solde_restant']:,.2f} USD</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous vous remercions de votre confiance et restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""


def get_email_template_remboursement(remboursement, titulaire):
    """Template HTML pour l'email de remboursement"""
    context = get_email_template_context()
    credit = remboursement.credit
    context.update({
        'titulaire_nom': str(titulaire),
        'montant_rembourse': remboursement.montant,
        'credit_id': credit.id,
        'solde_restant': credit.solde_restant,
        'type_operation': 'Remboursement de crédit',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Merci pour votre remboursement !</h2>
        
        <p>Bonjour <strong>{context['titulaire_nom']}</strong>,</p>
        
        <p>Nous vous remercions pour votre remboursement effectué avec succès.</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Montant remboursé :</strong> {context['montant_rembourse']:,.2f} USD</p>
            <p><strong>Crédit N° :</strong> {context['credit_id']}</p>
            <p><strong>Solde restant :</strong> {context['solde_restant']:,.2f} USD</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous vous remercions de votre confiance et restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""


def get_email_template_frais_adhesion(frais_adhesion, titulaire):
    """Template HTML pour l'email de paiement de frais d'adhésion"""
    context = get_email_template_context()
    
    # Déterminer le type de titulaire
    if frais_adhesion.titulaire_membre:
        type_titulaire = 'Membre'
    else:
        type_titulaire = 'Client'
    
    context.update({
        'titulaire_nom': str(titulaire),
        'type_titulaire': type_titulaire,
        'montant': frais_adhesion.montant,
        'date_paiement': frais_adhesion.date_paiement.strftime("%d/%m/%Y") if hasattr(frais_adhesion.date_paiement, 'strftime') else str(frais_adhesion.date_paiement),
        'type_operation': 'Paiement de frais d\'adhésion',
    })
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #2E5C8A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header img {{
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
        }}
        .header h1 {{
            margin: 10px 0;
            font-size: 24px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #4A90E2;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: #2E5C8A;
        }}
        .footer {{
            background: #2E5C8A;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="' + context['coop_logo_url'] + '" alt="Logo">' if context['coop_logo_url'] else ''}
        <h1>{context['coop_nom']}</h1>
        {('<p>' + context['coop_sigle'] + '</p>') if context['coop_sigle'] else ''}
    </div>
    
    <div class="content">
        <h2 style="color: #2E5C8A;">Bienvenue ! Votre adhésion a été confirmée</h2>
        
        <p>Bonjour <strong>{context['titulaire_nom']}</strong>,</p>
        
        <p>Nous avons le plaisir de vous confirmer que votre paiement de frais d'adhésion a été enregistré avec succès. Bienvenue dans notre coopérative !</p>
        
        <div class="info-box">
            <p><strong>Type d'opération :</strong> {context['type_operation']}</p>
            <p><strong>Type de titulaire :</strong> {context['type_titulaire']}</p>
            <p><strong>Montant payé :</strong> {context['montant']:,.2f} USD</p>
            <p><strong>Date de paiement :</strong> {context['date_paiement']}</p>
        </div>
        
        <p>Votre reçu PDF est disponible en pièce jointe. Vous pouvez également le télécharger directement depuis votre espace membre.</p>
        
        <p>Nous vous remercions de votre confiance et restons à votre disposition pour toute question.</p>
        
        <p>Cordialement,<br>
        <strong>L'équipe {context['coop_nom']}</strong></p>
    </div>
    
    <div class="footer">
        <p><strong>{context['coop_nom']}</strong></p>
        {('<p>Tél: ' + context['coop_telephone'] + '</p>') if context['coop_telephone'] else ''}
        {('<p>Email: ' + context['coop_email'] + '</p>') if context['coop_email'] else ''}
        {('<p>Site web: ' + context['coop_site_web'] + '</p>') if context['coop_site_web'] else ''}
        <p>&copy; {context['coop_nom']} - Tous droits réservés</p>
    </div>
</body>
</html>
"""
