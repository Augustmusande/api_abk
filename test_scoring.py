"""
Script de test pour le système de scoring des crédits
Ce script permet de tester les différents scénarios de scoring
"""

import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coopec.settings')
django.setup()

from users.models import Membre, Client
from credits.models import Credit, Remboursement
from decimal import Decimal

def print_separator():
    print("\n" + "="*80 + "\n")

def test_scoring():
    """Test du système de scoring"""
    
    print_separator()
    print("TEST DU SYSTÈME DE SCORING DES CRÉDITS")
    print_separator()
    
    # 1. Créer ou récupérer un membre pour les tests
    print("1. Creation/Recuperation d'un membre de test...")
    membre, created = Membre.objects.get_or_create(
        email="test_scoring@example.com",
        defaults={
            'nom': 'Test',
            'prenom': 'Scoring',
            'telephone': '123456789',
            'password': 'test123456',
            'type_membre': 'PHYSIQUE'
        }
    )
    if created:
        print(f"[OK] Membre cree : {membre.numero_compte}")
    else:
        print(f"[OK] Membre existant : {membre.numero_compte}")
    
    # Supprimer les anciens crédits de test pour repartir à zéro
    Credit.objects.filter(membre=membre).delete()
    print("[OK] Anciens credits de test supprimes")
    
    print_separator()
    
    # 2. Créer plusieurs crédits avec différentes dates de remboursement
    print("2. Creation de credits de test...")
    
    # Crédit 1 : Paiement avant la date (score attendu : 10/10)
    date_octroi_1 = date.today() - timedelta(days=60)
    credit1 = Credit.objects.create(
        membre=membre,
        montant=Decimal('1000.00'),
        taux_interet=Decimal('5.00'),
        duree=3,
        duree_type='MOIS',
        methode_interet='PRECOMPTE',
        date_octroi=date_octroi_1
    )
    print(f"[OK] Credit 1 cree : {credit1.id} - Montant: {credit1.montant}")
    print(f"   Date d'octroi: {credit1.date_octroi}")
    print(f"   Date de fin: {credit1.date_fin}")
    print(f"   Score initial: {credit1.score}/10")
    
    # Crédit 2 : Paiement à la date exacte (score attendu : 8/10)
    date_octroi_2 = date.today() - timedelta(days=90)
    credit2 = Credit.objects.create(
        membre=membre,
        montant=Decimal('2000.00'),
        taux_interet=Decimal('5.00'),
        duree=3,
        duree_type='MOIS',
        methode_interet='PRECOMPTE',
        date_octroi=date_octroi_2
    )
    print(f"[OK] Credit 2 cree : {credit2.id} - Montant: {credit2.montant}")
    print(f"   Date d'octroi: {credit2.date_octroi}")
    print(f"   Date de fin: {credit2.date_fin}")
    print(f"   Score initial: {credit2.score}/10")
    
    # Crédit 3 : Paiement 1 mois après (score attendu : 5/10)
    date_octroi_3 = date.today() - timedelta(days=120)
    credit3 = Credit.objects.create(
        membre=membre,
        montant=Decimal('1500.00'),
        taux_interet=Decimal('5.00'),
        duree=3,
        duree_type='MOIS',
        methode_interet='PRECOMPTE',
        date_octroi=date_octroi_3
    )
    print(f"[OK] Credit 3 cree : {credit3.id} - Montant: {credit3.montant}")
    print(f"   Date d'octroi: {credit3.date_octroi}")
    print(f"   Date de fin: {credit3.date_fin}")
    print(f"   Score initial: {credit3.score}/10")
    
    # Crédit 4 : Paiement 2 mois après (score attendu : 2/10)
    date_octroi_4 = date.today() - timedelta(days=150)
    credit4 = Credit.objects.create(
        membre=membre,
        montant=Decimal('3000.00'),
        taux_interet=Decimal('5.00'),
        duree=3,
        duree_type='MOIS',
        methode_interet='PRECOMPTE',
        date_octroi=date_octroi_4
    )
    print(f"[OK] Credit 4 cree : {credit4.id} - Montant: {credit4.montant}")
    print(f"   Date d'octroi: {credit4.date_octroi}")
    print(f"   Date de fin: {credit4.date_fin}")
    print(f"   Score initial: {credit4.score}/10")
    
    print_separator()
    
    # 3. Simuler les remboursements avec différentes dates
    print("3. Simulation des remboursements...")
    
    # Remboursement 1 : AVANT la date de fin (score attendu : 10/10)
    date_remb_1 = credit1.date_fin - timedelta(days=5)
    remb1 = Remboursement.objects.create(
        credit=credit1,
        montant=credit1.solde_restant,
        echeance=date_remb_1
    )
    credit1.refresh_from_db()
    print(f"[OK] Remboursement 1 : {remb1.montant} le {date_remb_1}")
    print(f"   Date de fin du credit : {credit1.date_fin}")
    print(f"   Score apres remboursement : {credit1.score}/10 (attendu: 10/10)")
    print(f"   [{'CORRECT' if credit1.score == Decimal('10.0') else 'ERREUR'}]")
    
    # Remboursement 2 : À LA DATE EXACTE (score attendu : 8/10)
    date_remb_2 = credit2.date_fin
    remb2 = Remboursement.objects.create(
        credit=credit2,
        montant=credit2.solde_restant,
        echeance=date_remb_2
    )
    credit2.refresh_from_db()
    print(f"[OK] Remboursement 2 : {remb2.montant} le {date_remb_2}")
    print(f"   Date de fin du credit : {credit2.date_fin}")
    print(f"   Score apres remboursement : {credit2.score}/10 (attendu: 8/10)")
    print(f"   [{'CORRECT' if credit2.score == Decimal('8.0') else 'ERREUR'}]")
    
    # Remboursement 3 : 1 MOIS APRÈS (score attendu : 5/10)
    date_remb_3 = credit3.date_fin + timedelta(days=30)
    remb3 = Remboursement.objects.create(
        credit=credit3,
        montant=credit3.solde_restant,
        echeance=date_remb_3
    )
    credit3.refresh_from_db()
    print(f"[OK] Remboursement 3 : {remb3.montant} le {date_remb_3}")
    print(f"   Date de fin du credit : {credit3.date_fin}")
    print(f"   Score apres remboursement : {credit3.score}/10 (attendu: 5/10)")
    print(f"   [{'CORRECT' if credit3.score == Decimal('5.0') else 'ERREUR'}]")
    
    # Remboursement 4 : 2 MOIS APRÈS (score attendu : 2/10)
    date_remb_4 = credit4.date_fin + timedelta(days=60)
    remb4 = Remboursement.objects.create(
        credit=credit4,
        montant=credit4.solde_restant,
        echeance=date_remb_4
    )
    credit4.refresh_from_db()
    print(f"[OK] Remboursement 4 : {remb4.montant} le {date_remb_4}")
    print(f"   Date de fin du credit : {credit4.date_fin}")
    print(f"   Score apres remboursement : {credit4.score}/10 (attendu: 2/10)")
    print(f"   [{'CORRECT' if credit4.score == Decimal('2.0') else 'ERREUR'}]")
    
    print_separator()
    
    # 4. Calculer le score moyen du membre
    print("4. Calcul du score moyen du membre...")
    score_data = membre.calculer_score_moyen()
    
    print(f"RESULTATS DU SCORING :")
    print(f"   Nombre de credits : {score_data['nombre_credits']}")
    print(f"   Score moyen : {score_data['score_moyen']}/10")
    print(f"   Pourcentage : {score_data['pourcentage']}%")
    print(f"   Mention : {score_data['mention']}")
    print(f"   Mention complete : {membre.get_mention_score()}")
    
    # Calcul manuel pour vérification
    scores = [float(credit1.score), float(credit2.score), float(credit3.score), float(credit4.score)]
    moyenne_manuelle = sum(scores) / len(scores)
    pourcentage_manuel = moyenne_manuelle * 10
    
    print(f"\n   Verification manuelle :")
    print(f"   Scores individuels : {scores}")
    print(f"   Moyenne calculee : {moyenne_manuelle:.2f}/10")
    print(f"   Pourcentage calcule : {pourcentage_manuel:.2f}%")
    print(f"   [{'CORRECT' if abs(score_data['score_moyen'] - moyenne_manuelle) < 0.01 else 'ERREUR'}]")
    
    print_separator()
    
    # 5. Test via l'API (simulation)
    print("5. Test via serializer (simulation API)...")
    from users.serializers import MembreSerializer
    from rest_framework.test import APIRequestFactory
    
    factory = APIRequestFactory()
    request = factory.get('/')
    serializer = MembreSerializer(membre, context={'request': request})
    data = serializer.data
    
    print(f"Donnees du serializer :")
    print(f"   score_moyen : {data.get('score_moyen')}")
    print(f"   pourcentage_score : {data.get('pourcentage_score')}")
    print(f"   mention_score : {data.get('mention_score')}")
    print(f"   nombre_credits : {data.get('nombre_credits')}")
    
    print_separator()
    print("[OK] TESTS TERMINES !")
    print_separator()
    
    return {
        'membre': membre,
        'credits': [credit1, credit2, credit3, credit4],
        'score_data': score_data
    }

if __name__ == '__main__':
    try:
        result = test_scoring()
        print("\n[OK] Tous les tests ont ete executes avec succes !")
        print(f"\nPour tester via l'API, utilisez :")
        print(f"   GET /api/membres/{result['membre'].id}/")
        print(f"   ou")
        print(f"   GET /api/membres/")
    except Exception as e:
        print(f"\n[ERREUR] ERREUR lors des tests : {str(e)}")
        import traceback
        traceback.print_exc()
