"""
Pagination personnalisée pour l'API COOPEC
15 enregistrements par page
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard : 15 enregistrements par page
    Page 1 : enregistrements 1-15 (les 15 derniers)
    Page 2 : enregistrements 16-30
    etc.
    """
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Retourne une réponse paginée avec les métadonnées
        """
        return Response({
            'count': self.page.paginator.count,  # Nombre total d'enregistrements
            'next': self.get_next_link(),  # URL de la page suivante
            'previous': self.get_previous_link(),  # URL de la page précédente
            'page_size': self.page_size,  # Taille de la page
            'current_page': self.page.number,  # Page actuelle
            'total_pages': self.page.paginator.num_pages,  # Nombre total de pages
            'results': data  # Les données de la page actuelle
        })

