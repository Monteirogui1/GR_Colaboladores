from import_export import resources
from .models import Marca

class MarcaResource(resources.ModelResource):
    class Meta:
        model = Marca
        fields = ('nome', 'descricao', 'status', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('nome',)