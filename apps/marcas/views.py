from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from .forms import MarcaForm
from .models import Marca
from ..shared.mixins import ClienteQuerySetMixin, ClienteCreateMixin, ClienteObjectMixin


class MarcaListView(ClienteQuerySetMixin, LoginRequiredMixin, ListView):
    model = Marca
    template_name = 'marcas/marca_list.html'
    context_object_name = 'marca'

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


class MarcaCreateView(ClienteCreateMixin, LoginRequiredMixin, CreateView):
    model = Marca
    template_name = 'marcas/marca_edit.html'
    form_class = MarcaForm
    success_url = reverse_lazy('marcas:marca_list')


class MarcaDetailView(ClienteObjectMixin, LoginRequiredMixin, DetailView):
    model = Marca
    template_name = 'marcas/detalhe_marca.html'


class MarcaUpdateView(ClienteObjectMixin, LoginRequiredMixin, UpdateView):
    model = Marca
    template_name = 'marcas/marca_edit.html'
    form_class = MarcaForm
    success_url = reverse_lazy('marcas:marca_list')


class MarcaDeleteView(ClienteObjectMixin, LoginRequiredMixin, DeleteView):
    model = Marca
    template_name = 'marcas/deleta_marca.html'
    success_url = reverse_lazy('marcas:marca_list')