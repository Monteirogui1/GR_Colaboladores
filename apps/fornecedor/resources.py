from import_export import resources
from .models import Fornecedor

class FornecedorResource(resources.ModelResource):
    class Meta:
        model = Fornecedor
        fields = ('nome', 'contato', 'email', 'descricao', 'status', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('nome',)