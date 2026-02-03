import os
import sys
import time
import json
import socket
import platform
import subprocess
import threading
import hashlib
import urllib.request
import urllib.error
import ssl
from datetime import datetime

# Configurações do Agente
VERSION = "2.0.0"
UPDATE_CHECK_INTERVAL = 3600  # 1 hora
HEARTBEAT_INTERVAL = 300  # 5 minutos
OFFLINE_CHECK_INTERVAL = 120  # 1 minuto


# Configurações são passadas via argumentos ou variáveis de ambiente
# NÃO salva em arquivos


class AgentConfig:
    """Gerenciador de configurações do agente via ambiente/argumentos"""

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """Carrega configurações de variáveis de ambiente"""
        return {
            "server_url": os.environ.get("AGENT_SERVER_URL", "http://192.168.1.54:5001"),
            "token_hash": os.environ.get("AGENT_TOKEN_HASH", ""),
            "machine_name": socket.gethostname(),
            "version": VERSION,
            "auto_update": os.environ.get("AGENT_AUTO_UPDATE", "true").lower() == "true",
            "notifications": os.environ.get("AGENT_NOTIFICATIONS", "true").lower() == "true",
            "check_interval": int(os.environ.get("AGENT_CHECK_INTERVAL", HEARTBEAT_INTERVAL))
        }

    def get(self, key, default=None):
        """Obtém valor de configuração"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Define valor de configuração (apenas em memória)"""
        self.config[key] = value


class TokenValidator:
    """Validador de token de instalação"""

    @staticmethod
    def hash_token(token):
        """Cria hash do token"""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def validate_with_server(server_url, token_hash, machine_name):
        """Valida token diretamente com o servidor"""
        try:
            url = f"{server_url}/api/inventory/agent/validate/"

            data = json.dumps({
                'token_hash': token_hash,
                'machine_name': machine_name
            }).encode()

            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                result = json.loads(response.read().decode())
                return result.get('valid', False)

        except Exception as e:
            print(f"❌ Erro ao validar token: {e}")
            return False


class NotificationManager:
    """Gerenciador de notificações do sistema"""

    @staticmethod
    def notify_windows_native(title, message):
        """Envia notificação nativa do Windows usando winotify"""
        if platform.system() != "Windows":
            return False

        try:
            from winotify import Notification

            toast = Notification(
                app_id="Agente de Inventário",
                title=title,
                msg=message,
                duration="short"
            )
            toast.show()
            return True

        except ImportError:
            return False
        except Exception as e:
            print(f"⚠️  Erro ao enviar notificação Windows: {e}")
            return False

    @staticmethod
    def notify_windows_powershell(title, message):
        """Envia notificação via PowerShell (fallback)"""
        try:
            title_escaped = title.replace('"', '`"')
            message_escaped = message.replace('"', '`"')

            ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{title_escaped}</text>
            <text id="2">{message_escaped}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Agente de Inventário").Show($toast)
'''

            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            return result.returncode == 0

        except Exception as e:
            print(f"⚠️  Erro ao enviar notificação PowerShell: {e}")
            return False

    @staticmethod
    def send_notification(title, message, priority="normal", icon_type="info"):
        """Envia notificação usando o melhor método disponível"""
        icon_console = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        print(f"{icon_console.get(icon_type, 'ℹ️')} {title}: {message}")

        if platform.system() != "Windows":
            return

        # Tenta métodos em ordem de preferência
        methods = [
            lambda: NotificationManager.notify_windows_native(title, message),
            lambda: NotificationManager.notify_windows_powershell(title, message),
        ]

        for method in methods:
            try:
                if method():
                    return
            except:
                continue


class NetworkMonitor:
    """Monitor de conectividade de rede"""

    def __init__(self, config):
        self.config = config
        self.is_online = False
        self.last_check = None
        self.consecutive_failures = 0

    def check_internet(self, host="8.8.8.8", port=53, timeout=3):
        """Verifica conectividade com a internet"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False

    def check_server(self):
        """Verifica conectividade com o servidor"""
        try:
            url = self.config.get('server_url') + '/api/inventory/health/'

            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, method='GET')

            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                return response.status == 200
        except Exception:
            return False

    def update_status(self):
        """Atualiza status de conectividade"""
        self.last_check = datetime.now()

        internet_ok = self.check_internet()

        if not internet_ok:
            if self.is_online:
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    self.is_online = False
                    return "offline"
            return "offline"

        server_ok = self.check_server()

        if server_ok:
            self.consecutive_failures = 0
            if not self.is_online:
                self.is_online = True
                return "reconnected"
            return "online"
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 3 and self.is_online:
                self.is_online = False
                return "offline"
            return "degraded"


class AutoUpdater:
    """Sistema de auto-atualização do agente"""

    def __init__(self, config):
        self.config = config
        self.current_version = VERSION

    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        if not self.config.get('auto_update'):
            return None

        try:
            url = self.config.get('server_url') + '/api/inventory/agent/update/'

            data = json.dumps({
                'current_version': self.current_version,
                'machine_name': self.config.get('machine_name')
            }).encode()

            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                result = json.loads(response.read().decode())

                if result.get('update_available'):
                    return result

        except Exception as e:
            print(f"⚠️  Erro ao verificar atualizações: {e}")

        return None

    def download_update(self, update_info):
        """Baixa e aplica atualização"""
        try:
            download_url = update_info.get('download_url')
            new_version = update_info.get('version')

            print(f"⬇️  Baixando atualização {new_version}...")

            if self.config.get('notifications'):
                NotificationManager.send_notification(
                    "Atualizando Agente",
                    f"Baixando versão {new_version}...",
                    priority="normal",
                    icon_type="info"
                )

            context = ssl._create_unverified_context()
            req = urllib.request.Request(download_url)

            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                new_content = response.read()

            # Backup do arquivo atual
            current_file = os.path.abspath(__file__)
            backup_file = current_file + '.bak'

            if os.path.exists(backup_file):
                os.remove(backup_file)

            # Cria backup
            with open(current_file, 'rb') as f:
                with open(backup_file, 'wb') as b:
                    b.write(f.read())

            # Salva novo arquivo
            with open(current_file, 'wb') as f:
                f.write(new_content)

            print(f"✅ Atualização instalada! Reiniciando...")

            if self.config.get('notifications'):
                NotificationManager.send_notification(
                    "Agente Atualizado",
                    f"Versão {new_version} instalada. Reiniciando...",
                    priority="normal",
                    icon_type="success"
                )

            time.sleep(2)

            # Reinicia o agente
            os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            print(f"❌ Erro ao aplicar atualização: {e}")

            if self.config.get('notifications'):
                NotificationManager.send_notification(
                    "Erro na Atualização",
                    "Não foi possível atualizar o agente.",
                    priority="high",
                    icon_type="error"
                )

            # Restaura backup
            current_file = os.path.abspath(__file__)
            backup_file = current_file + '.bak'

            if os.path.exists(backup_file):
                with open(backup_file, 'rb') as b:
                    with open(current_file, 'wb') as f:
                        f.write(b.read())


class SystemCollector:
    """Coletor de informações do sistema"""

    @staticmethod
    def get_system_info():
        """Coleta informações completas do sistema"""
        info = {
            'hostname': socket.gethostname(),
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'agent_version': VERSION,
            'last_update': datetime.now().isoformat(),
        }

        # Informações de rede
        try:
            info['ip_address'] = socket.gethostbyname(socket.gethostname())
        except:
            info['ip_address'] = "127.0.0.1"

        # Informações de disco (Windows)
        if platform.system() == "Windows":
            try:
                import ctypes

                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p("C:\\"),
                    None,
                    ctypes.pointer(total_bytes),
                    ctypes.pointer(free_bytes)
                )

                info['disk_total_gb'] = round(total_bytes.value / (1024 ** 3), 2)
                info['disk_free_gb'] = round(free_bytes.value / (1024 ** 3), 2)
                info['disk_used_gb'] = round((total_bytes.value - free_bytes.value) / (1024 ** 3), 2)
            except:
                pass

        # Memória RAM (Windows)
        if platform.system() == "Windows":
            try:
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                memstatus = MEMORYSTATUSEX()
                memstatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memstatus))

                info['ram_total_gb'] = round(memstatus.ullTotalPhys / (1024 ** 3), 2)
                info['ram_available_gb'] = round(memstatus.ullAvailPhys / (1024 ** 3), 2)
                info['ram_used_gb'] = round((memstatus.ullTotalPhys - memstatus.ullAvailPhys) / (1024 ** 3), 2)
            except:
                pass

        return info

    @staticmethod
    def send_data(config, data):
        """Envia dados para o servidor com autenticação por token hash"""
        try:
            url = config.get('server_url') + config.get('api_endpoint', '/api/checkin/')

            # Adiciona hash do token para autenticação
            data['token_hash'] = config.get('token_hash')

            json_data = json.dumps(data).encode()

            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                return response.status == 200 or response.status == 201

        except Exception as e:
            print(f"⚠️  Erro ao enviar dados: {e}")
            return False


class InventoryAgent:
    """Agente principal de inventário"""

    def __init__(self, token=None):
        self.config = AgentConfig()

        # Se token foi passado, processa
        if token:
            token_hash = TokenValidator.hash_token(token)
            self.config.set('token_hash', token_hash)

            # Valida com servidor
            if not TokenValidator.validate_with_server(
                    self.config.get('server_url'),
                    token_hash,
                    self.config.get('machine_name')
            ):
                raise ValueError("Token inválido ou expirado")

        # Token deve estar nas variáveis de ambiente
        elif not self.config.get('token_hash'):
            raise ValueError("Token não configurado. Use variável de ambiente AGENT_TOKEN_HASH")

        self.network = NetworkMonitor(self.config)
        self.updater = AutoUpdater(self.config)
        self.running = False
        self.last_status = None

    def start(self):
        """Inicia o agente"""
        print("=" * 60)
        print(f"🚀 Agente de Inventário v{VERSION}")
        print("=" * 60)
        print(f"📍 Máquina: {self.config.get('machine_name')}")
        print(f"🌐 Servidor: {self.config.get('server_url')}")
        print(f"⚙️  Auto-update: {'Ativado' if self.config.get('auto_update') else 'Desativado'}")
        print(f"🔔 Notificações: {'Ativadas' if self.config.get('notifications') else 'Desativadas'}")
        print(f"🔒 Seguro: Sem arquivos sensíveis salvos")
        print("=" * 60)

        self.running = True

        # Notifica inicialização
        if self.config.get('notifications'):
            NotificationManager.send_notification(
                "Agente Iniciado",
                "Agente de inventário está rodando.",
                priority="normal",
                icon_type="info"
            )

        # Thread para verificação de conectividade
        threading.Thread(target=self.network_monitor_loop, daemon=True).start()

        # Thread para envio de dados
        threading.Thread(target=self.data_sender_loop, daemon=True).start()

        # Thread para verificação de atualizações
        threading.Thread(target=self.update_checker_loop, daemon=True).start()

        print("\n✅ Agente iniciado com sucesso!")
        print("Rodando como serviço em segundo plano...\n")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Parando agente...")
            self.stop()

    def stop(self):
        """Para o agente"""
        self.running = False

        if self.config.get('notifications'):
            NotificationManager.send_notification(
                "Agente Parado",
                "Agente de inventário foi encerrado.",
                priority="normal",
                icon_type="info"
            )

    def network_monitor_loop(self):
        """Loop de monitoramento de rede"""
        while self.running:
            status = self.network.update_status()

            if status != self.last_status and self.config.get('notifications'):
                if status == "offline":
                    NotificationManager.send_notification(
                        "Agente Offline",
                        "Conexão com o servidor perdida.",
                        priority="high",
                        icon_type="warning"
                    )
                    print("🔴 Status: OFFLINE")

                elif status == "reconnected":
                    NotificationManager.send_notification(
                        "Agente Online",
                        "Conexão com o servidor restaurada.",
                        priority="normal",
                        icon_type="success"
                    )
                    print("🟢 Status: ONLINE")

                self.last_status = status

            time.sleep(OFFLINE_CHECK_INTERVAL)

    def data_sender_loop(self):
        """Loop de envio de dados"""
        while self.running:
            if self.network.is_online:
                try:
                    data = SystemCollector.get_system_info()
                    if SystemCollector.send_data(self.config, data):
                        print(f"📤 Dados enviados: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    print(f"⚠️  Erro no envio de dados: {e}")

            time.sleep(self.config.get('check_interval'))

    def update_checker_loop(self):
        """Loop de verificação de atualizações"""
        while self.running:
            if self.network.is_online:
                try:
                    update_info = self.updater.check_for_updates()
                    if update_info:
                        print(f"🔄 Atualização disponível: {update_info.get('version')}")

                        if self.config.get('notifications'):
                            NotificationManager.send_notification(
                                "Atualização Disponível",
                                f"Nova versão {update_info.get('version')} disponível. Atualizando...",
                                priority="normal",
                                icon_type="info"
                            )

                        self.updater.download_update(update_info)

                except Exception as e:
                    print(f"⚠️  Erro na verificação de atualizações: {e}")

            time.sleep(UPDATE_CHECK_INTERVAL)


def main():
    """Função principal"""

    # Verifica se token foi passado como argumento (primeira execução)
    token = None
    if len(sys.argv) > 1 and sys.argv[1].startswith('--token='):
        token = sys.argv[1].split('=')[1]

    try:
        agent = InventoryAgent(token=token)
        agent.start()
    except ValueError as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Agente interrompido")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()