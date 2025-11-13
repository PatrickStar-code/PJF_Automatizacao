from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys
import json
import time

import os
from fuzzywuzzy import fuzz


# ======== CONFIGURAÇÕES ========
load_dotenv()

USER = os.getenv("LOGIN", "")
PASSWORD = os.getenv("PASSWORD", "")



URL = "https://juizdefora-mg-tst.vivver.com/login"

JSON_PATH = "teams_output.json"
WAIT_TIME = 10

input_file = Path("teams_output.json")
markdown_text = input_file.read_text(encoding="utf-8")

matrix_medico_erro = []
area_atual = None
# ======== FUNÇÕES AUXILIARES ========

def carregar_dados_times(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as teamfile:
            leitor = json.load(teamfile)
            if "teams" in leitor:
                dados = leitor["teams"]
            else:
                dados = leitor  
    except FileNotFoundError:
        print(f"[ERRO] Arquivo JSON não encontrado: {caminho}")
        dados = []
    except json.JSONDecodeError as e:
        print(f"[ERRO] Erro ao ler o arquivo JSON: {e}")
        dados = []

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
    driver.get(URL)

    campo_conta = espera.until(EC.presence_of_element_located((By.ID, "conta")))
    if(campo_conta.get_attribute("value") == "" or campo_conta is None):
        campo_conta.send_keys(USER)
    
    campo_senha = espera.until(EC.presence_of_element_located((By.NAME, "password")))
    campo_senha.send_keys(PASSWORD)
    
    esperar_e_clicar(espera, By.CLASS_NAME, "btn_entrar")

    try:
        popup = espera.until(EC.visibility_of_element_located((By.CLASS_NAME, "window_close")))
        popup.click()
    except TimeoutException:
        print("[INFO] Nenhuma noticia de boas-vindas encontrado.")


def abrir_times(driver, espera, action):
    """Abre a área de times e clica no area Profissional"""
    abrir_formulario(driver=driver,espera=espera,action=action,shortcut_id="shortcut_esf_area_profissional")


def abrir_formulario(driver,espera,action,shortcut_id):
    """Abre a área de times"""
    print("➡️ Esperando o shortcut...")
    shortcut = espera.until(EC.element_to_be_clickable((By.ID, shortcut_id)))
    print("✅ Shortcut encontrado")

    action.double_click(shortcut).perform()
    print("✅ Duplo clique executado")




def pesquisar_unidade_por_area(driver, espera, action, dados,iframe):
    print("➡️ Trocando para o iFrame")
    iframe = espera.until(EC.visibility_of_element_located((By.ID, iframe)))
    driver.switch_to.frame(iframe)
    print("✅ Troca bem sucedida")


    if isinstance(dados, dict):
        times = dados["teams"]
    else:
        times = dados
        for i,team in enumerate(times):
            temp_team = team
            inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_municipio",
                campo_id="lookup_key_esf_area_profissional_id_municipio",
                valor="JUIZ DE FORA",
            )   
            inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_segmento",
                campo_id="lookup_key_esf_area_profissional_id_segmento",
                valor="URBANO",
            )   

            inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_unidade",
                campo_id="lookup_key_esf_area_profissional_id_unidade",
                valor=team["unid"],
            )

            inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_area",
                valor=team["area"],
                campo_id="lookup_key_esf_area_profissional_id_area",
                controle=True
            )

            time.sleep(0.5)
            print("-> Esperando botão pesquisar")
            btn_search = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_search")))
            btn_search.click()
            print("-> Botão pesquisar clicado")            
            verificar_medico(driver=driver,espera=espera,action=action,dados=team["members"],temp_team=temp_team)
  

    

def inserir( espera, action, id_campo, valor,campo_id,controle = False):
    try:
        print(f"➡️ Esperando o campo '{campo_id}' ser clicável")
        campo_id_element = espera.until(EC.element_to_be_clickable((By.ID,campo_id)))
        time.sleep(0.4)
        campo_id_element.clear()
        time.sleep(0.4)
        print(f"✅ Campo {campo_id} clicado")



        print(f"➡️ Esperando o campo '{id_campo}' ser clicável")
        campo = espera.until(EC.visibility_of_element_located((By.ID, id_campo)))
        action.move_to_element(campo).click().send_keys(valor).perform()
        time.sleep(0.5)
        print("Valor enviado")
        
        if controle:
            texto = campo.find_element(By.CSS_SELECTOR, ".select2-chosen").text.strip()

            if texto != valor:
                print("🔄 Valor diferente do atual — tentando selecionar nova opção...")

            try:
                espera.until(EC.visibility_of_element_located((By.ID, "select2-drop")))
                print("📋 Dropdown visível — buscando opções...")

                opcoes = espera.until(EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR,
                    "#select2-drop ul.select2-results li.select2-result-selectable"
                )))

                clicou = False
                for opcao in opcoes:
                    if valor.lower() in opcao.text.lower():
                        opcao.click()
                        clicou = True
                        print(f"✅ Clicado em: {opcao.text}")
                        break

                if not clicou:
                    print(f"❌ Opção '{valor}' não encontrada na lista.")

            except TimeoutException:
                # Se o dropdown não aparecer, pode ser que o campo tenha sido preenchido automaticamente
                texto_atual = campo.find_element(By.CSS_SELECTOR, ".select2-chosen").text.strip()
                if texto_atual == valor:
                    print("✅ O valor foi preenchido automaticamente (sem abrir o dropdown).")
                else:
                    print(f"⚠️ O dropdown não apareceu e o valor ainda não é '{valor}'.")
        else:
            print(f"✅ '{valor}' já estava selecionado.")
            
        print("✅ Inserção concluída")
        time.sleep(0.3)
    except Exception as e:
        print(f"Não foi impossivel inserir o campo  {id_campo} devido {e}")



def verificar_medico(driver, espera, action, dados,temp_team):
    table = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_datatable")))
    tbody = table.find_element(By.TAG_NAME,"tbody")
    linhas = tbody.find_elements(By.TAG_NAME, "tr")
    valores = list()

 

    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")
        if(colunas[0].text == "Não foram encontrados resultados"):
            print("Equipe sem medicos")
            break
        valores.append(colunas[9].text) 
    
   
    if len(valores) == 0:
        print("Fui para o if")
        for cnes in dados:
            adicionar_medico_equipe(driver=driver,espera=espera,action=action,pessoa=cnes["name"])

    else:
        for cnes in dados:
            nome = cnes["name"]
            encontrado = any(fuzz.ratio(nome, pessoa) > 80 for pessoa in valores)
            
            if encontrado:
                print(f"O médico {nome} está cadastrado corretamente")
            else:
                print(f"O médico {nome} não está na equipe — adicionando...")
                adicionar_medico_equipe(driver=driver,espera=espera,action=action,pessoa=nome)

        for pessoa in valores:
            encontrado = any(fuzz.ratio(pessoa, cnes["name"]) > 80 for cnes in dados)
        
            if not encontrado:
                print(f"O médico {pessoa} não está mais no CNES — deletando...")
                deletar_medico_equipe(espera=espera,medico=pessoa,actions=action,temp_team=temp_team)

        #Problema acontece aqui
        print("Saindo da tabela")
        cancel = espera.until(EC.presence_of_element_located((By.ID, "esf_area_profissional_cancel")))
        action.move_to_element(cancel).click().perform()




def adicionar_medico_equipe(driver,espera,action,pessoa):
    try:
        print("-> Cliquei no cancel")
        btn_cancel = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_cancel")))
        action.move_to_element(btn_cancel).click().perform()
        print("-> Cancel Bem Sucedido")


        time.sleep(1)

        print("-> Esperando o botão inserir")
        btn_inserir = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_insert")))
        action.move_to_element(btn_inserir).click().perform()
        print("-> Botão inserir clicado")

        time.sleep(1)
        
        print("-> Inserindo dados do medico")
        inserir(espera=espera,action=action,id_campo="s2id_esf_area_profissional_id_profissional",campo_id="lookup_key_esf_area_profissional_id_profissional",valor=pessoa)
        print("->Dado Inserido")

        time.sleep(1)
        espera.until(EC.invisibility_of_element_located((By.ID, "select2-drop-mask")))
        print("-> Esperando botão salvar")
        btn_salvar = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_save")))
        action.move_to_element(btn_salvar).click().perform()
        print("-> Botão salvar clicado")
        time.sleep(1)

        erro = driver.find_element(By.CSS_SELECTOR, "nav.fwk-navbar-danger")

        if erro.is_displayed():
            matrix_medico_erro.append()
            
        
 

    except Exception as e:
        print(f"Não foi possivel cadastrar o medico {pessoa}")
        matrix_medico_erro.append(pessoa)
        
        time.sleep(1)
        body = espera.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body.click()


        print("-> Cliquei no cancel")
        btn_cancel = espera.until(EC.presence_of_element_located((By.ID, "esf_area_profissional_cancel")))
        action.move_to_element(btn_cancel).click().perform()
        print("-> Cancel Bem Sucedido")

        time.sleep(2)
    
        print("-> Esperando botão pesquisar")
        btn_search = espera.until(EC.presence_of_element_located((By.ID, "esf_area_profissional_search")))
        action.move_to_element(btn_search).click().perform()
        print("-> Botão pesquisar clicado")

        time.sleep(1)

def deletar_medico_equipe(espera,medico,actions,temp_team):
    try:
        td = espera.until(EC.visibility_of_element_located((By.XPATH, f"//table[@id='esf_area_profissional_datatable']//td[normalize-space(text())='{medico}']")))        
        actions.double_click(td).perform()
        time.sleep(1)
        btn_excluir = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_delete")))
        actions.move_to_element(btn_excluir).click().perform()
        time.sleep(1)
        btn_confirmar_exclusao = espera.until(EC.visibility_of_element_located((By.CSS_SELECTOR,".modal-footer .btn.btn-primary.btn-lg")))
        actions.move_to_element(btn_confirmar_exclusao).click().perform()
        time.sleep(1)

        try:
            inserir(
                espera=espera,
                action=actions,
                id_campo="s2id_esf_area_profissional_id_municipio",
                campo_id="lookup_key_esf_area_profissional_id_municipio",
                valor="JUIZ DE FORA",
            )   
            inserir(
                espera=espera,
                action=actions,
                id_campo="s2id_esf_area_profissional_id_segmento",
                campo_id="lookup_key_esf_area_profissional_id_segmento",
                valor="URBANO",
            )   

            inserir(
                espera=espera,
                action=actions,
                id_campo="s2id_esf_area_profissional_id_unidade",
                campo_id="lookup_key_esf_area_profissional_id_unidade",
                valor=temp_team["unid"],
            )

            inserir(
                espera=espera,
                action=actions,
                id_campo="s2id_esf_area_profissional_id_area",
                valor=temp_team["area"],
                campo_id="lookup_key_esf_area_profissional_id_area",
                controle=True
            )

            btn_search = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_search")))
            actions.move_to_element(btn_search).click().perform()
        except Exception as e:
            print(e)

    
    except Exception as e:
        print(f"Falha ao deletar o medico {medico}")           
        



def main():
    dados = carregar_dados_times(JSON_PATH)
    if not dados:
        print("Nenhum dado carregado no JSON.")
        return


    driver = webdriver.Edge()
    espera = WebDriverWait(driver, WAIT_TIME)
    action = ActionChains(driver)

    try:
        login(driver, espera)
        abrir_times(driver, espera, action)
        pesquisar_unidade_por_area(driver,espera,action,dados,"iframe_esf_area_profissional")

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro: {e}")
    
    finally:
        print(matrix_medico_erro)
        print("Fechando navegador...")
        driver.quit()



if __name__ == "__main__":
    main()
