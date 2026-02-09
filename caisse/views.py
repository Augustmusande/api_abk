"""
VIEWS - APPLICATION CAISSE

Endpoints pour les calculs financiers et la gestion des dépenses.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from coopec.pagination import StandardResultsSetPagination
from users.permissions import IsAdminOrSuperAdmin
from .models import Depenses, CaisseType, Caissetypemvt, DonDirect
from .serializers import DepensesSerializer, CaisseTypeSerializer, CaissetypemvtSerializer, DonDirectSerializer
from .services import (
    calculer_interets_tous_credits, 
    calculer_frais_gestion,
    calculer_apports_tous_membres,
    calculer_apports_membre,
    repartir_interets_aux_membres
)
from decimal import Decimal

@extend_schema(tags=['Caisse'])
class CalculsFinanciersViewSet(viewsets.ViewSet):
    """
    ViewSet pour les calculs financiers de la caisse.
    - ADMIN et SUPERADMIN : voient tous les calculs
    - MEMBRE : voit uniquement ses propres intérêts et répartition
    - CLIENT : voit uniquement ses propres intérêts (pas de répartition, c'est pour les membres uniquement)
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def interets(self, request):
        """
        Calcule les intérêts des crédits.
        
        GET /api/caisse/interets/
        
        - ADMIN et SUPERADMIN : voient tous les intérêts (tous les crédits)
        - MEMBRE : voit uniquement les intérêts de ses propres crédits
        - CLIENT : voit uniquement les intérêts de ses propres crédits
        
        Retourne :
        - Intérêts par crédit
        - Intérêts par membre
        - Intérêt total global
        """
        user = request.user
        
        # ADMIN et SUPERADMIN voient tous les intérêts
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            resultats = calculer_interets_tous_credits()
            return Response(resultats)
        
        # MEMBRE voit uniquement ses propres intérêts
        if user.user_type == 'MEMBRE' and user.membre:
            from credits.models import Credit
            from .services import calculer_interet_credit
            credits = Credit.objects.filter(membre=user.membre)
            
            interets_par_credit = []
            interet_total = Decimal('0.00')
            
            for credit in credits:
                interet = calculer_interet_credit(credit)
                interet_total += interet
                interets_par_credit.append({
                    'credit_id': credit.id,
                    'montant': float(credit.montant),
                    'taux_interet': float(credit.taux_interet),
                    'interet': float(interet),
                    'membre': credit.membre.numero_compte if credit.membre else None,
                    'client': None,
                })
            
            return Response({
                'interets_par_credit': interets_par_credit,
                'interets_par_membre': [{
                    'membre_id': user.membre.id,
                    'membre_numero': user.membre.numero_compte,
                    'membre_nom': user.membre.get_full_name() if hasattr(user.membre, 'get_full_name') else str(user.membre),
                    'interet_total': float(interet_total),
                    'nombre_credits': len(interets_par_credit)
                }],
                'interet_total_global': float(interet_total),
                'nombre_credits': len(interets_par_credit)
            })
        
        # CLIENT voit uniquement ses propres intérêts
        if user.user_type == 'CLIENT' and user.client:
            from credits.models import Credit
            from .services import calculer_interet_credit
            credits = Credit.objects.filter(client=user.client)
            
            interets_par_credit = []
            interet_total = Decimal('0.00')
            
            for credit in credits:
                interet = calculer_interet_credit(credit)
                interet_total += interet
                interets_par_credit.append({
                    'credit_id': credit.id,
                    'montant': float(credit.montant),
                    'taux_interet': float(credit.taux_interet),
                    'interet': float(interet),
                    'membre': None,
                    'client': credit.client.numero_compte if credit.client else None,
                })
            
            return Response({
                'interets_par_credit': interets_par_credit,
                'interets_par_client': [{
                    'client_id': user.client.id,
                    'client_numero': user.client.numero_compte,
                    'client_nom': f"{user.client.nom} {user.client.prenom}",
                    'interet_total': float(interet_total),
                    'nombre_credits': len(interets_par_credit)
                }],
                'interet_total_global': float(interet_total),
                'nombre_credits': len(interets_par_credit)
            })
        
        # Si aucun type d'utilisateur reconnu, retourner une erreur
        return Response(
            {'error': 'Vous n\'avez pas accès à ces informations.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=False, methods=['get'])
    def frais_gestion(self, request):
        """
        Calcule les frais de gestion sur l'intérêt total global.
        
        GET /api/caisse/frais_gestion/?pourcentage=20
        
        - ADMIN et SUPERADMIN : voient tous les frais de gestion (tous les membres)
        - MEMBRE : voit uniquement ses propres frais de gestion
        - CLIENT : pas d'accès (les frais de gestion sont calculés sur les crédits des membres)
        
        Paramètres :
        - pourcentage (float, optionnel) : Pourcentage des frais de gestion (défaut: 20)
        
        IMPORTANT : Les frais de gestion sont calculés sur l'intérêt total global,
        puis répartis proportionnellement aux intérêts de chaque membre.
        
        Retourne :
        - Intérêt total global
        - Frais de gestion total global
        - Frais de gestion par membre (répartis proportionnellement)
        """
        user = request.user
        
        # CLIENT n'a pas accès aux frais de gestion (c'est pour les membres uniquement)
        if user.user_type == 'CLIENT':
            return Response(
                {'error': 'Les frais de gestion sont uniquement disponibles pour les membres et les administrateurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer le pourcentage depuis les paramètres de requête
        pourcentage = request.query_params.get('pourcentage_frais_gestion', request.query_params.get('pourcentage', 20))
        try:
            pourcentage = float(pourcentage)
        except (ValueError, TypeError):
            pourcentage = 20.0
        
        # Récupérer l'année de période si fournie
        periode_annee = request.query_params.get('periode_annee')
        if periode_annee:
            try:
                periode_annee = int(periode_annee)
            except (ValueError, TypeError):
                periode_annee = None
        else:
            periode_annee = None
        
# ADMIN et SUPERADMIN voient tous les frais de gestion
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            resultats = calculer_frais_gestion(pourcentage, periode_annee=periode_annee)
            return Response(resultats)
        
        # MEMBRE voit uniquement ses propres frais de gestion
        if user.user_type == 'MEMBRE' and user.membre:
            resultats_complets = calculer_frais_gestion(pourcentage, periode_annee=periode_annee)
            
            # Filtrer pour ne garder que le membre connecté
            membre_id = user.membre.id
            frais_membre = None
            
            for frais in resultats_complets.get('frais_par_membre', []):
                if frais.get('membre_id') == membre_id:
                    frais_membre = frais
                    break
            
            if not frais_membre:
                # Si le membre n'est pas dans la liste, créer une entrée avec 0
                frais_membre = {
                    'membre_id': membre_id,
                    'membre_numero': user.membre.numero_compte,
                    'membre_nom': str(user.membre),
                    'interet_total': 0.0,
                    'frais_gestion': 0.0,
                    'nombre_credits': 0
                }
            
            # Retourner uniquement les informations du membre avec les totaux globaux
            return Response({
                'frais_gestion_membre': frais_membre,
                'totaux_globaux': {
                    'interet_total_global': resultats_complets.get('interet_total_global', 0),
                    'frais_gestion_total_global': resultats_complets.get('frais_gestion_total_global', 0),
                },
                'pourcentage_utilise': pourcentage,
            })
        
        # Si aucun type d'utilisateur reconnu, retourner une erreur
        return Response(
            {'error': 'Vous n\'avez pas accès à ces informations.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=False, methods=['get'])
    def resume(self, request):
        """
        Retourne un résumé complet des calculs financiers.
        
        GET /api/caisse/resume/?pourcentage_frais_gestion=20
        
        - ADMIN et SUPERADMIN : voient tous les calculs
        - MEMBRE et CLIENT : pas d'accès (résumé uniquement pour les administrateurs)
        
        Paramètres :
        - pourcentage_frais_gestion (float, optionnel) : Pourcentage des frais de gestion (défaut: 20)
        
        Retourne :
        - Tous les calculs d'intérêts
        - Tous les calculs de frais de gestion
        """
        user = request.user
        
        # Seuls ADMIN et SUPERADMIN ont accès au résumé complet
        if user.user_type not in ['ADMIN', 'SUPERADMIN']:
            return Response(
                {'error': 'Le résumé complet des calculs financiers est uniquement disponible pour les administrateurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer le pourcentage depuis les paramètres de requête
        pourcentage = request.query_params.get('pourcentage_frais_gestion', 20)
        try:
            pourcentage = float(pourcentage)
        except (ValueError, TypeError):
            pourcentage = 20.0
        
        from datetime import date
        
        periode_mois = request.query_params.get('periode_mois')
        periode_annee = request.query_params.get('periode_annee')
        
        try:
            periode_mois = int(periode_mois) if periode_mois else None
            periode_annee = int(periode_annee) if periode_annee else None
        except (ValueError, TypeError):
            periode_mois = None
            periode_annee = None
        
        # Calculer les intérêts (tous les crédits, pas de filtrage par période)
        resultats_interets = calculer_interets_tous_credits()
        
        # Calculer les frais de gestion (sur l'intérêt total global + frais d'adhésion)
        resultats_frais = calculer_frais_gestion(pourcentage, periode_annee=periode_annee)
        
        # Calculer l'intérêt net à répartir (intérêt total - frais de gestion)
        interet_net = resultats_interets['interet_total_global'] - resultats_frais['frais_gestion_total_global']
        
        return Response({
            'interets': resultats_interets,
            'frais_gestion': resultats_frais,
            'interet_net_a_repartir': float(interet_net),
            'pourcentage_frais_gestion_utilise': pourcentage
        })
    
    @action(detail=False, methods=['get'])
    def apports_membres(self, request):
        """
        Calcule les apports des membres (parts sociales + épargnes bloquées).
        
        GET /api/caisse/apports_membres/?periode_mois=12&periode_annee=2025
        
        - ADMIN et SUPERADMIN : voient les apports de tous les membres
        - MEMBRE : voit uniquement ses propres apports
        - CLIENT : pas d'accès (les apports sont uniquement pour les membres)
        
        Paramètres :
        - periode_mois (int, optionnel) : Mois pour filtrer (1-12)
        - periode_annee (int, optionnel) : Année pour filtrer
        
        Retourne :
        - Apports par membre (parts sociales + épargnes bloquées)
        - Totaux globaux
        """
        user = request.user
        
        # CLIENT n'a pas accès aux apports des membres
        if user.user_type == 'CLIENT':
            return Response(
                {'error': 'Les apports sont uniquement disponibles pour les membres et les administrateurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        periode_mois = request.query_params.get('periode_mois')
        periode_annee = request.query_params.get('periode_annee')
        
        try:
            periode_mois = int(periode_mois) if periode_mois else None
            periode_annee = int(periode_annee) if periode_annee else None
        except (ValueError, TypeError):
            periode_mois = None
            periode_annee = None
        
        # Valider le mois (doit être entre 1 et 12)
        if periode_mois is not None and (periode_mois < 1 or periode_mois > 12):
            return Response({
                'error': f'Mois invalide: {periode_mois}. Le mois doit être entre 1 et 12.'
            }, status=400)
        
        # ADMIN et SUPERADMIN voient les apports de tous les membres
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            resultats = calculer_apports_tous_membres(periode_mois, periode_annee)
            return Response(resultats)
        
        # MEMBRE voit uniquement ses propres apports
        if user.user_type == 'MEMBRE' and user.membre:
            from .services import calculer_apports_membre
            apports_membre = calculer_apports_membre(user.membre, periode_mois, periode_annee)
            
            # Pour avoir les totaux globaux, on doit quand même calculer pour tous les membres
            # Mais on ne retournera que les totaux et les apports du membre
            resultats_complets = calculer_apports_tous_membres(periode_mois, periode_annee)
            
            return Response({
                'apports_membre': {
                    'membre_id': user.membre.id,
                    'membre_numero': user.membre.numero_compte,
                    'membre_nom': str(user.membre),
                    'montant_parts_sociales': float(apports_membre.get('montant_parts_sociales', 0)),
                    'montant_epargnes_bloquees': float(apports_membre.get('montant_epargnes_bloquees', 0)),
                    'montant_comptes_vue': float(apports_membre.get('montant_comptes_vue', 0)),
                    'total_credits_actifs': float(apports_membre.get('total_credits_actifs', 0)),
                    'total_apports_bruts': float(apports_membre.get('total_apports_bruts', 0)),
                    'total_apports': float(apports_membre.get('total_apports', 0)),
                },
                'totaux_globaux': {
                    'total_parts_sociales': resultats_complets.get('total_parts_sociales', 0),
                    'total_epargnes_bloquees': resultats_complets.get('total_epargnes_bloquees', 0),
                    'total_comptes_vue': resultats_complets.get('total_comptes_vue', 0),
                    'total_credits_actifs': resultats_complets.get('total_credits_actifs', 0),
                    'total_apports_bruts': resultats_complets.get('total_apports_bruts', 0),
                    'total_apports_global': resultats_complets.get('total_apports_global', 0),
                },
                'periode': {
                    'mois': periode_mois,
                    'annee': periode_annee,
                },
            })
        
        # Si aucun type d'utilisateur reconnu, retourner une erreur
        return Response(
            {'error': 'Vous n\'avez pas accès à ces informations.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=False, methods=['get'])
    def repartition_interets(self, request):
        """
        Répartit les intérêts aux membres selon leurs apports.
        
        GET /api/caisse/repartition_interets/?pourcentage_frais_gestion=20&periode_mois=12&periode_annee=2025
        GET /api/caisse/repartition_interets/ (utilise le mois et l'année courants par défaut)
        
        - SUPERADMIN et ADMIN : voient la répartition pour TOUS les membres (liste complète)
        - MEMBRE : voit UNIQUEMENT sa propre répartition (filtrée, pas les autres membres)
        - CLIENT : pas d'accès (la répartition est uniquement pour les membres)
        
        Paramètres :
        - pourcentage_frais_gestion (float, optionnel) : Pourcentage des frais de gestion (défaut: 20)
        - periode_mois (int, optionnel) : Mois pour filtrer les apports (1-12). Si non spécifié mais periode_annee spécifié, calcule le total de toute l'année. Si aucun des deux n'est spécifié, utilise le mois courant.
        - periode_annee (int, optionnel) : Année pour filtrer les apports. Si non spécifiée, utilise l'année courante.
        
        IMPORTANT : 
        - Les intérêts et frais de gestion sont calculés globalement (tous les crédits)
        - Les apports des membres sont filtrés par période (mois/année)
        - Si periode_mois n'est pas spécifié mais periode_annee l'est, retourne le total de toute l'année (somme des 12 mois)
        - Si un membre n'a pas d'apports dans la période, il aura 0 comme apports et proportion
        
        Formule :
        - proportion = (PartSocial_membre + epargne_bloquee_membre) / (PartSocialTotal + epargne_bloqueeTotal)
        - interet_membre = interet_net_a_repartir * proportion
        
        Retourne :
        - Répartition complète des intérêts par membre
        """
        user = request.user
        
        # CLIENT n'a pas accès à la répartition des intérêts (c'est uniquement pour les membres)
        if user.user_type == 'CLIENT':
            return Response(
                {'error': 'La répartition des intérêts est uniquement disponible pour les membres.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les paramètres
        pourcentage = request.query_params.get('pourcentage_frais_gestion', 20)
        periode_mois = request.query_params.get('periode_mois')
        periode_annee = request.query_params.get('periode_annee')
        
        try:
            pourcentage = float(pourcentage)
        except (ValueError, TypeError):
            pourcentage = 20.0
        
        try:
            periode_mois = int(periode_mois) if periode_mois else None
            periode_annee = int(periode_annee) if periode_annee else None
        except (ValueError, TypeError):
            periode_mois = None
            periode_annee = None
        
        # Valider le mois (doit être entre 1 et 12)
        if periode_mois is not None and (periode_mois < 1 or periode_mois > 12):
            return Response({
                'error': f'Mois invalide: {periode_mois}. Le mois doit être entre 1 et 12.'
            }, status=400)
        
        # Si aucune période n'est fournie, utiliser le mois et l'année courants
        # Si seule l'année est fournie (sans mois), on calcule le total annuel
        from datetime import date
        if periode_mois is None and periode_annee is None:
            aujourd_hui = date.today()
            periode_mois = aujourd_hui.month
            periode_annee = aujourd_hui.year
        elif periode_annee is None:
            aujourd_hui = date.today()
            periode_annee = aujourd_hui.year
        
        # ADMIN et SUPERADMIN voient la répartition pour tous les membres
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            resultats = repartir_interets_aux_membres(pourcentage, periode_mois, periode_annee)
            return Response(resultats)
        
        # MEMBRE voit uniquement sa propre répartition
        if user.user_type == 'MEMBRE' and user.membre:
            # Obtenir la répartition pour tous les membres (pour avoir les totaux globaux)
            resultats_complets = repartir_interets_aux_membres(pourcentage, periode_mois, periode_annee)
            
            # Filtrer pour ne garder que le membre connecté dans les répartitions
            membre_id = user.membre.id
            repartition_membre = None
            
            # Chercher la répartition du membre dans la liste 'repartitions'
            for repart in resultats_complets.get('repartitions', []):
                if repart.get('membre_id') == membre_id:
                    repartition_membre = repart
                    break
            
            # Si le membre n'est pas dans la répartition, créer une entrée avec 0
            if not repartition_membre:
                repartition_membre = {
                    'membre_id': membre_id,
                    'membre_numero': user.membre.numero_compte,
                    'membre_nom': str(user.membre),
                    'montant_parts_sociales': 0.0,
                    'montant_epargnes_bloquees': 0.0,
                    'montant_comptes_vue': 0.0,
                    'total_apports': 0.0,
                    'proportion': 0.0,
                    'interet_attribue': 0.0
                }
            
            # Retourner uniquement la répartition du membre avec les totaux globaux
            return Response({
                'periode_mois': resultats_complets.get('periode_mois'),
                'periode_annee': resultats_complets.get('periode_annee'),
                'interet_total_global': resultats_complets.get('interet_total_global', 0),
                'frais_gestion_total_global': resultats_complets.get('frais_gestion_total_global', 0),
                'interet_net_a_repartir': resultats_complets.get('interet_net_a_repartir', 0),
                'total_parts_sociales': resultats_complets.get('total_parts_sociales', 0),
                'total_epargnes_bloquees': resultats_complets.get('total_epargnes_bloquees', 0),
                'total_comptes_vue': resultats_complets.get('total_comptes_vue', 0),
                'total_apports_global': resultats_complets.get('total_apports_global', 0),
                'repartitions': [repartition_membre],  # Uniquement la répartition du membre connecté
                'pourcentage_frais_gestion_utilise': resultats_complets.get('pourcentage_frais_gestion_utilise', pourcentage)
            })
        
        # Si aucun type d'utilisateur reconnu, retourner une erreur
        return Response(
            {'error': 'Vous n\'avez pas accès à ces informations.'},
            status=status.HTTP_403_FORBIDDEN
        )

@extend_schema(tags=['Caisse'])
class DepensesViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des dépenses.
    - ADMIN et SUPERADMIN : voient toutes les dépenses et peuvent créer/modifier/supprimer
    - MEMBRE et CLIENT : pas d'accès (gestion réservée aux administrateurs)
    
    Les dépenses sont financées par les frais de gestion.
    """
    queryset = Depenses.objects.all()
    serializer_class = DepensesSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Seuls ADMIN et SUPERADMIN peuvent accéder aux dépenses"""
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'total']:
            return [IsAdminOrSuperAdmin()]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=['get'])
    def total(self, request):
        """
        Calcule le total des dépenses.
        
        GET /api/caisse/depenses/total/
        
        Retourne :
        - Total des dépenses
        - Nombre de dépenses
        """
        from decimal import Decimal
        total = sum([depense.pt for depense in self.queryset])
        
        return Response({
            'total_depenses': float(total),
            'nombre_depenses': self.queryset.count()
        })

@extend_schema(tags=['Caisse'])
class DonDirectViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des dons directs.
    - ADMIN et SUPERADMIN : voient tous les dons directs et peuvent créer/modifier/supprimer
    - MEMBRE et CLIENT : pas d'accès (gestion réservée aux administrateurs)
    
    Les dons directs sont des entrées directes en caisse de personnes qui ne sont ni membres ni clients.
    """
    queryset = DonDirect.objects.all()
    serializer_class = DonDirectSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Seuls ADMIN et SUPERADMIN peuvent accéder aux dons directs"""
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSuperAdmin()]
        return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        """Retourne tous les dons directs pour ADMIN et SUPERADMIN"""
        user = self.request.user
        if user.user_type in ['ADMIN', 'SUPERADMIN']:
            return DonDirect.objects.all()
        return DonDirect.objects.none()

@extend_schema(tags=['Types de Caisse'])
class CaisseTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les types de caisse (Airtel Money, Orange Money, Banque, etc.).
    Supporte toutes les opérations CRUD : GET, POST, PUT, PATCH, DELETE
    Accessible uniquement aux ADMIN et SUPERADMIN
    """
    queryset = CaisseType.objects.all()
    serializer_class = CaisseTypeSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_context(self):
        """Ajouter le contexte de la requête pour générer les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_serializer(self, *args, **kwargs):
        """S'assurer que le contexte est toujours passé au serializer"""
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)
    
    @extend_schema(
        summary="Calculer les totaux par type de caisse",
        description="""
        Endpoint pour calculer les totaux des montants par type de caisse.
        
        Pour chaque type de caisse, calcule le total en tenant compte du type d'opération :
        - Entrées : additionne le montant
        - Entrées_APRES_CALCUL_FRAIS_GESTION : additionne le montant
        - Sorties : soustrait le montant (retrait d'argent)
        - Remboursements : additionne le montant
        - Donations d'épargne : additionne le montant
        - Donations de part sociale : additionne le montant
        - Frais d'adhésion : additionne le montant
        - Dépenses : soustrait le montant (sortie d'argent)
        - Retraits : soustrait le montant (sortie d'argent)
        
        **Total général** : Calcule la différence entre toutes les entrées et toutes les sorties
        de tous les types de caisse (total_general = total_entrees - total_sorties)
        
        **Filtrage par date** : Utilise le champ `date` de Caissetypemvt
        - `date_debut` : Date de début (format: YYYY-MM-DD)
        - `date_fin` : Date de fin (format: YYYY-MM-DD)
        
        **Exemple de requête** :
        GET /api/caisse/caissetypes/calculer_totaux/?date_debut=2025-01-01&date_fin=2025-12-31
        """,
        parameters=[
            OpenApiParameter(
                name='date_debut',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Date de début pour le filtrage (format: YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='date_fin',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Date de fin pour le filtrage (format: YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={
            200: {
                'description': 'Liste des types de caisse avec leurs totaux',
                'examples': {
                    'application/json': {
                        'count': 3,
                        'total_general': 800000.00,
                        'total_general_entrees': 1000000.00,
                        'total_general_sorties': 200000.00,
                        'results': [
                            {
                                'id': 1,
                                'nom': 'Airtel Money',
                                'description': 'Caisse Airtel Money',
                                'image_url': 'http://example.com/media/caissetypes/logos/airtel.png',
                                'total_montant': 500000.00,
                                'total_entrees': 600000.00,
                                'total_sorties': 100000.00,
                                'nombre_mouvements': 45
                            },
                            {
                                'id': 2,
                                'nom': 'Orange Money',
                                'description': 'Caisse Orange Money',
                                'image_url': 'http://example.com/media/caissetypes/logos/orange.png',
                                'total_montant': 300000.00,
                                'total_entrees': 400000.00,
                                'total_sorties': 100000.00,
                                'nombre_mouvements': 30
                            }
                        ]
                    }
                }
            }
        }
    )
    @action(detail=False, methods=['get'], url_path='calculer_totaux')
    def calculer_totaux(self, request):
        """
        Calcule les totaux des montants par type de caisse.
        Filtre par date si date_debut et/ou date_fin sont fournis.
        """
        from datetime import date as date_type
        from django.utils.dateparse import parse_date
        
        # Récupérer les paramètres de filtrage par date
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')
        
        date_debut = None
        date_fin = None
        
        if date_debut_str:
            try:
                date_debut = parse_date(date_debut_str)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date_debut invalide. Utilisez le format YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if date_fin_str:
            try:
                date_fin = parse_date(date_fin_str)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date_fin invalide. Utilisez le format YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Vérifier la cohérence des dates
        if date_debut and date_fin and date_debut > date_fin:
            return Response(
                {'error': 'La date de début doit être antérieure ou égale à la date de fin.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer tous les types de caisse
        caissetypes = CaisseType.objects.all().order_by('nom')
        
        # Préparer les résultats
        results = []
        
        for caissetype in caissetypes:
            # Filtrer les mouvements par type de caisse et date
            mouvements = Caissetypemvt.objects.filter(caissetype=caissetype)
            
            # Appliquer le filtrage par date si fourni
            if date_debut:
                mouvements = mouvements.filter(date__gte=date_debut)
            if date_fin:
                mouvements = mouvements.filter(date__lte=date_fin)
            
            # Calculer le total en additionnant/soustrayant les montants selon le type
            total_montant = Decimal('0.00')
            total_entrees = Decimal('0.00')
            total_sorties = Decimal('0.00')
            
            for mouvement in mouvements:
                # Utiliser directement les autres relations (remboursement, donations, etc.)
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
            
            # Construire l'URL de l'image si elle existe
            image_url = None
            if caissetype.image and hasattr(caissetype.image, 'url'):
                image_url = request.build_absolute_uri(caissetype.image.url)
            
            results.append({
                'id': caissetype.id,
                'nom': caissetype.nom,
                'description': caissetype.description or '',
                'image_url': image_url,
                'total_montant': float(total_montant),
                'total_entrees': float(total_entrees),
                'total_sorties': float(total_sorties),
                'nombre_mouvements': mouvements.count(),
                'last_updated': caissetype.last_updated,
                'created_at': caissetype.created_at
            })
        
        # Calculer le total général (différence entre toutes les entrées et sorties de tous les types de caisse)
        total_general_entrees = Decimal('0.00')
        total_general_sorties = Decimal('0.00')
        total_general = Decimal('0.00')
        
        for result in results:
            total_general_entrees += Decimal(str(result['total_entrees']))
            total_general_sorties += Decimal(str(result['total_sorties']))
            total_general += Decimal(str(result['total_montant']))
        
        # Pagination
        paginator = StandardResultsSetPagination()
        paginated_results = paginator.paginate_queryset(results, request)
        
        response_data = {
            'count': len(results),
            'total_general': float(total_general),
            'total_general_entrees': float(total_general_entrees),
            'total_general_sorties': float(total_general_sorties),
            'results': paginated_results if paginated_results is not None else results
        }
        
        if paginated_results is not None:
            # Ajouter les totaux généraux aux métadonnées de pagination
            paginated_response = paginator.get_paginated_response(paginated_results)
            paginated_response.data['total_general'] = float(total_general)
            paginated_response.data['total_general_entrees'] = float(total_general_entrees)
            paginated_response.data['total_general_sorties'] = float(total_general_sorties)
            return paginated_response
        
        return Response(response_data, status=status.HTTP_200_OK)

@extend_schema(tags=['Mouvements de Type de Caisse'])
class CaissetypemvtViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les mouvements de type de caisse.
    Permet de lier un type de caisse à une donnation/remboursement/dépense/retrait.
    Supporte toutes les opérations CRUD : GET, POST, PUT, PATCH, DELETE
    Accessible uniquement aux ADMIN et SUPERADMIN
    
    **Filtrage disponible :**
    - `caissetype` : ID du type de caisse
    - `date` : Date exacte (format: YYYY-MM-DD)
    - `date__gte` : Date >= (format: YYYY-MM-DD)
    - `date__lte` : Date <= (format: YYYY-MM-DD)
    
    - `remboursement` : ID du remboursement
    - `donnatepargne` : ID du don d'épargne
    - `donnatpartsocial` : ID du don de part sociale
    - `fraisadhesion` : ID des frais d'adhésion
    - `depense` : ID de la dépense
    - `retrait` : ID du retrait
    """
    queryset = Caissetypemvt.objects.all()
    serializer_class = CaissetypemvtSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Permet le filtrage des mouvements par type de caisse et date
        """
        queryset = Caissetypemvt.objects.all().select_related(
            'caissetype', 'remboursement', 
            'donnatepargne', 'donnatpartsocial', 'fraisadhesion',
            'depense', 'retrait'
        )
        
        # Filtrage par type de caisse
        caissetype_id = self.request.query_params.get('caissetype')
        if caissetype_id:
            queryset = queryset.filter(caissetype_id=caissetype_id)
        
        # Filtrage par date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        date_gte = self.request.query_params.get('date__gte')
        if date_gte:
            queryset = queryset.filter(date__gte=date_gte)
        
        date_lte = self.request.query_params.get('date__lte')
        if date_lte:
            queryset = queryset.filter(date__lte=date_lte)
        
        return queryset.order_by('-date', '-created_at')
    
    @extend_schema(
        summary="Historique détaillé des opérations par type de caisse",
        description="""
        Retourne l'historique détaillé des opérations avec les montants et types d'opérations.
        
        **Filtrage disponible :**
        - `caissetype` : ID du type de caisse (obligatoire pour filtrer)
        - `date_debut` : Date de début (format: YYYY-MM-DD)
        - `date_fin` : Date de fin (format: YYYY-MM-DD)
        
        **Types d'opérations retournés :**
        - Crédit (SORTIE)
        - Remboursement
        - Don d'épargne
        - Don de part sociale
        - Frais d'adhésion
        - Dépense
        - Retrait
        
        Chaque opération inclut :
        - Type d'opération
        - Montant
        - Date
        - Détails de l'opération
        """,
        parameters=[
            OpenApiParameter(
                name='caissetype',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID du type de caisse (obligatoire)',
                required=True
            ),
            OpenApiParameter(
                name='date_debut',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Date de début pour le filtrage (format: YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='date_fin',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Date de fin pour le filtrage (format: YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={
            200: {
                'description': 'Historique des opérations avec détails',
                'examples': {
                    'application/json': {
                        'caissetype_id': 1,
                        'caissetype_nom': 'Airtel Money',
                        'count': 45,
                        'results': [
                            {
                                'id': 1,
                                'date': '2025-01-15',
                                'type_operation': 'Crédit',
                                'sous_type': 'ENTREE',
                                'montant': 1000.00,
                                'libelle': 'Versement initial',
                                'credit_id': 5,
                                'remboursement_id': None,
                                'donnatepargne_id': None,
                                'donnatpartsocial_id': None,
                                'fraisadhesion_id': None,
                                'depense_id': None,
                                'retrait_id': None
                            }
                        ]
                    }
                }
            }
        }
    )
    @action(detail=False, methods=['get'], url_path='historique')
    def historique(self, request):
        """
        Retourne l'historique détaillé des opérations par type de caisse avec montants et types d'opérations.
        """
        from datetime import date as date_type
        from django.utils.dateparse import parse_date
        
        # Récupérer le type de caisse (obligatoire)
        caissetype_id = request.query_params.get('caissetype')
        if not caissetype_id:
            return Response(
                {'error': 'Le paramètre caissetype est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            caissetype_id = int(caissetype_id)
            caissetype = CaisseType.objects.get(id=caissetype_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Format de caissetype invalide. Doit être un nombre.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CaisseType.DoesNotExist:
            return Response(
                {'error': f'Aucun type de caisse trouvé avec l\'ID {caissetype_id}.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les paramètres de filtrage par date
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')
        
        date_debut = None
        date_fin = None
        
        if date_debut_str:
            try:
                date_debut = parse_date(date_debut_str)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date_debut invalide. Utilisez le format YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if date_fin_str:
            try:
                date_fin = parse_date(date_fin_str)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Format de date_fin invalide. Utilisez le format YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Vérifier la cohérence des dates
        if date_debut and date_fin and date_debut > date_fin:
            return Response(
                {'error': 'La date de début doit être antérieure ou égale à la date de fin.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrer les mouvements
        mouvements = Caissetypemvt.objects.filter(caissetype=caissetype).select_related(
            'remboursement', 'donnatepargne', 
            'donnatpartsocial', 'fraisadhesion', 'depense', 'retrait'
        )
        
        if date_debut:
            mouvements = mouvements.filter(date__gte=date_debut)
        if date_fin:
            mouvements = mouvements.filter(date__lte=date_fin)
        
        # Construire l'historique détaillé
        historique = []
        
        for mouvement in mouvements.order_by('-date', '-created_at'):
            operation = {
                'id': mouvement.id,
                'date': mouvement.date.isoformat() if mouvement.date else None,
                'caissetype_id': caissetype.id,
                'caissetype_nom': caissetype.nom,
            }
            
            # Utiliser directement les autres relations (remboursement, donations, etc.)

            if mouvement.remboursement:
                operation.update({
                    'type_operation': 'Remboursement',
                    'sous_type': 'ENTREE',
                    'montant': float(mouvement.remboursement.montant),
                    'libelle': f'Remboursement crédit #{mouvement.remboursement.credit.id if mouvement.remboursement.credit else "N/A"}',
                                        'remboursement_id': mouvement.remboursement.id,
                    'donnatepargne_id': None,
                    'donnatpartsocial_id': None,
                    'fraisadhesion_id': None,
                    'depense_id': None,
                    'retrait_id': None,
                })
            
            # Don d'épargne
            elif mouvement.donnatepargne:
                operation.update({
                    'type_operation': 'Don d\'épargne',
                    'sous_type': 'ENTREE',
                    'montant': float(mouvement.donnatepargne.montant),
                    'libelle': f'Don d\'épargne - {mouvement.donnatepargne.souscriptEpargne.designation if mouvement.donnatepargne.souscriptEpargne else "N/A"}',
                                        'remboursement_id': None,
                    'donnatepargne_id': mouvement.donnatepargne.id,
                    'donnatpartsocial_id': None,
                    'fraisadhesion_id': None,
                    'depense_id': None,
                    'retrait_id': None,
                })
            
            # Don de part sociale
            elif mouvement.donnatpartsocial:
                operation.update({
                    'type_operation': 'Don de part sociale',
                    'sous_type': 'ENTREE',
                    'montant': float(mouvement.donnatpartsocial.montant),
                    'libelle': f'Don de part sociale - {mouvement.donnatpartsocial.souscription_part_social.partSocial.annee if mouvement.donnatpartsocial.souscription_part_social and mouvement.donnatpartsocial.souscription_part_social.partSocial else "N/A"}',
                                        'remboursement_id': None,
                    'donnatepargne_id': None,
                    'donnatpartsocial_id': mouvement.donnatpartsocial.id,
                    'fraisadhesion_id': None,
                    'depense_id': None,
                    'retrait_id': None,
                })
            
            # Frais d'adhésion
            elif mouvement.fraisadhesion:
                operation.update({
                    'type_operation': 'Frais d\'adhésion',
                    'sous_type': 'ENTREE',
                    'montant': float(mouvement.fraisadhesion.montant),
                    'libelle': f'Frais d\'adhésion',
                                        'remboursement_id': None,
                    'donnatepargne_id': None,
                    'donnatpartsocial_id': None,
                    'fraisadhesion_id': mouvement.fraisadhesion.id,
                    'depense_id': None,
                    'retrait_id': None,
                })
            
            # Dépense
            elif mouvement.depense:
                operation.update({
                    'type_operation': 'Dépense',
                    'sous_type': 'SORTIE',
                    'montant': float(mouvement.depense.pt),  # Prix total
                    'libelle': f'{mouvement.depense.libelle} - {mouvement.depense.quantite} {mouvement.depense.uniter}',
                                        'remboursement_id': None,
                    'donnatepargne_id': None,
                    'donnatpartsocial_id': None,
                    'fraisadhesion_id': None,
                    'depense_id': mouvement.depense.id,
                    'retrait_id': None,
                })
            
            # Retrait
            elif mouvement.retrait:
                operation.update({
                    'type_operation': 'Retrait',
                    'sous_type': 'SORTIE',
                    'montant': float(mouvement.retrait.montant),
                    'libelle': f'Retrait - {mouvement.retrait.motif or "Sans motif"}',
                                        'remboursement_id': None,
                    'donnatepargne_id': None,
                    'donnatpartsocial_id': None,
                    'fraisadhesion_id': None,
                    'depense_id': None,
                    'retrait_id': mouvement.retrait.id,
                })
            
            historique.append(operation)
        
        # Pagination
        paginator = StandardResultsSetPagination()
        paginated_results = paginator.paginate_queryset(historique, request)
        
        response_data = {
            'caissetype_id': caissetype.id,
            'caissetype_nom': caissetype.nom,
            'count': len(historique),
            'results': paginated_results if paginated_results is not None else historique
        }
        
        if paginated_results is not None:
            paginated_response = paginator.get_paginated_response(paginated_results)
            paginated_response.data['caissetype_id'] = caissetype.id
            paginated_response.data['caissetype_nom'] = caissetype.nom
            return paginated_response
        
        return Response(response_data, status=status.HTTP_200_OK)