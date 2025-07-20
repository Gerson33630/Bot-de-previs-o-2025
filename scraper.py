from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
from fake_useragent import UserAgent
import logging
import json
from datetime import datetime
import os

# Configuração avançada de logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configurações globais
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
DELAY_RANGE = (1.0, 2.5)
HISTORY_LENGTH = 15
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"

# URLs dos jogos
URLS = {
    "aviator": "https://www.elephant.bet/pt/games/aviator",
    "jetx": "https://www.elephant.bet/pt/games/jetx",
    "rocketman": "https://www.elephant.bet/pt/games/rocketman",
    "spaceman": "https://www.elephant.bet/pt/games/spaceman",
    "navigator": "https://www.elephant.bet/pt/games/navigator",
    "fashnator": "https://www.elephant.bet/pt/games/fashnator",
    "swimminator": "https://www.elephant.bet/pt/games/swimminator"
}

def configurar_driver():
    """Configura e retorna uma instância do WebDriver com opções otimizadas"""
    options = Options()
    
    # Configurações para melhorar o stealth e desempenho
    options.add_argument(f"user-agent={UserAgent().random}")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Desativa logs desnecessários do Chrome
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    # Configuração do serviço
    service = Service(executable_path=CHROME_DRIVER_PATH)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        
        # Configurações adicionais para evitar detecção
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except WebDriverException as e:
        logger.error(f"Erro ao iniciar o WebDriver: {e}")
        raise

def coletar_dados_do_jogo(jogo, retry_count=0):
    """
    Coleta dados históricos de um jogo específico no ElephantBet
    
    Args:
        jogo (str): Nome do jogo (deve estar nas chaves de URLS)
        retry_count (int): Contador de tentativas (uso interno)
    
    Returns:
        list: Lista de valores históricos ou None em caso de falha
    """
    if jogo not in URLS:
        logger.error(f"Jogo '{jogo}' não suportado. Opções válidas: {list(URLS.keys())}")
        return None

    logger.info(f"Iniciando coleta para {jogo} (tentativa {retry_count + 1})")
    
    driver = None
    try:
        driver = configurar_driver()
        driver.get(URLS[jogo])
        
        # Espera até que os elementos estejam presentes
        WebDriverWait(driver, REQUEST_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "crash-point"))
        )
        
        # Delay aleatório para parecer humano
        time.sleep(random.uniform(*DELAY_RANGE))
        
        # Coleta os elementos de crash-point
        pontos = driver.find_elements(By.CLASS_NAME, "crash-point")
        valores = []
        
        for el in pontos[:HISTORY_LENGTH]:
            texto = el.text.strip().replace("x", "").replace(",", ".")
            try:
                valor = float(texto)
                valores.append(valor)
            except ValueError as e:
                logger.warning(f"Valor inválido encontrado: '{el.text}' - {e}")
                continue
        
        if not valores:
            logger.warning(f"Nenhum valor válido encontrado para {jogo}")
            if retry_count < MAX_RETRIES - 1:
                return coletar_dados_do_jogo(jogo, retry_count + 1)
            return None
        
        logger.info(f"Coleta bem-sucedida para {jogo}. Valores: {valores}")
        return valores

    except TimeoutException:
        logger.error(f"Timeout ao acessar {jogo}")
        if retry_count < MAX_RETRIES - 1:
            return coletar_dados_do_jogo(jogo, retry_count + 1)
        return None
        
    except Exception as e:
        logger.error(f"Erro inesperado ao coletar {jogo}: {e}", exc_info=True)
        if retry_count < MAX_RETRIES - 1:
            return coletar_dados_do_jogo(jogo, retry_count + 1)
        return None

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Erro ao fechar driver: {e}")

def salvar_dados_em_json(jogo, dados):
    """Salva os dados coletados em um arquivo JSON com timestamp"""
    if not dados:
        return False
    
    try:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{jogo}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "jogo": jogo,
                "timestamp": datetime.now().isoformat(),
                "valores": dados
            }, f, indent=2)
        
        logger.info(f"Dados salvos em {filename}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar dados: {e}")
        return False

# Exemplo de uso
if __name__ == "__main__":
    try:
        jogo = "aviator"  # Pode ser alterado para qualquer jogo na lista URLS
        dados = coletar_dados_do_jogo(jogo)
        
        if dados:
            salvar_dados_em_json(jogo, dados)
            logger.info(f"Resultado da coleta: {dados}")
        else:
            logger.error("Falha ao coletar dados")
    except KeyboardInterrupt:
        logger.info("Script interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
