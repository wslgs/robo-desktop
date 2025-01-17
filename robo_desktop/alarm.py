import subprocess
import time
import logging
import os
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from datetime import datetime, timedelta

# Configurar diretórios de logs e reports
log_directory = 'logs'
reports_directory = 'reports'

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

if not os.path.exists(reports_directory):
    os.makedirs(reports_directory)

# Configurar logging
log_file_path = os.path.join(log_directory, 'alarms_log.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Variável global para armazenar erros
error_reports = []

def save_error_report():
    """
    Salva as mensagens de erro acumuladas em um arquivo de relatório na pasta reports.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_filename = os.path.join(reports_directory, f'report_{timestamp}.report')
    
    with open(report_filename, 'w') as file:
        if error_reports:
            for error in error_reports:
                file.write(error + '\n')
        else:
            file.write("Nenhum erro encontrado durante a execução.\n")

def add_error_report(error_message):
    """
    Adiciona uma mensagem de erro à lista de erros.

    Args:
        error_message (str): Mensagem de erro a ser adicionada.
    """
    error_reports.append(error_message)

# Arrays para as opções de alarme e soneca
alarm_sounds = ["Alarms", "Xilofone", "Acordes", "Toque", "Jingle", "Transição", "Decrescente", "Quique", "Eco"]
snooze_times = ["Desativado", "5 minutos", "10 minutos", "20 minutos", "30 minutos", "1 hora"]

# Função para abrir o relógio do Windows
def open_clock():
    try:
        logger.info("Abrindo o aplicativo de Relógio do Windows...")
        subprocess.Popen(['start', 'ms-clock:'], shell=True)
        time.sleep(5)  # Esperar alguns segundos para garantir que o aplicativo abriu
    except Exception as e:
        error_message = f"Erro ao abrir o aplicativo de Relógio do Windows: {e}"
        logger.error(error_message)
        add_error_report(error_message)

# Função para fechar o relógio do Windows
def close_clock():
    try:
        logger.info("Fechando o aplicativo de Relógio do Windows...")
        app.kill()
        logger.info("Aplicativo de Relógio do Windows fechado com sucesso.")
    except Exception as e:
        error_message = f"Erro ao fechar o aplicativo de Relógio do Windows: {e}"
        logger.error(error_message)
        add_error_report(error_message)

# Função para criar tarefas agendadas
def criar_tarefa_agendada(nome_tarefa, script_path, hora, minuto, dias, repetir=True):
    try:
        # Excluir tarefa existente
        comando_excluir = f'schtasks /delete /tn "{nome_tarefa}" /f'
        logger.info(f"Excluindo tarefa agendada existente: {comando_excluir}")
        subprocess.run(comando_excluir, shell=True)
        
        if repetir:
            comando_base = f'schtasks /create /tn "{nome_tarefa}" /tr "python \\"{script_path}\\"" /sc weekly /st {hora:02d}:{minuto:02d} /f'
            for dia in dias:
                comando = f'{comando_base} /d {dia}'
                logger.info(f"Criando tarefa agendada: {comando}")
                result = subprocess.run(comando, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Erro ao criar tarefa agendada: {result.stderr}")
                    add_error_report(f"Erro ao criar tarefa agendada: {result.stderr}")
                else:
                    logger.info(f"Tarefa agendada criada com sucesso: {comando}")
        else:
            data_alarme = datetime.now().replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if data_alarme < datetime.now():
                data_alarme += timedelta(days=1)
            comando = f'schtasks /create /tn "{nome_tarefa}" /tr "python \\"{script_path}\\"" /sc once /st {data_alarme.strftime("%H:%M")} /sd {data_alarme.strftime("%d/%m/%Y")} /f'
            logger.info(f"Criando tarefa agendada: {comando}")
            result = subprocess.run(comando, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Erro ao criar tarefa agendada: {result.stderr}")
                add_error_report(f"Erro ao criar tarefa agendada: {result.stderr}")
            else:
                logger.info(f"Tarefa agendada criada com sucesso: {comando}")
    except Exception as e:
        error_message = f"Erro ao criar tarefa agendada: {e}"
        logger.error(error_message)
        add_error_report(error_message)

# Função para criar diretório e arquivo histórico, se não existirem
def criar_diretorio_historico():
    usuario = os.getlogin()
    diretorio_historico = f"C:\\Users\\{usuario}\\Documents\\histórico_robô"
    arquivo_historico = os.path.join(diretorio_historico, "historico.txt")

    if not os.path.exists(diretorio_historico):
        os.makedirs(diretorio_historico)
        logger.info(f"Criado diretório: {diretorio_historico}")

    if not os.path.exists(arquivo_historico):
        with open(arquivo_historico, 'w') as f:
            f.write("Histórico de Execução dos Alarmes\n")
        logger.info(f"Criado arquivo: {arquivo_historico}")

# Criar diretório e arquivo histórico antes de criar alarmes
criar_diretorio_historico()

# Abrir o aplicativo de Relógio do Windows
open_clock()

# Listar todas as janelas para verificar o título correto
try:
    logger.info("Listando janelas abertas para verificar o título correto...")
    windows = Desktop(backend="uia").windows()
    for win in windows:
        logger.info(f"Janela encontrada: {win.window_text()}")
except Exception as e:
    error_message = f"Erro ao listar janelas abertas: {e}"
    logger.error(error_message)
    add_error_report(error_message)

# Tente conectar ao aplicativo de Relógio do Windows
try:
    logger.info("Conectando ao aplicativo de Relógio do Windows...")
    app = Application(backend="uia").connect(title_re="Relógio")
    clock = app.window(title_re="Relógio")
    logger.info("Conexão estabelecida com sucesso.")
except Exception as e:
    error_message = f"Erro ao conectar ao aplicativo de Relógio do Windows: {e}"
    logger.error(error_message)
    add_error_report(error_message)
    save_error_report()
    exit()

# Acessar a aba "Alarme" na esquerda
try:
    logger.info("Acessando a aba Alarme...")
    alarm_tab = clock.child_window(title="Alarme", control_type="ListItem")
    alarm_tab.wait('visible', timeout=10).select()
    logger.info("Aba Alarme acessada com sucesso.")
except Exception as e:
    error_message = f"Erro ao acessar a aba Alarme: {e}"
    logger.error(error_message)
    add_error_report(error_message)
    save_error_report()
    exit()

def criar_alarme(hora, minuto, nome, dias, soneca, repetir=True, campainha=None):
    try:
        logger.info("Clicando no botão + para adicionar um novo alarme...")
        add_alarm_button = clock.child_window(title="Adicionar um alarme", control_type="Button")
        add_alarm_button.wait('visible', timeout=10).click()
        time.sleep(2)  # Adicionar um delay para garantir que a janela está pronta
        
        logger.info("Configurando o novo alarme...")
        
        # Configurar a hora e minutos do alarme usando teclado
        logger.info("Inserindo hora e minutos...")
        for digit in f"{hora:02d}":
            send_keys(f"{{VK_NUMPAD{digit}}}")
        send_keys("{TAB}")
        for digit in f"{minuto:02d}":
            send_keys(f"{{VK_NUMPAD{digit}}}")
        send_keys("{TAB}")
        time.sleep(1)
        
        # Configurar o nome do alarme
        logger.info("Configurando o nome do alarme...")
        send_keys(f"{nome.replace(' ', '{SPACE}')}")
        time.sleep(1)
        
        # Verificar se a próxima seção é "Repetir alarme"
        logger.info("Verificando a próxima seção...")
        send_keys("{TAB}")
        if repetir:
            send_keys("{SPACE}")
        send_keys("{TAB}")
        
        # Configurar os dias da semana
        logger.info("Configurando os dias da semana...")
        for dia in range(1, 8):  # Navegar pelos dias de Domingo a Sábado
            if dia in dias:
                send_keys("{SPACE}")
            send_keys("{RIGHT}")
            time.sleep(0.5)
        
        # Configurar o som do alarme
        if campainha:
            logger.info("Configurando o som do alarme...")
            send_keys("{TAB}")
            index = alarm_sounds.index(campainha)
            for _ in range(index):
                send_keys("{DOWN}")
            send_keys("{TAB}")
        else:
            send_keys("{TAB}")
            send_keys("{TAB}")

        # Configurar soneca
        logger.info("Configurando a soneca...")
        current_index = snooze_times.index("10 minutos")
        desired_index = snooze_times.index(soneca)
        steps = desired_index - current_index
        if steps > 0:
            for _ in range(steps):
                send_keys("{DOWN}")
        elif steps < 0:
            for _ in range(-steps):
                send_keys("{UP}")
        send_keys("{TAB}")
        
        # Salvar o alarme
        logger.info("Salvando o alarme...")
        send_keys("{SPACE}")
        time.sleep(2)
        
        logger.info("Alarme criado com sucesso.")
        
        # Criar tarefa agendada no Windows
        script_path = os.path.abspath('register_alarm.py')
        dias_semana = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        dias_agendados = [dias_semana[dia - 1] for dia in dias]
        criar_tarefa_agendada(nome, script_path, hora, minuto, dias_agendados, repetir)
        
    except Exception as e:
        error_message = f"Erro ao criar o alarme: {e}"
        logger.error(error_message)
        add_error_report(error_message)

# Criar o primeiro alarme
criar_alarme(hora=8, minuto=0, nome="Tenha um excelente dia de trabalho!", dias=[2, 3, 4, 5, 6], soneca="5 minutos")

# Criar o segundo alarme
criar_alarme(hora=7, minuto=45, nome="Curtir o final de semana", dias=[1, 7], soneca="30 minutos", repetir=True, campainha="Jingle")

# Fecha o relógio
close_clock()

# Salvar relatório de erros, se houver
save_error_report()
