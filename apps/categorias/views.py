from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from .forms import CategoriaForm
from .models import Categoria
from ..shared.mixins import ClienteQuerySetMixin, ClienteCreateMixin, ClienteObjectMixin


class CategoriaListView(ClienteQuerySetMixin, LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'categorias/categoria_list.html'
    context_object_name = 'categoria'

    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome')
        status = self.request.GET.get('status')
        descricao = self.request.GET.get('descricao')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if descricao:
            queryset = queryset.filter(nome__icontains=descricao)
        if status == 'true':
            queryset = queryset.filter(status=True)
        if status == 'false':
            queryset = queryset.filter(status=False)

        return queryset


class CategoriaCreateView(ClienteCreateMixin, LoginRequiredMixin, CreateView):
    model = Categoria
    template_name = 'categorias/categoria_edit.html'
    form_class = CategoriaForm
    success_url = reverse_lazy('categorias:categoria_list')


class CategoriaDetailView(ClienteObjectMixin, LoginRequiredMixin, DetailView):
    model = Categoria
    template_name = 'categorias/detalhe_categoria.html'


class CategoriaUpdateView(ClienteObjectMixin, LoginRequiredMixin, UpdateView):
    model = Categoria
    template_name = 'categorias/categoria_edit.html'
    form_class = CategoriaForm
    success_url = reverse_lazy('categorias:categoria_list')


class CategoriaDeleteView(ClienteObjectMixin, LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'categorias/deleta_categoria.html'
    success_url = reverse_lazy('categorias:categoria_list')