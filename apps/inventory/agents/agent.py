import os
import sys
import time
import json
import socket
import platform
import subprocess
import threading
import hashlib
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional
from pathlib import Path
import psutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurações do Agente
VERSION = "2.0.4"
UPDATE_CHECK_INTERVAL = 3600
HEARTBEAT_INTERVAL = 60
OFFLINE_CHECK_INTERVAL = 60

# Configurar logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('InventoryAgent')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'agent.log'),
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)

# Desabilitar warnings de SSL
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
            "check_interval": int(os.environ.get("AGENT_CHECK_INTERVAL", HEARTBEAT_INTERVAL)),
            "endpoint_validate": "/api/inventario/agent/validate/",
            "endpoint_checkin": "/api/inventario/checkin/",
            "endpoint_update": "/api/inventario/agent/update/",
            "endpoint_health": "/api/inventario/health/",
            "endpoint_notifications": "/api/notifications/",
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value


class RequestsSession:
    """Gerenciador de sessão HTTP com retry"""

    _session = None

    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = requests.Session()

            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)

        return cls._session


class TokenValidator:
    """Validador de token de instalação"""

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def validate_with_server(server_url, token_hash, machine_name):
        try:
            url = f"{server_url}/api/inventario/agent/validate/"

            payload = {
                'token': token_hash,
                'machine_name': machine_name
            }

            session = RequestsSession.get_session()
            response = session.post(
                url,
                json=payload,
                verify=False,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                is_valid = result.get('valid', False)
                if is_valid:
                    logger.info("Token validado com sucesso")
                else:
                    logger.error(f"Token inválido: {result.get('message')}")
                return is_valid

            logger.error(f"Erro ao validar token: HTTP {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Erro ao validar token: {e}")
            return False


class NetworkMonitor:
    """Monitor de conectividade de rede"""

    def __init__(self, config):
        self.config = config
        self.is_online = False
        self.last_check = None

    def check_connectivity(self):
        try:
            url = self.config.get('server_url') + self.config.get('endpoint_health')

            session = RequestsSession.get_session()
            response = session.get(url, verify=False, timeout=5)

            self.is_online = response.status_code == 200
            self.last_check = datetime.now()

            return self.is_online

        except requests.exceptions.RequestException:
            self.is_online = False
            self.last_check = datetime.now()
            return False


class AutoUpdater:
    """Gerenciador de atualizações automáticas"""

    def __init__(self, config):
        self.config = config

    def check_for_updates(self):
        try:
            url = self.config.get('server_url') + self.config.get('endpoint_update')

            payload = {
                'current_version': self.config.get('version'),
                'machine_name': self.config.get('machine_name')
            }

            session = RequestsSession.get_session()
            response = session.post(url, json=payload, verify=False, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('update_available'):
                    logger.info(f"Atualização disponível: {data.get('version')}")
                    return data

            return None

        except Exception as e:
            logger.error(f"Erro ao verificar atualizações: {e}")
            return None

    def download_update(self, update_info):
        if not self.config.get('auto_update'):
            logger.info("Auto-update desativado")
            return

        try:
            download_url = update_info.get('download_url')

            logger.info(f"Baixando atualização {update_info.get('version')}")

            session = RequestsSession.get_session()
            response = session.get(download_url, verify=False, timeout=30)

            if response.status_code == 200:
                current_file = os.path.abspath(__file__)
                backup_file = current_file + '.bak'

                with open(backup_file, 'wb') as f:
                    with open(current_file, 'rb') as orig:
                        f.write(orig.read())

                with open(current_file, 'wb') as f:
                    f.write(response.content)

                logger.info("Atualização aplicada com sucesso")

                time.sleep(2)
                os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            logger.error(f"Erro ao aplicar atualização: {e}")

            current_file = os.path.abspath(__file__)
            backup_file = current_file + '.bak'

            if os.path.exists(backup_file):
                with open(backup_file, 'rb') as b:
                    with open(current_file, 'wb') as f:
                        f.write(b.read())


class PowerShellCollector:
    """Coletor de informações via PowerShell - IGUAL AO AGENT.PS1"""

    POWERSHELL_SCRIPT = r'''
    $ErrorActionPreference = "SilentlyContinue"

    function Get-SystemInfo {
        # Usuário logado
        $loggedUser = ((Get-CimInstance Win32_ComputerSystem).UserName -split '\\')[-1]

        # MAC principal
        $primaryNet = Get-CimInstance Win32_NetworkAdapterConfiguration |
                      Where-Object { $_.IPEnabled } | Select-Object -First 1
        $macAddress = $primaryNet.MACAddress

        # Slots e módulos de RAM
        $arrays         = Get-CimInstance Win32_PhysicalMemoryArray
        $totalSlots     = ($arrays | Measure-Object -Property MemoryDevices -Sum).Sum
        $modules        = Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
            [pscustomobject]@{
                bank_label     = $_.BankLabel
                device_locator = $_.DeviceLocator
                capacity_gb    = [math]::Round($_.Capacity/1GB,2)
                speed_mhz      = $_.Speed
                manufacturer   = $_.Manufacturer
                part_number    = $_.PartNumber
                serial_number  = $_.SerialNumber
            }
        }
        $populatedSlots = $modules.Count

        # Antivírus: escolhe primeiro não Defender, senão o primeiro da lista
        $avList = Get-CimInstance -Namespace "root\SecurityCenter2" -ClassName AntiVirusProduct -ErrorAction SilentlyContinue
        $av = $avList | Where-Object { $_.displayName -notmatch "Defender" } | Select-Object -First 1
        if (-not $av) { $av = $avList | Select-Object -First 1 }

        # Outras infos
        $os    = Get-CimInstance Win32_OperatingSystem
        $cs    = Get-CimInstance Win32_ComputerSystem
        $bios  = Get-CimInstance Win32_BIOS
        $upt   = (Get-Date) - $os.LastBootUpTime
        $proc  = Get-CimInstance Win32_Processor
        $disk  = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        $net   = Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object IPEnabled
        $gpu   = Get-CimInstance Win32_VideoController | Select-Object -First 1

        # TPM
        try {
            $tpm = Get-Tpm
            $tpmInfo = [pscustomobject]@{
                present          = $tpm.TpmPresent
                ready            = $tpm.TpmReady
                enabled          = $tpm.TpmEnabled
                activated        = $tpm.TpmActivated
                spec_version     = $tpm.SpecVersion
                manufacturer     = $tpm.ManufacturerIdTxt
                manufacturer_ver = $tpm.ManufacturerVersion
            }
        } catch {
            $tpmInfo = [pscustomobject]@{
                present          = $false
                ready            = $false
                enabled          = $false
                activated        = $false
                spec_version     = $null
                manufacturer     = $null
                manufacturer_ver = $null
            }
        }

        # Converter datas para timestamp JSON
        $installDateJson = $null
        if ($os.InstallDate) {
            $installDateJson = "/Date($([Math]::Floor((Get-Date $os.InstallDate).ToUniversalTime().Subtract((Get-Date '1970-01-01')).TotalMilliseconds)))/"
        }

        $lastBootJson = $null
        if ($os.LastBootUpTime) {
            $lastBootJson = "/Date($([Math]::Floor((Get-Date $os.LastBootUpTime).ToUniversalTime().Subtract((Get-Date '1970-01-01')).TotalMilliseconds)))/"
        }

        $biosReleaseJson = $null
        if ($bios.ReleaseDate) {
            $biosReleaseJson = "/Date($([Math]::Floor((Get-Date $bios.ReleaseDate).ToUniversalTime().Subtract((Get-Date '1970-01-01')).TotalMilliseconds)))/"
        }

        # Espaço em disco usado
        $diskUsedGb = [math]::Round(($disk.Size - $disk.FreeSpace)/1GB, 2)

        # IP Address
        $ipAddress = if ($primaryNet.IPAddress) { $primaryNet.IPAddress[0] } else { "127.0.0.1" }

        $result = [pscustomobject]@{
            hostname               = $env:COMPUTERNAME
            ip_address             = $ipAddress
            logged_user            = $loggedUser

            manufacturer           = $cs.Manufacturer
            model                  = $cs.Model
            serial_number          = $bios.SerialNumber
            bios_version           = $bios.SMBIOSBIOSVersion
            bios_release           = $biosReleaseJson

            os_caption             = $os.Caption
            os_architecture        = $os.OSArchitecture
            os_build               = $os.BuildNumber
            install_date           = $os.InstallDate
            last_boot              = $os.LastBootUpTime
            uptime_days            = [math]::Round($upt.TotalDays,2)

            cpu                    = $proc.Name
            ram_gb                 = [math]::Round(($cs.TotalPhysicalMemory/1GB),2)
            disk_space_gb          = [math]::Round($disk.Size/1GB,2)
            disk_free_gb           = [math]::Round($disk.FreeSpace/1GB,2)
            disk_used_gb           = $diskUsedGb

            mac_address            = $macAddress
            total_memory_slots     = $totalSlots
            populated_memory_slots = $populatedSlots
            memory_modules         = @($modules)

            network_adapters       = @($net | ForEach-Object {
                [pscustomobject]@{
                    name    = $_.Description
                    mac     = $_.MACAddress
                    ip      = ($_.IPAddress -join ",")
                    gateway = ($_.DefaultIPGateway -join ",")
                    dns     = ($_.DNSServerSearchOrder -join ",")
                    dhcp    = $_.DHCPEnabled
                }
            })

            gpu_name               = $gpu.Name
            gpu_driver             = $gpu.DriverVersion

            antivirus_name         = $av.displayName
            av_state               = if ($av.productState) { $av.productState.ToString() } else { $null }

            tpm                    = $tpmInfo
        }

        return $result | ConvertTo-Json -Depth 10 -Compress
    }

    # Executar e retornar JSON
    Get-SystemInfo
    '''

    @staticmethod
    def get_system_info():
        """Executa PowerShell e retorna informações coletadas"""
        try:
            logger.info("Coletando informações via PowerShell...")

            # Executar PowerShell
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                 PowerShellCollector.POWERSHELL_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )

            if result.returncode != 0:
                logger.error(f"PowerShell erro: {result.stderr}")
                raise Exception(f"PowerShell retornou código {result.returncode}")

            # Parse do JSON retornado
            output = result.stdout.strip()

            if not output:
                raise Exception("PowerShell não retornou dados")

            data = json.loads(output)

            logger.info(f"Dados coletados com sucesso: {data.get('hostname')}")

            return data

        except subprocess.TimeoutExpired:
            logger.error("Timeout ao executar PowerShell")
            raise Exception("Timeout na coleta de dados")

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON do PowerShell: {e}")
            logger.error(f"Output recebido: {result.stdout}")
            raise Exception("Dados inválidos retornados pelo PowerShell")

        except Exception as e:
            logger.error(f"Erro ao coletar informações via PowerShell: {e}")
            raise

    @staticmethod
    def send_data(config, data):
        """Envia dados para o servidor - FORMATO IGUAL AO POWERSHELL"""
        try:
            url = config.get('server_url') + config.get("endpoint_checkin")

            # FORMATO IDÊNTICO AO POWERSHELL
            payload = {
                "hostname": data["hostname"],
                "ip": data.get("ip_address", ""),
                "hardware": data,
                "token": config.get("token_hash")
            }

            logger.info(f"Enviando dados para {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            session = RequestsSession.get_session()
            response = session.post(
                url,
                json=payload,
                verify=False,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info("Dados enviados com sucesso")
                return True
            else:
                logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return False

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão: {e}")
            return False
        except requests.exceptions.Timeout:
            logger.error("Timeout na requisição")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar dados: {e}")
            return False


class NotificationManager:
    """
    Gerenciador de notificações usando sistema nativo do Windows

    Features:
    - Toast notifications via PowerShell
    - Busca notificações do servidor
    - Marca como lida automaticamente
    - Histórico local para evitar duplicatas
    """

    NOTIFICATION_CHECK_INTERVAL = 120  # segundos (2 minutos)
    NOTIFICATION_DISPLAY_DELAY = 2  # segundos entre notificações

    def __init__(self, config):
        """
        Inicializa o gerenciador de notificações

        Args:
            config (dict): Configuração do agente com server_url, machine_name, etc.
        """
        self.config = config
        self.server_url = config.get('server_url', 'http://192.168.1.54:5001')
        self.endpoint = config.get('endpoint_notifications', '/api/notifications/')
        self.machine_name = config.get('machine_name', '')
        self.notifications_enabled = config.get('notifications', True)

        # Arquivo de histórico
        self.history_file = Path("logs/notification_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Carregar histórico
        self.shown_notifications = self._load_history()

        logger.info("NotificationManager inicializado (Windows Nativo)")

    def _load_history(self):
        """Carrega histórico de notificações exibidas"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('shown_notifications', []))
            except Exception as e:
                logger.warning(f"Erro ao carregar histórico: {e}")
        return set()

    def _save_history(self):
        """Salva histórico de notificações exibidas"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    'shown_notifications': list(self.shown_notifications),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")

    def send_notification(self, title, message, priority="normal", icon_type="info"):
        """
        Envia notificação local usando Windows nativo

        Args:
            title (str): Título da notificação
            message (str): Mensagem da notificação
            priority (str): Prioridade (low, normal, high, critical)
            icon_type (str): Tipo do ícone (info, warning, error, success)
        """
        if not self.notifications_enabled:
            logger.debug("Notificações desabilitadas")
            return False

        if platform.system() != 'Windows':
            logger.warning("Sistema não é Windows")
            return False

        try:
            # Mapear ícone para emoji/símbolo
            icon_map = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅',
                'alert': '🔔',
                'critical': '🚨'
            }
            icon = icon_map.get(icon_type, 'ℹ️')

            # Título com ícone
            full_title = f"{icon} {title}"

            # Criar notificação via PowerShell
            self._show_windows_toast(full_title, message)

            logger.info(f"Notificação enviada: {title}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            return False

    def _show_windows_toast(self, title, message):
        """
        Exibe notificação Toast nativa do Windows via PowerShell

        Args:
            title (str): Título da notificação
            message (str): Mensagem da notificação
        """
        # Escapar aspas no PowerShell
        title_escaped = title.replace('"', '`"').replace("'", "''")
        message_escaped = message.replace('"', '`"').replace("'", "''")

        # Script PowerShell para Toast Notification (Windows 10/11)
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$APP_ID = 'TI Manager'

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title_escaped}</text>
            <text>{message_escaped}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Default" />
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
"""

        try:
            # Executar PowerShell
            subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW  # Não mostrar janela do PowerShell
            )
            logger.debug("Toast notification exibida via PowerShell")

        except subprocess.TimeoutExpired:
            logger.warning("Timeout ao executar PowerShell")
            # Fallback para msg.exe (mais simples mas menos bonito)
            self._show_msg_fallback(title, message)

        except Exception as e:
            logger.error(f"Erro no PowerShell Toast: {e}")
            # Fallback para msg.exe
            self._show_msg_fallback(title, message)

    def _show_msg_fallback(self, title, message):
        """
        Fallback usando msg.exe (Windows XP+)

        Args:
            title (str): Título da notificação
            message (str): Mensagem da notificação
        """
        try:
            # msg.exe - comando nativo do Windows
            # msg * exibe para todos os usuários da sessão
            full_message = f"{title}\n\n{message}"

            subprocess.run(
                ['msg', '*', full_message],
                capture_output=True,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.debug("Notificação exibida via msg.exe (fallback)")

        except Exception as e:
            logger.error(f"Erro no fallback msg.exe: {e}")

    def fetch_pending_notifications(self):
        """
        Busca notificações pendentes do servidor via POST

        Returns:
            list: Lista de notificações ou lista vazia em caso de erro
        """
        if not self.notifications_enabled:
            return []

        try:
            session = RequestsSession.get_session()

            url = f"{self.server_url}{self.endpoint}?machine_name={self.machine_name}&status=pending&limit=20"

            # Enviar via POST com JSON payload (CORRIGIDO)
            payload = {
                'machine_name': self.machine_name,
                'status': 'pending',
                'limit': 20
            }

            logger.debug(f"Buscando notificações em: {url}")
            logger.debug(f"Payload: {payload}")

            response = session.post(url, json=payload, verify=False, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    notifications = data.get('notifications', [])
                    logger.info(f"Notificações encontradas: {len(notifications)}")
                    return notifications
                else:
                    logger.warning(f"API retornou erro: {data.get('error')}")
                    return []
            else:
                logger.warning(f"Erro HTTP {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
            return []

    def mark_as_read(self, notification_id):
        """
        Marca notificação como lida no servidor

        Args:
            notification_id (int): ID da notificação

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            session = RequestsSession.get_session()

            url = f"{self.server_url}/api/notifications/mark-read/"
            data = {'notification_id': notification_id}

            response = session.post(url, json=data, verify=False, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"Notificação {notification_id} marcada como lida")
                    return True

            logger.warning(f"Falha ao marcar notificação {notification_id} como lida")
            return False

        except Exception as e:
            logger.error(f"Erro ao marcar como lida: {e}")
            return False

    def process_pending_notifications(self):
        """
        Processa todas as notificações pendentes

        Busca notificações do servidor, exibe as não vistas e marca como lidas.
        """
        if not self.notifications_enabled:
            return

        logger.info("Verificando notificações do servidor...")

        # Buscar notificações
        notifications = self.fetch_pending_notifications()

        if not notifications:
            logger.debug("Nenhuma notificação pendente")
            return

        # Processar cada notificação
        for notif in notifications:
            notif_id = notif.get('id')

            # Verificar se já foi exibida
            if notif_id in self.shown_notifications:
                logger.debug(f"Notificação {notif_id} já foi exibida")
                continue

            # Exibir notificação
            title = notif.get('title', 'Notificação')
            message = notif.get('message', '')
            notif_type = notif.get('type', 'info')
            priority = notif.get('priority', 'normal')

            logger.info(f"Exibindo notificação: {title}")

            success = self.send_notification(
                title=title,
                message=message,
                priority=priority,
                icon_type=notif_type
            )

            if success:
                # Marcar como exibida localmente
                self.shown_notifications.add(notif_id)
                self._save_history()

                # Marcar como lida no servidor
                self.mark_as_read(notif_id)

                # Aguardar entre notificações
                time.sleep(self.NOTIFICATION_DISPLAY_DELAY)


class InventoryAgent:
    """Agente principal de inventário"""

    def __init__(self, token=None):
        self.config = AgentConfig()

        if token:
            token_hash = TokenValidator.hash_token(token)
            self.config.set('token_hash', token_hash)

            if not TokenValidator.validate_with_server(
                    self.config.get('server_url'),
                    token_hash,
                    self.config.get('machine_name')
            ):
                raise ValueError("Token inválido ou expirado")

        elif not self.config.get('token_hash'):
            raise ValueError("Token não configurado")

        self.network = NetworkMonitor(self.config)
        self.updater = AutoUpdater(self.config)
        self.notification_manager = NotificationManager(self.config)
        self.running = False
        self.last_status = None

        logger.info(f"Agente iniciado - Versão {VERSION}")
        logger.info(f"Máquina: {self.config.get('machine_name')}")
        logger.info(f"Servidor: {self.config.get('server_url')}")

    def start(self):
        """Inicia o agente"""
        self.running = True

        threading.Thread(target=self.network_monitor_loop, daemon=True).start()
        threading.Thread(target=self.data_sender_loop, daemon=True).start()
        threading.Thread(target=self.notification_checker_loop, daemon=True).start()

        if self.config.get('auto_update'):
            threading.Thread(target=self.update_checker_loop, daemon=True).start()

        logger.info("Threads iniciadas com sucesso")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Agente interrompido pelo usuário")
            self.running = False

    def network_monitor_loop(self):
        """Loop de monitoramento de rede"""
        while self.running:
            status = None

            if self.network.check_connectivity():
                if self.last_status == "offline":
                    status = "reconnected"
                    logger.info("Conexão restaurada")
            else:
                if self.last_status != "offline":
                    status = "offline"
                    logger.warning("Servidor offline")

            self.last_status = status

            time.sleep(OFFLINE_CHECK_INTERVAL)

    def data_sender_loop(self):
        """Loop de envio de dados usando PowerShell para coleta"""
        while self.running:
            is_online = self.network.check_connectivity()

            if is_online:
                try:
                    # USA POWERSHELL PARA COLETAR
                    data = PowerShellCollector.get_system_info()

                    # USA PYTHON PARA ENVIAR
                    PowerShellCollector.send_data(self.config, data)

                except Exception as e:
                    logger.error(f"Erro no ciclo de envio: {e}")
            else:
                logger.debug("Servidor offline, aguardando reconexão")

            time.sleep(HEARTBEAT_INTERVAL)

    def update_checker_loop(self):
        """Loop de verificação de atualizações"""
        while self.running:
            if self.network.is_online:
                try:
                    update_info = self.updater.check_for_updates()
                    if update_info:
                        self.updater.download_update(update_info)
                except Exception as e:
                    logger.error(f"Erro ao verificar atualizações: {e}")

            time.sleep(UPDATE_CHECK_INTERVAL)

    def notification_checker_loop(self):
        """Loop de verificação de notificações"""
        time.sleep(30)
        while self.running:
            if self.network.is_online:
                try:
                    self.notification_manager.process_pending_notifications()
                except Exception as e:
                    logger.error(f"Erro ao verificar notificações: {e}")
            time.sleep(NotificationManager.NOTIFICATION_CHECK_INTERVAL)


def main():
    """Função principal"""

    token = None
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--token='):
                token = arg.split('=', 1)[1]
                break

    try:
        agent = InventoryAgent(token=token)
        agent.start()

    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Agente interrompido")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()