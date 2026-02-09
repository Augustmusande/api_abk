"""
SERVICES - CALCULS FINANCIERS POUR LA CAISSE

Tous les calculs financiers (intérêts, frais de gestion, répartition aux membres, etc.)
"""

from decimal import Decimal
from datetime import date, datetime
from credits.models import Credit
from membres.models import SouscriptionPartSocial, DonnatPartSocial, Compte, DonnatEpargne, SouscriptEpargne, Retrait
from users.models import Membre, Client

def calculer_interet_credit(credit):
    """
    Calcule l'intérêt d'un crédit.
    Formule : interet = (montant * taux_interet) / 100
    
    Cette formule est la même pour les deux méthodes (PRECOMPTE et POSTCOMPTE).
    La différence réside dans le moment où l'intérêt est prélevé :
    - PRECOMPTE : l'intérêt est déduit du montant versé (coupé à la source, méthode par défaut)
    - POSTCOMPTE : l'intérêt n'est pas déduit du montant versé (compté à l'échéance)
    
    Args:
        credit (Credit): Le crédit concerné
    
    Returns:
        Decimal: Montant des intérêts calculés
    """
    return (credit.montant * credit.taux_interet) / Decimal('100')

def calculer_interets_tous_credits():
    """
    Calcule les intérêts de tous les crédits.
    
    Returns:
        dict: Dictionnaire avec les résultats des calculs
    """
    # Utiliser only() pour ne récupérer que les champs nécessaires et éviter les erreurs de champs inexistants
    # Cela évite que Django essaie d'accéder à des champs qui n'existent pas dans la base de données
    credits = Credit.objects.only('id', 'montant', 'taux_interet', 'membre_id', 'client_id').select_related('membre', 'client')
    
    # Intérêts par crédit
    interets_par_credit = []
    for credit in credits:
        interet = calculer_interet_credit(credit)
        interets_par_credit.append({
            'credit_id': credit.id,
            'montant': float(credit.montant),
            'taux_interet': float(credit.taux_interet),
            'interet': float(interet),
            'membre': credit.membre.numero_compte if credit.membre else None,
            'client': credit.client.numero_compte if credit.client else None
        })
    
    # Intérêts par membre
    interets_par_membre = {}
    for credit in credits:
        if credit.membre:
            membre_id = credit.membre.id
            membre_numero = credit.membre.numero_compte
            # Gérer le nom selon le type de membre (physique ou morale)
            if credit.membre.type_membre == 'MORALE':
                membre_nom = credit.membre.raison_sociale or credit.membre.sigle or 'Entreprise'
            else:
                membre_nom = f"{credit.membre.nom or ''} {credit.membre.prenom or ''}".strip() or 'Personne physique'
            
            if membre_id not in interets_par_membre:
                interets_par_membre[membre_id] = {
                    'membre_id': membre_id,
                    'membre_numero': membre_numero,
                    'membre_nom': membre_nom,
                    'interet_total': Decimal('0.00'),
                    'nombre_credits': 0
                }
            
            interet = calculer_interet_credit(credit)
            interets_par_membre[membre_id]['interet_total'] += interet
            interets_par_membre[membre_id]['nombre_credits'] += 1
    
    # Convertir en liste
    interets_par_membre_list = []
    for membre_id, data in interets_par_membre.items():
        interets_par_membre_list.append({
            'membre_id': data['membre_id'],
            'membre_numero': data['membre_numero'],
            'membre_nom': data['membre_nom'],
            'interet_total': float(data['interet_total']),
            'nombre_credits': data['nombre_credits']
        })
    
    # Intérêt total global - utiliser la même queryset pour éviter les problèmes
    interet_total_global = sum([calculer_interet_credit(credit) for credit in credits])
    
    return {
        'interets_par_credit': interets_par_credit,
        'interets_par_membre': interets_par_membre_list,
        'interet_total_global': float(interet_total_global),
        'nombre_credits': credits.count()
    }

def calculer_frais_gestion(pourcentage=20, periode_annee=None):
    """
    Calcule les frais de gestion sur l'intérêt total global + les frais d'adhésion.
    Formule : frais_gestion = (interet_total_global * pourcentage) / 100 + total_frais_adhesion
    
    IMPORTANT ABK : 
    - Les frais de gestion sont calculés sur l'intérêt total global (20% par défaut)
    - TOUS les frais d'adhésion sont ajoutés aux frais de gestion
    - Les frais de gestion sont un résultat de calcul, jamais stockés
    - Pas de création de Caissetypemvt (les frais de gestion ne sont pas tracés)
    - Utilisé uniquement pour la répartition des intérêts aux membres
    
    Args:
        pourcentage (float): Pourcentage des frais de gestion (défaut: 20%)
        periode_annee (int, optionnel): Année pour filtrer les frais d'adhésion
    
    Returns:
        dict: Dictionnaire avec les résultats des calculs
    """
    from membres.models import FraisAdhesion
    
    # Calculer d'abord les intérêts totaux
    resultats_interets = calculer_interets_tous_credits()
    interet_total_global = Decimal(str(resultats_interets['interet_total_global']))
    
    # Calculer les frais de gestion sur l'intérêt total global
    frais_gestion_interets = (interet_total_global * Decimal(str(pourcentage))) / Decimal('100')
    
    # Calculer le total des frais d'adhésion
    # IMPORTANT : Tous les frais d'adhésion font partie des frais de gestion
    frais_adhesion_query = FraisAdhesion.objects.all()
    if periode_annee:
        frais_adhesion_query = frais_adhesion_query.filter(date_paiement__year=periode_annee)
    
    total_frais_adhesion = Decimal('0.00')
    for frais_adhesion in frais_adhesion_query:
        total_frais_adhesion += Decimal(str(frais_adhesion.montant))
    
    # Le total des frais de gestion = frais de gestion sur intérêts + frais d'adhésion
    frais_gestion_total = frais_gestion_interets + total_frais_adhesion
    
    # Répartir les frais de gestion proportionnellement aux intérêts de chaque membre
    frais_par_membre = []
    for membre_data in resultats_interets['interets_par_membre']:
        interet_membre = Decimal(str(membre_data['interet_total']))
        
        # Si l'intérêt total global est 0, pas de répartition
        if interet_total_global == 0:
            proportion = Decimal('0.00')
        else:
            proportion = interet_membre / interet_total_global
        
        frais_membre = frais_gestion_total * proportion
        
        frais_par_membre.append({
            'membre_id': membre_data['membre_id'],
            'membre_numero': membre_data['membre_numero'],
            'membre_nom': membre_data['membre_nom'],
            'interet_total': membre_data['interet_total'],
            'frais_gestion': float(frais_membre),  # Ajout du champ frais_gestion calculé
            'proportion': float(proportion),
            'nombre_credits': membre_data['nombre_credits']
        })
    
    # IMPORTANT ABK : Les frais de gestion sont un résultat de calcul, jamais stockés.
    # Pas de création de Caissetypemvt (les frais de gestion ne sont pas tracés).
    # Utilisé uniquement pour la répartition des intérêts aux membres.
    
    # Calculer les frais de gestion disponibles (après soustraction des dépenses)
    from caisse.models import Depenses
    total_depenses_existantes = Decimal('0.00')
    for depense in Depenses.objects.all():
        total_depenses_existantes += Decimal(str(depense.pt))
    
    frais_gestion_disponible = frais_gestion_total - total_depenses_existantes
    if frais_gestion_disponible < 0:
        frais_gestion_disponible = Decimal('0.00')
    
    return {
        'pourcentage_utilise': pourcentage,
        'interet_total_global': resultats_interets['interet_total_global'],
        'frais_gestion_total_global': float(frais_gestion_total),
        'frais_gestion_interets': float(frais_gestion_interets),  # Frais de gestion calculés sur les intérêts
        'total_frais_adhesion': float(total_frais_adhesion),  # Total des frais d'adhésion inclus
        'total_depenses': float(total_depenses_existantes),  # Total des dépenses existantes
        'frais_gestion_disponible': float(frais_gestion_disponible),  # Frais de gestion disponibles (après dépenses)
        'frais_par_membre': frais_par_membre,
        'nombre_credits': resultats_interets['nombre_credits']
    }

# ============================================================================
# SERVICE 2.5 : CALCUL DU SOLDE DISPONIBLE PAR TYPE DE CAISSE (POUR CRÉDITS ET RETRAITS)
# ============================================================================

def calculer_solde_caissetype_disponible(caissetype):
    """
    Calcule le solde disponible dans un type de caisse spécifique.
    Utilisé pour les crédits et les retraits.
    
    IMPORTANT : 
    - Utilise la même logique que calculer_totaux() dans CaisseTypeViewSet
    - Calcule total_montant = total_entrees - total_sorties basé sur Caissetypemvt
    - Inclut TOUTES les entrées (remboursements, donations, frais d'adhésion, remboursements, donations, frais d'adhésion)
    - Soustrait TOUTES les sorties (dépenses, retraits)
    - Ne soustrait PAS les crédits actifs (ils sont déjà comptabilisés dans les sorties via Caissetypemvt)
    
    Args:
        caissetype: Instance de CaisseType
        
    Returns:
        dict: {
            'solde_disponible': Decimal,  # Solde disponible (total_montant)
            'total_entrees': Decimal,     # Total des entrées
            'total_sorties': Decimal,     # Total des sorties
        }
    """
    from caisse.models import Caissetypemvt
    
    # Récupérer tous les mouvements pour ce type de caisse
    mouvements = Caissetypemvt.objects.filter(caissetype=caissetype)
    
    # Calculer le total en additionnant/soustrayant les montants selon le type
    total_montant = Decimal('0.00')
    total_entrees = Decimal('0.00')
    total_sorties = Decimal('0.00')
    
    for mouvement in mouvements:
                # Les opérations sont maintenant gérées via Caissetypemvt directement
        
        # Remboursement - toujours ajouter (entrée d'argent)
        if mouvement.remboursement:
            montant_remb = Decimal(str(mouvement.remboursement.montant))
            total_montant += montant_remb
            total_entrees += montant_remb
        
        # Donation épargne - toujours ajouter (entrée d'argent)
        if mouvement.donnatepargne:
            montant_epargne = Decimal(str(mouvement.donnatepargne.montant))
            total_montant += montant_epargne
            total_entrees += montant_epargne
        
        # Donation part sociale - toujours ajouter (entrée d'argent)
        if mouvement.donnatpartsocial:
            montant_part = Decimal(str(mouvement.donnatpartsocial.montant))
            total_montant += montant_part
            total_entrees += montant_part
        
        # Frais d'adhésion - toujours ajouter (entrée d'argent)
        if mouvement.fraisadhesion:
            montant_frais = Decimal(str(mouvement.fraisadhesion.montant))
            total_montant += montant_frais
            total_entrees += montant_frais
        
        # Dépense - toujours soustraire (sortie d'argent)
        if mouvement.depense:
            montant_depense = Decimal(str(mouvement.depense.pt))  # Utiliser la propriété pt (prix total)
            total_montant -= montant_depense
            total_sorties += montant_depense
        
        # Retrait - toujours soustraire (sortie d'argent)
        if mouvement.retrait:
            montant_retrait = Decimal(str(mouvement.retrait.montant))
            total_montant -= montant_retrait
            total_sorties += montant_retrait
        
        # Don direct - toujours ajouter (entrée d'argent)
        if mouvement.dondirect:
            montant_don = Decimal(str(mouvement.dondirect.montant))
            total_montant += montant_don
            total_entrees += montant_don
        
        # Crédit - toujours soustraire (sortie d'argent)
        # IMPORTANT : Le montant soustrait dépend de la méthode d'intérêt :
        # - PRECOMPTE : on soustrait montant_effectif (montant - intérêt) car c'est ce qui est réellement sorti
        # - POSTCOMPTE : on soustrait montant (montant demandé) car c'est ce qui est réellement sorti
        if mouvement.credit:
            if mouvement.credit.methode_interet == 'PRECOMPTE':
                # Pour PRECOMPTE : montant effectivement sorti = montant - intérêt
                montant_credit = Decimal(str(mouvement.credit.montant_effectif))
            else:  # POSTCOMPTE
                # Pour POSTCOMPTE : montant effectivement sorti = montant demandé
                montant_credit = Decimal(str(mouvement.credit.montant))
            total_montant -= montant_credit
            total_sorties += montant_credit
    
    # Le solde disponible est le total_montant (total_entrees - total_sorties)
    solde_disponible = total_montant
    
    # S'assurer que le solde ne soit pas négatif
    if solde_disponible < 0:
        solde_disponible = Decimal('0.00')
    
    return {
        'solde_disponible': solde_disponible,
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
    }

# ============================================================================
# SERVICE 3 : CALCUL DES APPORTS DES MEMBRES (PARTS SOCIALES + ÉPARGNES BLOQUÉES)
# ============================================================================

def calculer_apports_membre(membre, periode_mois=None, periode_annee=None):
    """
    Calcule les apports d'un membre (parts sociales + épargnes bloquées + comptes en vue).
    
    IMPORTANT : 
    - Les épargnes de type "BLOQUE" sont prises en compte via les donations d'épargne
    - Les comptes en vue (VUE) sont pris en compte via les mouvements de type DEPOT
    
    Args:
        membre (Membre): Le membre concerné
        periode_mois (int, optional): Mois pour filtrer (1-12)
        periode_annee (int, optional): Année pour filtrer
    
    Returns:
        dict: Dictionnaire avec les apports calculés
    """
    # Mapping des mois
    MOIS_MAPPING = {
        1: 'JANVIER', 2: 'FEVRIER', 3: 'MARS', 4: 'AVRIL',
        5: 'MAI', 6: 'JUIN', 7: 'JUILLET', 8: 'AOUT',
        9: 'SEPTEMBRE', 10: 'OCTOBRE', 11: 'NOVEMBRE', 12: 'DECEMBRE'
    }
    
    # === CALCULER LES PARTS SOCIALES ===
    montant_parts_sociales = Decimal('0.00')
    
    # Récupérer toutes les souscriptions de parts sociales du membre
    souscriptions = SouscriptionPartSocial.objects.filter(membre=membre)
    
    for souscription in souscriptions:
        # Filtrer par période si spécifiée
        if periode_mois and periode_annee:
            # Récupérer les donations du mois/année spécifiés
            mois_nom = MOIS_MAPPING.get(periode_mois)
            if mois_nom:
                donations = DonnatPartSocial.objects.filter(
                    souscription_part_social=souscription,
                    mois=mois_nom,
                    date_donnat__year=periode_annee
                )
                montant_parts_sociales += sum([d.montant for d in donations])
        else:
            # Toutes les donations (cumul depuis le début)
            montant_parts_sociales += souscription.montant_total_verse
    
    # === CALCULER LES ÉPARGNES BLOQUÉES (UNIQUEMENT TYPE BLOQUE) ===
    montant_epargnes_bloquees = Decimal('0.00')
    
    # Récupérer les comptes bloqués du membre
    comptes_bloques = Compte.objects.filter(
        titulaire_membre=membre,
        type_compte='BLOQUE'
    )
    
    for compte in comptes_bloques:
        # Récupérer les souscriptions d'épargne sur ce compte
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription_epargne in souscriptions_epargne:
            # Filtrer par période si spécifiée
            if periode_mois and periode_annee:
                # Récupérer les donations du mois spécifié
                mois_nom = MOIS_MAPPING.get(periode_mois)
                if mois_nom:
                    donations = DonnatEpargne.objects.filter(
                        souscriptEpargne=souscription_epargne,
                        mois=mois_nom
                    )
                    # Filtrer par année : on utilise la date de souscription de l'épargne
                    if souscription_epargne.date_souscription.year == periode_annee:
                        montant_dons = sum([d.montant for d in donations])
                        # Soustraire les retraits de la période
                        retraits = Retrait.objects.filter(
                            souscriptEpargne=souscription_epargne,
                            date_operation__month=periode_mois,
                            date_operation__year=periode_annee
                        )
                        montant_retraits = sum([r.montant for r in retraits])
                        montant_epargnes_bloquees += montant_dons - montant_retraits
                    # Si l'année ne correspond pas, on n'ajoute rien (0 pour cette période)
            elif periode_annee:
                # Si seulement l'année est fournie, sommer tous les mois de l'année
                for month_num in range(1, 13):
                    mois_nom = MOIS_MAPPING.get(month_num)
                    if mois_nom:
                        donations = DonnatEpargne.objects.filter(
                            souscriptEpargne=souscription_epargne,
                            mois=mois_nom
                        )
                        if souscription_epargne.date_souscription.year == periode_annee:
                            montant_dons = sum([d.montant for d in donations])
                            # Soustraire les retraits du mois
                            retraits = Retrait.objects.filter(
                                souscriptEpargne=souscription_epargne,
                                date_operation__month=month_num,
                                date_operation__year=periode_annee
                            )
                            montant_retraits = sum([r.montant for r in retraits])
                            montant_epargnes_bloquees += montant_dons - montant_retraits
            else:
                # Toutes les donations (cumul depuis le début) - utiliser solde_epargne
                montant_epargnes_bloquees += souscription_epargne.solde_epargne
    
    # === CALCULER LES COMPTES EN VUE (TYPE VUE) ===
    montant_comptes_vue = Decimal('0.00')
    
    # Récupérer les comptes en vue du membre
    comptes_vue = Compte.objects.filter(
        titulaire_membre=membre,
        type_compte='VUE'
    )
    
    # Calculer les épargnes sur comptes VUE (via DonnatEpargne)
    for compte in comptes_vue:
        # Récupérer les souscriptions d'épargne sur ce compte
        souscriptions_epargne = SouscriptEpargne.objects.filter(compte=compte)
        
        for souscription_epargne in souscriptions_epargne:
            # Filtrer par période si spécifiée
            if periode_mois and periode_annee:
                # Récupérer les donations du mois spécifié
                mois_nom = MOIS_MAPPING.get(periode_mois)
                if mois_nom:
                    donations = DonnatEpargne.objects.filter(
                        souscriptEpargne=souscription_epargne,
                        mois=mois_nom
                    )
                    # Filtrer par année : on utilise la date de souscription de l'épargne
                    if souscription_epargne.date_souscription.year == periode_annee:
                        montant_dons = sum([d.montant for d in donations])
                        # Soustraire les retraits de la période
                        retraits = Retrait.objects.filter(
                            souscriptEpargne=souscription_epargne,
                            date_operation__month=periode_mois,
                            date_operation__year=periode_annee
                        )
                        montant_retraits = sum([r.montant for r in retraits])
                        montant_comptes_vue += montant_dons - montant_retraits
                    # Si l'année ne correspond pas, on n'ajoute rien (0 pour cette période)
            elif periode_annee:
                # Si seulement l'année est fournie, sommer tous les mois de l'année
                for month_num in range(1, 13):
                    mois_nom = MOIS_MAPPING.get(month_num)
                    if mois_nom:
                        donations = DonnatEpargne.objects.filter(
                            souscriptEpargne=souscription_epargne,
                            mois=mois_nom
                        )
                        if souscription_epargne.date_souscription.year == periode_annee:
                            montant_dons = sum([d.montant for d in donations])
                            # Soustraire les retraits du mois
                            retraits = Retrait.objects.filter(
                                souscriptEpargne=souscription_epargne,
                                date_operation__month=month_num,
                                date_operation__year=periode_annee
                            )
                            montant_retraits = sum([r.montant for r in retraits])
                            montant_comptes_vue += montant_dons - montant_retraits
            else:
                # Toutes les donations (cumul depuis le début) - utiliser solde_epargne
                montant_comptes_vue += souscription_epargne.solde_epargne
    
    # Note: Les dépôts directs sur comptes VUE (sans souscription d'épargne) 
    # sont gérés via DonnatEpargne liés à des souscriptions d'épargne.
    # Le modèle Mouvement a été supprimé, donc on ne calcule que les épargnes via DonnatEpargne.
    
    # === CALCULER LES CRÉDITS ACTIFS DU MEMBRE ===
    # Les crédits actifs (EN_COURS ou ECHEANCE_DEPASSEE) représentent l'argent prêté
    # On soustrait le solde_restant (argent encore dû) des apports
    credits_actifs = Credit.objects.filter(
        membre=membre,
        statut__in=['EN_COURS', 'ECHEANCE_DEPASSEE']
    )
    total_credits_actifs = sum([c.solde_restant for c in credits_actifs])
    
    # Calculer le total des apports bruts
    total_apports_bruts = montant_parts_sociales + montant_epargnes_bloquees + montant_comptes_vue
    
    # Soustraire les crédits actifs pour obtenir l'argent disponible
    total_apports = max(Decimal('0.00'), total_apports_bruts - total_credits_actifs)
    
    # Gérer le nom selon le type de membre (physique ou morale)
    if membre.type_membre == 'MORALE':
        membre_nom = membre.raison_sociale or membre.sigle or 'Entreprise'
    else:
        membre_nom = f"{membre.nom or ''} {membre.prenom or ''}".strip() or 'Personne physique'
    
    return {
        'membre_id': membre.id,
        'membre_numero': membre.numero_compte,
        'membre_nom': membre_nom,
        'montant_parts_sociales': float(montant_parts_sociales),
        'montant_epargnes_bloquees': float(montant_epargnes_bloquees),
        'montant_comptes_vue': float(montant_comptes_vue),
        'total_credits_actifs': float(total_credits_actifs),
        'total_apports': float(total_apports)
    }

def calculer_apports_tous_membres(periode_mois=None, periode_annee=None):
    """
    Calcule les apports de tous les membres ayant des apports (épargnes, parts sociales).
    
    IMPORTANT : 
    - Inclut TOUS les membres qui ont des apports, même s'ils ne sont pas encore actifs.
    - Si une période est spécifiée, seuls les apports de cette période sont comptés.
    - Si un membre n'a pas d'apports dans cette période, il n'apparaît pas dans les résultats.
    - Le total_apports_global représente l'argent disponible dans la caisse après avoir soustrait
      les crédits actifs (EN_COURS ou ECHEANCE_DEPASSEE). C'est l'argent disponible pour prêter.
    
    Args:
        periode_mois (int, optional): Mois pour filtrer (1-12)
        periode_annee (int, optional): Année pour filtrer
    
    Returns:
        dict: Dictionnaire avec les apports de tous les membres et les totaux, incluant:
            - total_apports_global: Apports bruts - crédits actifs (argent disponible)
            - total_credits_actifs: Total des crédits actifs (argent prêté)
    """
    # Inclure tous les membres qui ont des apports (épargnes, parts sociales)
    # même s'ils ne sont pas encore actifs, car l'argent est dans la caisse
    membres_actifs = Membre.objects.all()
    
    apports_par_membre = []
    total_parts_sociales = Decimal('0.00')
    total_epargnes_bloquees = Decimal('0.00')
    total_comptes_vue = Decimal('0.00')
    
    for membre in membres_actifs:
        # Calculer les apports du membre pour la période spécifiée
        # Si période spécifiée et membre n'a pas donné dans cette période, apports = 0
        apports = calculer_apports_membre(membre, periode_mois, periode_annee)
        
        # Calculer le total des apports du membre
        total_apports_membre = (
            apports['montant_parts_sociales'] + 
            apports['montant_epargnes_bloquees'] + 
            apports.get('montant_comptes_vue', 0)
        )
        
        # Si une période est spécifiée et que le membre n'a aucun apport dans cette période,
        # on ne l'inclut pas dans les résultats
        if periode_mois is not None or periode_annee is not None:
            if total_apports_membre == 0:
                # Ne pas inclure ce membre s'il n'a pas d'apports dans la période
                continue
        else:
            # Même sans période, ne pas inclure les membres qui n'ont aucun apport
            if total_apports_membre == 0:
                continue
        
        # Ajouter le membre avec ses apports
        apports_par_membre.append(apports)
        
        total_parts_sociales += Decimal(str(apports['montant_parts_sociales']))
        total_epargnes_bloquees += Decimal(str(apports['montant_epargnes_bloquees']))
        total_comptes_vue += Decimal(str(apports.get('montant_comptes_vue', 0)))
    
    # Calculer le total des apports bruts
    total_apports_bruts = total_parts_sociales + total_epargnes_bloquees + total_comptes_vue
    
    # Calculer le total des crédits actifs (EN_COURS ou ECHEANCE_DEPASSEE)
    # Ce sont les crédits qui représentent de l'argent prêté et non encore remboursé
    # IMPORTANT : Le montant soustrait dépend de la méthode d'intérêt :
    # - PRECOMPTE : on soustrait montant_effectif (montant - interet) car c'est ce qui est réellement sorti
    # - POSTCOMPTE : on soustrait montant (montant emprunté) car c'est ce qui est réellement sorti
    credits_actifs = Credit.objects.filter(
        statut__in=['EN_COURS', 'ECHEANCE_DEPASSEE']
    )
    total_credits_actifs = Decimal('0.00')
    for credit in credits_actifs:
        if credit.methode_interet == 'PRECOMPTE':
            # Pour PRECOMPTE : on soustrait montant_effectif (montant - interet)
            total_credits_actifs += credit.montant_effectif
        else:  # POSTCOMPTE
            # Pour POSTCOMPTE : on soustrait montant (montant emprunté)
            total_credits_actifs += credit.montant
    
    # Le total_apports_global représente l'argent disponible dans la caisse
    # après avoir soustrait les crédits actifs (argent prêté)
    total_apports_global = total_apports_bruts - total_credits_actifs
    
    # S'assurer que le total ne soit pas négatif
    if total_apports_global < 0:
        total_apports_global = Decimal('0.00')
    
    return {
        'apports_par_membre': apports_par_membre,
        'total_parts_sociales': float(total_parts_sociales),
        'total_epargnes_bloquees': float(total_epargnes_bloquees),
        'total_comptes_vue': float(total_comptes_vue),
        'total_apports_global': float(total_apports_global),
        'total_credits_actifs': float(total_credits_actifs),
        'periode_mois': periode_mois,
        'periode_annee': periode_annee
    }

# ============================================================================
# SERVICE 4 : RÉPARTITION DES INTÉRÊTS AUX MEMBRES
# ============================================================================

def repartir_interets_aux_membres(pourcentage_frais_gestion=20, periode_mois=None, periode_annee=None):
    """
    Répartit les intérêts aux membres selon leurs apports (parts sociales + épargnes bloquées).
    
    Formule :
    - proportion = (PartSocial_membre + epargne_bloquee_membre) / (PartSocialTotal + epargne_bloqueeTotal)
    - interet_membre = interet_net_a_repartir * proportion
    
    Où :
    - interet_net_a_repartir = interet_total_global - frais_gestion_total_global
    
    IMPORTANT : 
    - Les intérêts et frais de gestion sont calculés globalement (tous les crédits)
    - Les apports des membres sont filtrés par période (mois/année) pour la répartition
    - Si periode_mois n'est pas spécifié mais periode_annee l'est, calcule le total de toute l'année
    - Si un membre n'a pas d'apports dans la période, il aura 0 comme apports et proportion
    
    Args:
        pourcentage_frais_gestion (float): Pourcentage des frais de gestion (défaut: 20%)
        periode_mois (int, optional): Mois pour filtrer les apports (1-12). Si None et periode_annee spécifié, calcule le total annuel.
        periode_annee (int, optional): Année pour filtrer les apports
    
    Returns:
        dict: Dictionnaire avec la répartition complète
    """
    # Si aucune période n'est spécifiée, utiliser le mois et l'année courants
    from datetime import date
    if periode_mois is None and periode_annee is None:
        aujourd_hui = date.today()
        periode_mois = aujourd_hui.month
        periode_annee = aujourd_hui.year
    elif periode_annee is None:
        aujourd_hui = date.today()
        periode_annee = aujourd_hui.year
    
    # 1. Calculer les intérêts et frais de gestion (globaux - tous les crédits)
    resultats_interets = calculer_interets_tous_credits()
    resultats_frais = calculer_frais_gestion(pourcentage_frais_gestion)
    
    interet_total_global = Decimal(str(resultats_interets['interet_total_global']))
    frais_gestion_total_global = Decimal(str(resultats_frais['frais_gestion_total_global']))
    interet_net_a_repartir = interet_total_global - frais_gestion_total_global
    
    # 2. Calculer les apports de tous les membres
    # Si periode_mois est None mais periode_annee est spécifié, calculer le total de toute l'année
    if periode_mois is None and periode_annee is not None:
        # Calculer la somme de tous les mois de l'année
        apports_par_membre_annuel = {}
        total_parts_sociales_annuel = Decimal('0.00')
        total_epargnes_bloquees_annuel = Decimal('0.00')
        total_comptes_vue_annuel = Decimal('0.00')
        
        for mois in range(1, 13):
            apports_mois = calculer_apports_tous_membres(mois, periode_annee)
            
            for membre_apports in apports_mois['apports_par_membre']:
                membre_id = membre_apports['membre_id']
                
                if membre_id not in apports_par_membre_annuel:
                    apports_par_membre_annuel[membre_id] = {
                        'membre_id': membre_apports['membre_id'],
                        'membre_numero': membre_apports['membre_numero'],
                        'membre_nom': membre_apports['membre_nom'],
                        'montant_parts_sociales': Decimal('0.00'),
                        'montant_epargnes_bloquees': Decimal('0.00'),
                        'montant_comptes_vue': Decimal('0.00'),
                        'total_apports': Decimal('0.00')
                    }
                
                apports_par_membre_annuel[membre_id]['montant_parts_sociales'] += Decimal(str(membre_apports['montant_parts_sociales']))
                apports_par_membre_annuel[membre_id]['montant_epargnes_bloquees'] += Decimal(str(membre_apports['montant_epargnes_bloquees']))
                apports_par_membre_annuel[membre_id]['montant_comptes_vue'] += Decimal(str(membre_apports.get('montant_comptes_vue', 0)))
                apports_par_membre_annuel[membre_id]['total_apports'] += Decimal(str(membre_apports['total_apports']))
            
            total_parts_sociales_annuel += Decimal(str(apports_mois['total_parts_sociales']))
            total_epargnes_bloquees_annuel += Decimal(str(apports_mois['total_epargnes_bloquees']))
            total_comptes_vue_annuel += Decimal(str(apports_mois.get('total_comptes_vue', 0)))
        
        # Convertir en format attendu
        apports_par_membre_list = []
        for membre_id, data in apports_par_membre_annuel.items():
            apports_par_membre_list.append({
                'membre_id': data['membre_id'],
                'membre_numero': data['membre_numero'],
                'membre_nom': data['membre_nom'],
                'montant_parts_sociales': float(data['montant_parts_sociales']),
                'montant_epargnes_bloquees': float(data['montant_epargnes_bloquees']),
                'montant_comptes_vue': float(data.get('montant_comptes_vue', 0)),
                'total_apports': float(data['total_apports'])
            })
        
        # total_comptes_vue_annuel est déjà calculé dans la boucle des mois ci-dessus
        total_apports_global = total_parts_sociales_annuel + total_epargnes_bloquees_annuel + total_comptes_vue_annuel
        apports = {
            'apports_par_membre': apports_par_membre_list,
            'total_parts_sociales': float(total_parts_sociales_annuel),
            'total_epargnes_bloquees': float(total_epargnes_bloquees_annuel),
            'total_comptes_vue': float(total_comptes_vue_annuel),
            'total_apports_global': float(total_apports_global)
        }
        periode_mois = None  # Indiquer que c'est le total annuel
    else:
        # Calculer les apports FILTRÉS PAR PÉRIODE (mois/année) si une période est spécifiée
        # Si un membre n'a pas d'apports dans cette période, il n'apparaîtra pas dans les résultats
        apports = calculer_apports_tous_membres(periode_mois, periode_annee)
        total_apports_global = Decimal(str(apports['total_apports_global']))
    
    # 3. Répartir les intérêts proportionnellement
    repartitions = []
    
    for membre_apports in apports['apports_par_membre']:
        apports_membre = Decimal(str(membre_apports['total_apports']))
        
        # Calculer la proportion
        if total_apports_global == 0:
            proportion = Decimal('0.00')
        else:
            proportion = apports_membre / total_apports_global
        
        # Calculer l'intérêt attribué au membre
        interet_membre = interet_net_a_repartir * proportion
        
        repartitions.append({
            'membre_id': membre_apports['membre_id'],
            'membre_numero': membre_apports['membre_numero'],
            'membre_nom': membre_apports['membre_nom'],
            'montant_parts_sociales': membre_apports['montant_parts_sociales'],
            'montant_epargnes_bloquees': membre_apports['montant_epargnes_bloquees'],
            'montant_comptes_vue': membre_apports.get('montant_comptes_vue', 0),
            'total_apports': membre_apports['total_apports'],
            'proportion': float(proportion),
            'interet_attribue': float(interet_membre)
        })
    
    return {
        'periode_mois': periode_mois,
        'periode_annee': periode_annee,
        'interet_total_global': resultats_interets['interet_total_global'],
        'frais_gestion_total_global': resultats_frais['frais_gestion_total_global'],
        'interet_net_a_repartir': float(interet_net_a_repartir),
        'total_parts_sociales': apports['total_parts_sociales'],
        'total_epargnes_bloquees': apports['total_epargnes_bloquees'],
        'total_comptes_vue': apports.get('total_comptes_vue', 0),
        'total_apports_global': apports['total_apports_global'],
        'repartitions': repartitions,
        'pourcentage_frais_gestion_utilise': pourcentage_frais_gestion
    }
