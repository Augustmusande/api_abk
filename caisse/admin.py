from django.contrib import admin
from .models import Depenses


@admin.register(Depenses)
class DepensesAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'quantite', 'uniter', 'pu', 'get_pt', 'date_depense', 'created_at')
    list_filter = ('date_depense', 'created_at')
    search_fields = ('libelle',)
    readonly_fields = ('get_pt', 'created_at', 'updated_at')
    date_hierarchy = 'date_depense'
    
    fieldsets = (
        ('Informations de la dépense', {
            'fields': ('libelle', 'uniter', 'quantite', 'pu', 'get_pt', 'date_depense')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_pt(self, obj):
        """
        Affiche le prix total calculé dynamiquement.
        """
        return f"{obj.pt} FCFA"
    get_pt.short_description = "Prix total"
