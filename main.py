from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import time
import csv
import os

# ======== CONFIGURAÇÕES ========
load_dotenv()

USER = os.getenv("LOGIN", "")
PASSWORD = os.getenv("PASSWORD", "")

print(f"Login: {USER}", flush=True)
print(f"Senha: {PASSWORD}", flush=True)

URL = "https://juizdefora-mg-tst.vivver.com/login?page=%2Fdesktop&conta=SMS"

CSV_PATH = "Book(Planilha1).csv"
WAIT_TIME = 10

# ======== FUNÇÕES AUXILIARES ========

def carregar_dados_csv(caminho):
    dados = []
    try:
        with open(caminho, newline='', encoding='utf-8') as csvfile:
            leitor = csv.DictReader(csvfile)
            for linha in leitor:
                dados.append(linha)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo CSV não encontrado: {caminho}")
    return dados


def esperar_e_clicar(espera, by, seletor):
    """Espera o elemento aparecer e clica"""
    try:
        elemento = espera.until(EC.element_to_be_clickable((by, seletor)))
        elemento.click()
        return elemento
    except TimeoutException:
        print(f"[ERRO] Tempo excedido ao procurar {seletor}")
        return None


def login(driver, espera):
    """Realiza login no sistema"""
    driver.get(URL)

    # Espera campo de login
    campo_conta = espera.until(EC.presence_of_element_located((By.ID, "conta")))
    if(campo_conta.get_attribute("value") != "" and campo_conta is None):
        campo_conta.send_keys(USER)
    
    campo_senha = espera.until(EC.presence_of_element_located((By.NAME, "password")))
    campo_senha.send_keys(PASSWORD)
    
    esperar_e_clicar(espera, By.CLASS_NAME, "btn_entrar")

    try:
        popup = espera.until(EC.element_to_be_clickable((By.CLASS_NAME, "window_close")))
        popup.click()
    except TimeoutException:
        print("[INFO] Nenhuma noticia de boas-vindas encontrado.")


def abrir_abrangencia(driver, espera, action):
    """Abre a área de abrangência com duplo clique"""
    abrangencia = espera.until(EC.element_to_be_clickable((By.ID, "shortcut_esf_abrangencia_area")))
    action.double_click(abrangencia).perform()


def preencher_formulario(driver, espera, dados):
    """Preenche o formulário usando os dados do CSV"""
    for i, dado in enumerate(dados, start=1):
        print(f"Processando linha {i}...")
        try:
            municipio = esperar_e_clicar(espera, By.ID, "s2id_esf_abrangencia_area_codmunicipio")
            if municipio:
                # Exemplo de preenchimento de campo
                # driver.find_element(By.ID, "campo_exemplo").send_keys(dado["coluna"])
                pass
        except NoSuchElementException as e:
            print(f"[ERRO] Campo não encontrado na linha {i}: {e}")


# ======== EXECUÇÃO PRINCIPAL ========

def main():
    dados = carregar_dados_csv(CSV_PATH)
    if not dados:
        print("Nenhum dado carregado do CSV.")
        return

    driver = webdriver.Edge()
    espera = WebDriverWait(driver, WAIT_TIME)
    action = ActionChains(driver)

    try:
        login(driver, espera)
        abrir_abrangencia(driver, espera, action)
        preencher_formulario(driver, espera, dados)

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro: {e}")
    
    finally:
        print("Fechando navegador...")
        driver.quit()


if __name__ == "__main__":
    main()
