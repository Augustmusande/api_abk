
from rest_framework.routers import DefaultRouter
from .views import CreditViewSet, RemboursementViewSet


router = DefaultRouter()
router.register(r'credits', CreditViewSet, basename='credit')
router.register(r'remboursements', RemboursementViewSet, basename='remboursement')

urlpatterns = router.urls
