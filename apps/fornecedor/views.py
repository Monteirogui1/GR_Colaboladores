from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from .forms import FornecedorForm
from .models import Fornecedor
from ..shared.mixins import ClienteQuerySetMixin, ClienteCreateMixin, ClienteObjectMixin

app_name = 'fornecedores'


class FornecedorListView(ClienteQuerySetMixin, LoginRequiredMixin, ListView):
    model = Fornecedor
    template_name = 'fornecedor/fornecedores_list.html'
    context_object_name = 'fornecedores'

    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome')
        status = self.request.GET.get('status')
        contato = self.request.GET.get('contato')
        email = self.request.GET.get('email')
        descricao = self.request.GET.get('descricao')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if descricao:
            queryset = queryset.filter(nome__icontains=descricao)
        if contato:
            queryset = queryset.filter(contato__icontains=contato)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if status == 'true':
            queryset = queryset.filter(status=True)
        if status == 'false':
            queryset = queryset.filter(status=False)

        return queryset


class FornecedorCreateView(ClienteCreateMixin, LoginRequiredMixin, CreateView):
    model = Fornecedor
    template_name = 'fornecedor/fornecedores_edit.html'
    form_class = FornecedorForm
    success_url = reverse_lazy('fornecedores:fornecedores_list')


class FornecedorDetailView(ClienteObjectMixin, LoginRequiredMixin, DetailView):
    model = Fornecedor
    template_name = 'fornecedor/fornecedores_detail.html'


class FornecedorUpdateView(ClienteObjectMixin, LoginRequiredMixin, UpdateView):
    model = Fornecedor
    template_name = 'fornecedor/fornecedores_edit.html'
    form_class = FornecedorForm
    success_url = reverse_lazy('fornecedores:fornecedores_list')


class FornecedorDeleteView(ClienteObjectMixin, LoginRequiredMixin, DeleteView):
    model = Fornecedor
    template_name = 'fornecedor/deleta_fornecedor.html'
    success_url = reverse_lazy('fornecedores:fornecedores_list')