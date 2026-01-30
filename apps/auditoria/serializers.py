from rest_framework import serializers
from .models import Auditoria, AuditoriaItem, AuditoriaHistorico
from apps.ativos.models import Ativo
from apps.authentication.models import User


class AtivoSimplificadoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para ativo dentro de AuditoriaItem"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    localizacao_nome = serializers.CharField(source='localizacao.nome', read_only=True)
    status_nome = serializers.CharField(source='status.nome', read_only=True)

    class Meta:
        model = Ativo
        fields = [
            'id', 'etiqueta', 'nome', 'numero_serie',
            'categoria_nome', 'localizacao_nome', 'status_nome'
        ]


class UsuarioSimplificadoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para usuário"""
    nome_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'nome_completo']

    def get_nome_completo(self, obj):
        return obj.get_full_name() or obj.username


class AuditoriaItemSerializer(serializers.ModelSerializer):
    """Serializer para itens da auditoria"""
    ativo = AtivoSimplificadoSerializer(read_only=True)
    ativo_id = serializers.PrimaryKeyRelatedField(
        queryset=Ativo.objects.all(),
        source='ativo',
        write_only=True
    )
    verificado_por = UsuarioSimplificadoSerializer(read_only=True)
    estado_fisico_display = serializers.CharField(source='get_estado_fisico_display', read_only=True)

    class Meta:
        model = AuditoriaItem
        fields = [
            'id', 'auditoria', 'ativo', 'ativo_id', 'verificado',
            'data_verificacao', 'verificado_por', 'observacao',
            'estado_fisico', 'estado_fisico_display', 'localizacao_real',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'data_verificacao']


class AuditoriaHistoricoSerializer(serializers.ModelSerializer):
    """Serializer para histórico da auditoria"""
    usuario = UsuarioSimplificadoSerializer(read_only=True)

    class Meta:
        model = AuditoriaHistorico
        fields = ['id', 'auditoria', 'acao', 'descricao', 'usuario', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditoriaListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de auditorias (resumido)"""
    localizacao_nome = serializers.CharField(source='localizacao.nome', read_only=True)
    responsavel = UsuarioSimplificadoSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progresso = serializers.SerializerMethodField()

    class Meta:
        model = Auditoria
        fields = [
            'id', 'titulo', 'localizacao', 'localizacao_nome',
            'responsavel', 'status', 'status_display',
            'data_inicio', 'data_finalizacao',
            'total_ativos', 'ativos_verificados', 'ativos_nao_encontrados',
            'progresso', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'data_inicio', 'data_finalizacao',
            'total_ativos', 'ativos_verificados', 'ativos_nao_encontrados',
            'created_at', 'updated_at'
        ]

    def get_progresso(self, obj):
        return obj.calcular_progresso()


class AuditoriaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da auditoria"""
    localizacao_nome = serializers.CharField(source='localizacao.nome', read_only=True)
    responsavel = UsuarioSimplificadoSerializer(read_only=True)
    responsavel_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='responsavel',
        write_only=True,
        required=False
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progresso = serializers.SerializerMethodField()
    itens = AuditoriaItemSerializer(many=True, read_only=True)
    historico = AuditoriaHistoricoSerializer(many=True, read_only=True)

    class Meta:
        model = Auditoria
        fields = [
            'id', 'titulo', 'localizacao', 'localizacao_nome',
            'responsavel', 'responsavel_id', 'status', 'status_display',
            'data_inicio', 'data_finalizacao', 'observacoes',
            'total_ativos', 'ativos_verificados', 'ativos_nao_encontrados',
            'progresso', 'itens', 'historico',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'data_inicio', 'data_finalizacao',
            'total_ativos', 'ativos_verificados', 'ativos_nao_encontrados',
            'created_at', 'updated_at'
        ]

    def get_progresso(self, obj):
        return obj.calcular_progresso()


class AuditoriaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de auditoria"""

    class Meta:
        model = Auditoria
        fields = ['titulo', 'localizacao', 'responsavel', 'observacoes']

    def create(self, validated_data):
        # Cria a auditoria
        auditoria = Auditoria.objects.create(**validated_data)

        # Busca todos os ativos da localização
        ativos = Ativo.objects.filter(
            cliente=auditoria.cliente,
            localizacao=auditoria.localizacao
        )

        # Cria os itens da auditoria
        for ativo in ativos:
            AuditoriaItem.objects.create(
                auditoria=auditoria,
                ativo=ativo
            )

        # Atualiza o total de ativos
        auditoria.total_ativos = ativos.count()
        auditoria.save()

        # Registra no histórico
        AuditoriaHistorico.objects.create(
            auditoria=auditoria,
            acao='Criação',
            descricao=f'Auditoria criada com {ativos.count()} ativos via API',
            usuario=self.context['request'].user if 'request' in self.context else None
        )

        return auditoria


class BuscarAtivoSerializer(serializers.Serializer):
    """Serializer para buscar ativo por código/etiqueta"""
    codigo = serializers.CharField(max_length=100, required=True)


class VerificarItemSerializer(serializers.Serializer):
    """Serializer para verificar item da auditoria"""
    estado_fisico = serializers.ChoiceField(
        choices=['otimo', 'bom', 'regular', 'ruim'],
        required=False,
        allow_blank=True
    )
    localizacao_real = serializers.CharField(max_length=200, required=False, allow_blank=True)
    observacao = serializers.CharField(required=False, allow_blank=True)


class FinalizarAuditoriaSerializer(serializers.Serializer):
    """Serializer para finalizar auditoria"""
    observacoes_finais = serializers.CharField(required=False, allow_blank=True)


class EstatisticasAuditoriaSerializer(serializers.Serializer):
    """Serializer para estatísticas da auditoria"""
    total_ativos = serializers.IntegerField()
    ativos_verificados = serializers.IntegerField()
    ativos_pendentes = serializers.IntegerField()
    progresso = serializers.FloatField()
    por_estado = serializers.DictField()
    tempo_decorrido = serializers.CharField()