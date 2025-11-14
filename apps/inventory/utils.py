import winrm
from .models import Machine

def send_notification_logic(machine_id, title, message):
    """
    Envia uma notificação via msg.exe para a máquina remota identificada por machine_id.
    Lança RuntimeError em caso de falha.
    """
    # 1. Recupera a máquina e seu IP
    machine = Machine.objects.get(id=machine_id)
    ip = machine.ip_address
    if not ip:
        raise RuntimeError(f"Máquina {machine.hostname} não possui IP cadastrado.")

    # 2. Prepara a mensagem (título + corpo), evita aspas que quebrem o comando
    full_msg = f"{title}\r\n{message}".replace('"', '')

    # 3. Cria sessão WinRM
    session = winrm.Session(
        f"http://{ip}:5985/wsman",
        auth=('admin', 'senha'),               # ← ajuste para suas credenciais
        server_cert_validation='ignore'
    )

    # 4. Executa msg.exe na sessão remota
    result = session.run_cmd('msg', ['*', '/TIME:5', full_msg])

    # 5. Verifica retorno
    if result.status_code != 0:
        err = (result.std_err.decode('utf-8', errors='ignore') or
               f"Exit code {result.status_code}").strip()
        raise RuntimeError(f"Falha ao enviar notificação para {machine.hostname}: {err}")

    return result.std_out.decode('utf-8', errors='ignore').strip()
