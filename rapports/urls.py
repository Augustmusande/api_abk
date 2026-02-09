"""
URLs pour l'application rapports
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RapportViewSet, EnvoiEmailViewSet, ReceiptViewSet

router = DefaultRouter()
router.register(r'rapports', RapportViewSet, basename='rapport')
router.register(r'envois-emails', EnvoiEmailViewSet, basename='envoi-email')
router.register(r'receipts', ReceiptViewSet, basename='receipt')

urlpatterns = [
    path('', include(router.urls)),
]

