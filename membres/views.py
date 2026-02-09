
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from coopec.pagination import StandardResultsSetPagination
from users.permissions import IsAdminOrSuperAdmin
from .models import PartSocial, FraisAdhesion, DonnatPartSocial, SouscriptEpargne, DonnatEpargne, Compte, SouscriptionPartSocial, Retrait
from .serializers import *

@extend_schema(tags=['Membres'])
class CompteViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les comptes.
	- ADMIN et SUPERADMIN : voient tous les comptes
	- MEMBRE : voit uniquement ses propres comptes
	- CLIENT : voit uniquement ses propres comptes
	"""
	queryset = Compte.objects.all()
	serializer_class = CompteSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les comptes selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return Compte.objects.all()
		
		# MEMBRE voit uniquement ses propres comptes
		if user.user_type == 'MEMBRE' and user.membre:
			return Compte.objects.filter(titulaire_membre=user.membre)
		
		# CLIENT voit uniquement ses propres comptes
		if user.user_type == 'CLIENT' and user.client:
			return Compte.objects.filter(titulaire_client=user.client)
		
		# Par défaut, retourner un queryset vide
		return Compte.objects.none()

@extend_schema(tags=['Membres'])
class PartSocialViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les parts sociales.
	- ADMIN et SUPERADMIN : voient toutes les parts sociales
	- MEMBRE : voit toutes les parts sociales (modèle global, pas de filtrage par membre)
	- CLIENT : pas d'accès (les parts sociales sont uniquement pour les membres)
	"""
	queryset = PartSocial.objects.all()
	serializer_class = PartSocialSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN, SUPERADMIN et MEMBRE voient toutes les parts sociales
		if user.user_type in ['ADMIN', 'SUPERADMIN', 'MEMBRE']:
			return PartSocial.objects.all()
		
		# CLIENT n'a pas accès aux parts sociales
		return PartSocial.objects.none()

@extend_schema(tags=['Membres'])
class FraisAdhesionViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les frais d'adhésion.
	- ADMIN et SUPERADMIN : voient tous les frais d'adhésion
	- MEMBRE : voit uniquement ses propres frais d'adhésion
	- CLIENT : voit uniquement ses propres frais d'adhésion
	"""
	queryset = FraisAdhesion.objects.all()
	serializer_class = FraisAdhesionSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les frais d'adhésion selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return FraisAdhesion.objects.all()
		
		# MEMBRE voit uniquement ses propres frais d'adhésion
		if user.user_type == 'MEMBRE' and user.membre:
			return FraisAdhesion.objects.filter(titulaire_membre=user.membre)
		
		# CLIENT voit uniquement ses propres frais d'adhésion
		if user.user_type == 'CLIENT' and user.client:
			return FraisAdhesion.objects.filter(titulaire_client=user.client)
		
		# Par défaut, retourner un queryset vide
		return FraisAdhesion.objects.none()

@extend_schema(tags=['Membres'])
class SouscriptionPartSocialViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les souscriptions de parts sociales.
	- ADMIN et SUPERADMIN : voient toutes les souscriptions
	- MEMBRE : voit uniquement ses propres souscriptions
	- CLIENT : pas d'accès (les parts sociales sont uniquement pour les membres)
	"""
	queryset = SouscriptionPartSocial.objects.all()
	serializer_class = SouscriptionPartSocialSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les souscriptions selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return SouscriptionPartSocial.objects.all()
		
		# MEMBRE voit uniquement ses propres souscriptions
		if user.user_type == 'MEMBRE' and user.membre:
			return SouscriptionPartSocial.objects.filter(membre=user.membre)
		
		# CLIENT n'a pas accès aux souscriptions de parts sociales
		return SouscriptionPartSocial.objects.none()

@extend_schema(tags=['Membres'])
class DonnatPartSocialViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les dons de parts sociales.
	- ADMIN et SUPERADMIN : voient tous les dons
	- MEMBRE : voit uniquement les dons de ses propres souscriptions
	- CLIENT : pas d'accès (les parts sociales sont uniquement pour les membres)
	"""
	queryset = DonnatPartSocial.objects.all()
	serializer_class = DonnatPartSocialSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les dons selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return DonnatPartSocial.objects.all()
		
		# MEMBRE voit uniquement les dons de ses propres souscriptions
		if user.user_type == 'MEMBRE' and user.membre:
			return DonnatPartSocial.objects.filter(souscription_part_social__membre=user.membre)
		
		# CLIENT n'a pas accès aux dons de parts sociales
		return DonnatPartSocial.objects.none()


@extend_schema(tags=['Membres'])
class SouscriptEpargneViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les souscriptions d'épargne.
	- ADMIN et SUPERADMIN : voient toutes les souscriptions
	- MEMBRE : voit uniquement ses propres souscriptions d'épargne
	- CLIENT : voit uniquement ses propres souscriptions d'épargne
	"""
	queryset = SouscriptEpargne.objects.all()
	serializer_class = SouscriptEpargneSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les souscriptions d'épargne selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return SouscriptEpargne.objects.all()
		
		# MEMBRE voit uniquement ses propres souscriptions d'épargne
		if user.user_type == 'MEMBRE' and user.membre:
			return SouscriptEpargne.objects.filter(compte__titulaire_membre=user.membre)
		
		# CLIENT voit uniquement ses propres souscriptions d'épargne
		if user.user_type == 'CLIENT' and user.client:
			return SouscriptEpargne.objects.filter(compte__titulaire_client=user.client)
		
		# Par défaut, retourner un queryset vide
		return SouscriptEpargne.objects.none()

@extend_schema(tags=['Membres'])
class DonnatEpargneViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les dons d'épargne.
	- ADMIN et SUPERADMIN : voient tous les dons
	- MEMBRE : voit uniquement les dons de ses propres souscriptions d'épargne
	- CLIENT : voit uniquement les dons de ses propres souscriptions d'épargne
	"""
	queryset = DonnatEpargne.objects.all()
	serializer_class = DonnatEpargneSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les dons d'épargne selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return DonnatEpargne.objects.all()
		
		# MEMBRE voit uniquement les dons de ses propres souscriptions d'épargne
		if user.user_type == 'MEMBRE' and user.membre:
			return DonnatEpargne.objects.filter(souscriptEpargne__compte__titulaire_membre=user.membre)
		
		# CLIENT voit uniquement les dons de ses propres souscriptions d'épargne
		if user.user_type == 'CLIENT' and user.client:
			return DonnatEpargne.objects.filter(souscriptEpargne__compte__titulaire_client=user.client)
		
		# Par défaut, retourner un queryset vide
		return DonnatEpargne.objects.none()

@extend_schema(tags=['Membres'])
class RetraitViewSet(viewsets.ModelViewSet):
	"""
	ViewSet pour les retraits d'épargne.
	- ADMIN et SUPERADMIN : voient tous les retraits
	- MEMBRE : voit uniquement les retraits de ses propres souscriptions d'épargne
	- CLIENT : voit uniquement les retraits de ses propres souscriptions d'épargne
	"""
	queryset = Retrait.objects.all()
	serializer_class = RetraitSerializer
	pagination_class = StandardResultsSetPagination
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		"""Filtre les retraits selon le type d'utilisateur connecté"""
		user = self.request.user
		
		# ADMIN et SUPERADMIN voient tout
		if user.user_type in ['ADMIN', 'SUPERADMIN']:
			return Retrait.objects.all()
		
		# MEMBRE voit uniquement les retraits de ses propres souscriptions d'épargne
		if user.user_type == 'MEMBRE' and user.membre:
			return Retrait.objects.filter(souscriptEpargne__compte__titulaire_membre=user.membre)
		
		# CLIENT voit uniquement les retraits de ses propres souscriptions d'épargne
		if user.user_type == 'CLIENT' and user.client:
			return Retrait.objects.filter(souscriptEpargne__compte__titulaire_client=user.client)
		
		# Par défaut, retourner un queryset vide
		return Retrait.objects.none()
