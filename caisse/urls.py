"""
URLs - APPLICATION CAISSE
"""

from rest_framework.routers import DefaultRouter
from .views import CalculsFinanciersViewSet, DepensesViewSet, CaisseTypeViewSet, CaissetypemvtViewSet, DonDirectViewSet

router = DefaultRouter()

# Enregistrement des viewsets
router.register(r'calculs', CalculsFinanciersViewSet, basename='calculs-financiers')
router.register(r'depenses', DepensesViewSet, basename='depenses')
router.register(r'dons-directs', DonDirectViewSet, basename='dons-directs')
router.register(r'caissetypes', CaisseTypeViewSet, basename='caissetypes')
router.register(r'caissetypemvt', CaissetypemvtViewSet, basename='caissetypemvt')

urlpatterns = router.urls

