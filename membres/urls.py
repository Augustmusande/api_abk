from rest_framework.routers import DefaultRouter
from .views import PartSocialViewSet, FraisAdhesionViewSet, DonnatPartSocialViewSet, SouscriptEpargneViewSet, DonnatEpargneViewSet, CompteViewSet, SouscriptionPartSocialViewSet, RetraitViewSet



router = DefaultRouter()
router.register(r'partsociaux', PartSocialViewSet)
router.register(r'souscriptionpartsociaux', SouscriptionPartSocialViewSet, basename='souscriptionpartsocial')
router.register(r'fraisadhesion', FraisAdhesionViewSet)
router.register(r'donnatpartsociaux', DonnatPartSocialViewSet)



router.register(r'souscriptepargne', SouscriptEpargneViewSet)
router.register(r'donnatepargne', DonnatEpargneViewSet)
router.register(r'retraits', RetraitViewSet)
router.register(r'comptes', CompteViewSet)

urlpatterns = router.urls
