from import_export import resources
from .models import Categoria

class CategoriaResource(resources.ModelResource):
    class Meta:
        model = Categoria
        fields = ('nome', 'descricao', 'status', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('nome',)