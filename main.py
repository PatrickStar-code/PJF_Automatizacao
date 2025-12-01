from pathlib import Path
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
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

def normalizar(texto):
    texto = texto.upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto

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







def inserir( espera, action, id_campo, valor,campo_id,controle = False):
    try:
        print(f"➡️ Esperando o campo '{campo_id}' ser clicável")
        campo_id_element = espera.until(EC.element_to_be_clickable((By.ID,campo_id)))
        time.sleep(1)
        campo_id_element.clear()
        time.sleep(1)
        print(f"✅ Campo {campo_id} clicado")



        print(f"➡️ Esperando o campo '{id_campo}' ser clicável")
        campo = espera.until(EC.visibility_of_element_located((By.ID, id_campo)))
        action.move_to_element(campo).click().send_keys(valor).perform()
        time.sleep(1)
        
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
        time.sleep(1)
    except Exception as e:
        print(f"Não foi impossivel inserir o campo  {id_campo} devido {e}")



def login(driver, espera,action):
    driver.get(URL)

    campo_conta = espera.until(EC.presence_of_element_located((By.ID, "conta")))
    if(campo_conta.get_attribute("value") == "" or campo_conta is None):
        campo_conta.send_keys(USER)
    
    campo_senha = espera.until(EC.presence_of_element_located((By.NAME, "password")))
    campo_senha.send_keys(PASSWORD)
    
    btn_entrar =  espera.until(EC.visibility_of_element_located((By.CLASS_NAME, "btn_entrar")))
    action.move_to_element(btn_entrar).click().perform()

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
            print(f"Equipe - {team["area"]} , {i + 1}  de {len(times)}")
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
                valor=team["segmento"],
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

            time.sleep(1)
            print("➡️ Esperando botão pesquisar")
            btn_search = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_search")))
            action.move_to_element(btn_search).click().perform()
            print("✅ Botão pesquisar clicado")
            time.sleep(1)
            try:
                select_element = espera.until(
                    EC.visibility_of_element_located(
                        (By.NAME, "esf_area_profissional_datatable_length")
                    )
                )
                

                select = Select(select_element)
                select.select_by_value("100")

            except Exception as e:
                print("Select não Encontrado")
            verificar_medico_adicionando(driver=driver,espera=espera,action=action,dados=team["members"])
            # verificar_medico_deletando(espera=espera,action=action,dados=team["members"],temp_team=temp_team)
  

    



def verificar_medico_deletando( espera, action, dados,temp_team):
    valores = []

    time.sleep(1)

    medicos_na_tela = extrair_medicos_da_tabela(espera)


    for pessoa in medicos_na_tela:
        encontrado = any(fuzz.ratio( normalizar(pessoa), normalizar(cnes["name"])) > 85 for cnes in dados)
        
        if not encontrado:
            print(f"O médico {pessoa} não está mais no CNES — deletando...")
            deletar_medico_equipe(espera=espera,medico=pessoa,actions=action,temp_team=temp_team)
    
    print("Deletado menbros não cadastrado no CNES")
        
    time.sleep(1)
    cancel = espera.until(EC.presence_of_element_located((By.ID, "esf_area_profissional_cancel")))
    action.move_to_element(cancel).click().perform()
    time.sleep(1)
    print("Saindo da Tabela")




def deletar_medico_equipe(espera,medico,actions,temp_team):
    try:
        try:
            td = espera.until(EC.visibility_of_element_located((By.XPATH, f"//table[@id='esf_area_profissional_datatable']//td[normalize-space(text())='{medico}']")))        
            actions.double_click(td).perform()
        except:
            print("Entrei No except")

            
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
                valor=temp_team["segmento"],
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
            time.sleep(1)
        except Exception as e:
            print(e)

    
    except Exception as e:
        print(f"Falha ao deletar o medico {medico}")           
        


def verificar_medico_adicionando(driver, espera, action, dados):
    medicos_na_tela = extrair_medicos_da_tabela(espera)
    nomes_cnes = {normalizar(item["name"]) for item in dados}

    faltando_no_pronto = nomes_cnes - medicos_na_tela

    if faltando_no_pronto:
        print("\n🔍 Médicos encontrados no CNES mas não no Pronto:")
        for nome in faltando_no_pronto:
            print(f" - {nome}")
    else:
        print("\n✔ Nenhum médico faltando.")

    cancelar_tabela(espera, action)

    adicionar_medico_equipe(
        driver=driver,
        espera=espera,
        action=action,
        lista_add=list(faltando_no_pronto)
    )


def extrair_medicos_da_tabela(espera):
    """Tenta extrair os nomes dos médicos da tabela.
       Se não existir tabela, extrai do card select2."""
    
    time.sleep(1)
    valores = set()

    try:
        table = espera.until(
            EC.visibility_of_element_located((By.ID, "esf_area_profissional_datatable"))
        )
        print("📄 Tabela encontrada! Extraindo dados...")

        tbody = table.find_element(By.TAG_NAME, "tbody")
        linhas = tbody.find_elements(By.TAG_NAME, "tr")

        for linha in linhas:
            colunas = linha.find_elements(By.TAG_NAME, "td")

            # Linha vazia
            if len(colunas) == 1 and "Não foram encontrados resultados" in colunas[0].text:
                print("⚠ Equipe sem médicos cadastrados.")
                break

            # Linha invalida
            if len(colunas) <= 9:
                print("⚠ Linha ignorada (menos de 10 colunas)")
                continue

            valores.add(normalizar(colunas[9].text))

    except Exception:
        print("⚠ Nenhuma tabela encontrada. Extraindo do card...")
        select_valor = espera.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".select2-chosen"))
        ).text
        valores.add(normalizar(select_valor))
        print(f"✔ Apenas um registro encontrado: {select_valor}")

    return valores


def cancelar_tabela(espera, action):
    """Clica no botão cancelar da tabela."""
    print("➡️ Cancelando tabela...")
    try:
        btn_cancel = espera.until(
            EC.element_to_be_clickable((By.ID, "esf_area_profissional_cancel"))
        )
        action.move_to_element(btn_cancel).click().perform()
        print("✔ Cancelado com sucesso.\n")
    except Exception as e:
        print(f"❌ Erro ao clicar em cancelar: {e}")

def acessar_modal_profissional(driver, espera):
    # Volta ao HTML principal
    driver.switch_to.default_content()

    # Aguarda o iframe ser recriado
    iframe = espera.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='esf_area_profissional']"))
    )

    # Entra no iframe atualizado
    driver.switch_to.frame(iframe)


def adicionar_medico_equipe(driver, espera, action, lista_add):

    time.sleep(1)
    print("➡️ Abrindo formulário de Inserção...")
    click_btn_inserir(espera, action)

    processados = []
    print(f"📌 Médicos a serem adicionados: {lista_add}")
    time.sleep(1)
    # acessar_modal_profissional(driver=driver,espera=espera)

    for medico in lista_add:
        print(f"\n➡️ Adicionando médico: {medico}")
        try:
            inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_profissional",
                campo_id="lookup_key_esf_area_profissional_id_profissional",
                valor=medico
            )
            print("✔ Médico inserido no input.")
            

            salvar_profissional(espera, action)
            processados.append(medico)

        except Exception as e:
            print(f"❌ Erro ao processar {medico}: {e}")
            matrix_medico_erro.append(medico)

    # Remove da lista os adicionados
    for nome in processados:
        if nome in lista_add:
            lista_add.remove(nome)


def click_btn_inserir(espera, action):
    """Clica no botão de inserir dentro da tela."""
    try:
        btn_inserir = espera.until(
            EC.element_to_be_clickable((By.ID, "esf_area_profissional_insert"))
        )
        action.move_to_element(btn_inserir).click().perform()
        print("✔ Botão inserir clicado.")
    except Exception as e:
        print(f"❌ Erro ao clicar em inserir: {e}")
        raise



def salvar_profissional(espera, action):
    """Clica no botão inserir para salvar o profissional."""
    try:
        time.sleep(1)
        btn_salvar = espera.until(
            EC.element_to_be_clickable((By.ID, "esf_area_profissional_save"))
        )
        action.move_to_element(btn_salvar).click().perform()
        print("✔ Profissional salvo.")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

        raise



def main():
    dados = carregar_dados_times(JSON_PATH)
    if not dados:
        print("Nenhum dado carregado no JSON.")
        return


    driver = webdriver.Edge()
    espera = WebDriverWait(driver, WAIT_TIME)
    action = ActionChains(driver)

    try:
        login(driver, espera,action)
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
