from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from .forms import ClienteWizardForm
from .models import Cliente
from django.contrib import messages
import subprocess
import uuid


class ClienteWizardView(LoginRequiredMixin, View):
    template_name = 'shared/cliente_wizard.html'

    def get(self, request):
        form = ClienteWizardForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ClienteWizardForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            # Gera um nome de banco único (ou defina outra lógica conforme seu padrão)
            db_name = f"cliente_{uuid.uuid4().hex[:8]}"

            try:
                # 1. Cria o banco físico (Postgres exemplo)
                res_db = subprocess.run(['createdb', db_name], capture_output=True)
                if res_db.returncode != 0:
                    messages.error(request, f'Erro ao criar banco: {res_db.stderr.decode()}')
                    return render(request, self.template_name, {'form': form})

                cliente.save()

                # 2. Roda migrações no novo banco
                res_migrate = subprocess.run(
                    ['python', 'manage.py', 'migrate', '--database', db_name],
                    capture_output=True
                )
                if res_migrate.returncode != 0:
                    messages.error(request, f'Erro nas migrações: {res_migrate.stderr.decode()}')
                    return render(request, self.template_name, {'form': form})

                # 3. Cria usuário admin inicial, se fornecido
                email_admin = form.cleaned_data.get('email_admin')
                senha_admin = form.cleaned_data.get('senha_admin')
                if email_admin and senha_admin:
                    from django.db import connections
                    from django.contrib.auth.hashers import make_password
                    with connections[db_name].cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO auth_user (username, email, is_staff, is_superuser, is_active, password, date_joined)
                            VALUES (%s, %s, TRUE, TRUE, TRUE, %s, now())
                            """,
                            [
                                'admin',
                                email_admin,
                                make_password(senha_admin)
                            ]
                        )

                messages.success(request, f'Cliente {cliente.nome} criado e banco {db_name} provisionado!')
                return redirect('admin:shared_cliente_changelist')
            except Exception as e:
                messages.error(request, f'Erro inesperado: {str(e)}')
                return render(request, self.template_name, {'form': form})

        return render(request, self.template_name, {'form': form})
