from difflib import SequenceMatcher
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
from rapidfuzz import fuzz, process


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






def inserir(espera, action, id_campo, valor, campo_id, controle=False):
    try:
        print(f"➡️ Esperando o campo '{campo_id}' ser clicável")
        campo_id_element = espera.until(EC.element_to_be_clickable((By.ID, campo_id)))
        time.sleep(0.4)
        campo_id_element.clear()
        time.sleep(0.4)
        print(f"✅ Campo {campo_id} clicado")

        print(f"➡️ Esperando o campo '{id_campo}' ser clicável")
        campo = espera.until(EC.visibility_of_element_located((By.ID, id_campo)))
        action.move_to_element(campo).click().send_keys(valor).perform()
        time.sleep(0.4)

        try:
            no_results = espera.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "ul.select2-results li.select2-no-results"
                ))
            )

            print(f"❌ Nenhum resultado encontrado para '{valor}'. Pulando...")
            return False

        except TimeoutException:
            pass

        # -------------------------------------

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
                    return False

            except TimeoutException:
                texto_atual = campo.find_element(By.CSS_SELECTOR, ".select2-chosen").text.strip()
                if texto_atual == valor:
                    print("✅ O valor foi preenchido automaticamente (sem abrir o dropdown).")
                else:
                    print(f"⚠️ O dropdown não apareceu e o valor ainda não é '{valor}'.")
                    return False
        else:
            print(f"✅ '{valor}' já estava selecionado.")

        print("✅ Inserção concluída")
        time.sleep(1)
        return True 

    except Exception as e:
        print(f"Não foi impossível inserir o campo {id_campo} devido {e}")
        return False



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
            verificar_medico_deletando(driver=driver,espera=espera,action=action,dados=team["members"],temp_team=temp_team)
            # verificar_medico_adicionando(driver=driver,espera=espera,action=action,dados=team["members"])
  

    



def verificar_medico_deletando(driver, espera, action, dados,temp_team):
    valores = []

    time.sleep(1)

    medicos_na_tela = extrair_medicos_da_tabela(espera,driver)


    for pessoa in medicos_na_tela:
        encontrado = any(mesma_pessoa(pessoa, cnes["name"]) for cnes in dados)
        
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
            print("Ta em card")

            
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


def mesma_pessoa(a, b):
    a_norm = normalizar(a)
    b_norm = normalizar(b)

    pa = a_norm.split()
    pb = b_norm.split()

    menor, maior = (pa, pb) if len(pa) <= len(pb) else (pb, pa)

    if all(p in maior for p in menor):
        return True

    score = fuzz.ratio(a_norm, b_norm)
    return score >= 85

def nomes_sao_mesma_pessoa(n1, n2):
    n1 = normalizar(n1)
    n2 = normalizar(n2)

    # Se iguais
    if n1 == n2:
        return True

    p1 = n1.split()
    p2 = n2.split()

    if all(p in p1 for p in p2):
        return True
    if all(p in p2 for p in p1):
        return True

    if SequenceMatcher(None, n1, n2).ratio() >= 0.80:
        return True

    inter = set(p1) & set(p2)
    if len(inter) >= 3:  
        return True

    return False

def nomes_similares(n1, n2):
    # São exatamente iguais
    if n1 == n2:
        return True
    
    # Um é prefixo do outro
    if n1.startswith(n2) or n2.startswith(n1):
        return True
    
    # Quebrar em partes
    p1 = n1.split()
    p2 = n2.split()
    
    # Se só o último sobrenome é diferente → considerar igual
    if p1[:-1] == p2 or p2[:-1] == p1:
        return True
    
    # Comparar primeiro e penúltimo sobrenome
    if p1[0] == p2[0]:
        if len(p1) > 1 and len(p2) > 1:
            if p1[-2] == p2[-2]:
                return True
    
    return False


def verificar_medico_adicionando(driver, espera, action, dados):
    medicos_na_tela = extrair_medicos_da_tabela(driver,espera)
    nomes_cnes = {normalizar(item["name"]) for item in dados}

    faltando_nomes = []

    for nome in nomes_cnes:
        achou = any(nomes_similares(nome, m) for m in medicos_na_tela)
        if not achou:
            faltando_nomes.append(nome)

    faltando_no_pronto = []

    for item in dados:
        nome_original = item["name"]
        nome_normalizado = normalizar(nome_original)

        if nome_normalizado in faltando_nomes:
            faltando_no_pronto.append({
                "nome": nome_original,
                "role": item.get("role"),
            })

    if faltando_no_pronto:
        print("\n🔍 Médicos encontrados no CNES mas não no Pronto:")
        for nome in faltando_no_pronto:
            print(f" - {nome}")
    else:
        print("\n✅ Nenhum médico faltando.")

    cancelar_tabela(espera, action)
    if(len(faltando_no_pronto) != 0):
        adicionar_medico_equipe(
            driver=driver,
            espera=espera,
            action=action,
            lista_add=list(faltando_no_pronto)
        )
    else:
        print( " 🧑‍🤝‍🧑 SEM MEDICOS A SEREM ADICIONADOS")


def extrair_medicos_da_tabela(espera,driver):
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
        nome_card = espera.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#s2id_esf_area_profissional_id_profissional .select2-chosen"))
        ).text

        valores.add(normalizar(nome_card))

        print(f"✅ Apenas um registro encontrado: {nome_card}")

    return valores


def cancelar_tabela(espera, action):
    """Clica no botão cancelar da tabela."""
    print("➡️ Cancelando tabela...")
    try:
        btn_cancel = espera.until(
            EC.element_to_be_clickable((By.ID, "esf_area_profissional_cancel"))
        )
        action.move_to_element(btn_cancel).click().perform()
        print("✅ Cancelado com sucesso.\n")
    except Exception as e:
        print(f"❌ Erro ao clicar em cancelar: {e}")

def existe_erro_na_navbar(driver):
    try:
        return driver.find_element(By.XPATH, "//p[contains(text(), 'Por favor, corrija os erros')]")
    except:
        return None


def adicionar_medico_equipe(driver, espera, action, lista_add):

    time.sleep(1)
    print("➡️ Abrindo formulário de Inserção...")
    click_btn_inserir(espera, action)

    processados = []
    print(f"📌 Médicos a serem adicionados: {lista_add}")
    time.sleep(1)

    for medico in lista_add:
        print(f"\n➡️ Adicionando médico: {medico}")
        try:
            ok =  inserir(
                espera=espera,
                action=action,
                id_campo="s2id_esf_area_profissional_id_profissional",
                campo_id="lookup_key_esf_area_profissional_id_profissional",
                valor=medico["nome"]
            )

            if not ok:
                print(f"⚠️ Pulando médico '{medico["nome"]}' (não encontrado)")
                matrix_medico_erro.append(medico)
                continue

            else:
                print("✅ Médico inserido no input.")

                ok2 = inserir(
                    espera=espera,
                    action=action,
                    id_campo="s2id_esf_area_profissional_id_especialidade",
                    campo_id="loup_key_esf_area_profissional_id_especialidade",
                    valor=medico["role"]
                )

                if not ok2:
                    print(f"⚠️ Medico sem Este CBO '{medico["role"]}' (não encontrado)")
                    matrix_medico_erro.append(medico)
                    continue
                else:
                    time.sleep(0.4)  
                    erro = existe_erro_na_navbar(driver)

                    if erro:
                        print("❌ Erro detectado na navbar!")
                        print("➤ Adicionando médico na lista de erros...")
                        matrix_medico_erro.append(medico)

                        # fecha o alerta para não atrapalhar
                        try:
                            fechar = driver.find_element(By.CSS_SELECTOR, ".fwk-navbar-danger .close")
                            fechar.click()
                        except:
                            pass

                        continue 

                    time.sleep(0.4)
                    salvar_profissional(espera, action)
                    processados.append(medico)

        except Exception as e:
            print(f"❌ Erro ao processar {medico}: {e}")
            matrix_medico_erro.append(medico)
        finally:
            time.sleep(0.4)
            print(f"\n➡️ Procurando botão de copiar")
            btn_copy = espera.until(EC.visibility_of_element_located((By.ID,"esf_area_profissional_insert_copy")))
            action.move_to_element(btn_copy).click().perform()
            print("✅ Botão copiar clicado.")





    # Remove da lista os adicionados
    for nome in processados:
        if nome in lista_add:
            lista_add.remove(nome)
    
    cancelar_tabela(espera=espera,action=action)  
    # if aqui
    time.sleep(0.4)

     # 🔍 Tenta encontrar o modal "Atenção"
    try:
        modal = espera.until(
            EC.visibility_of_element_located((
                By.CSS_SELECTOR,
                "div.modal-dialog div.modal-content"
            ))
        )

        print("⚠️ Modal de confirmação encontrado — clicando em SIM...")

        botao_sim = modal.find_element(
            By.CSS_SELECTOR,
            "div.modal-footer button.btn-primary"
        )

        action.move_to_element(botao_sim).click().perform()
        print("✅ Clique em SIM realizado.")

    except TimeoutException:
        # Modal NÃO apareceu (fluxo normal)
        print("➡️ Nenhum modal de confirmação — seguindo fluxo normalmente.")

    



def click_btn_inserir(espera, action):
    """Clica no botão de inserir dentro da tela."""
    try:
        btn_inserir = espera.until(
            EC.element_to_be_clickable((By.ID, "esf_area_profissional_insert"))
        )
        action.move_to_element(btn_inserir).click().perform()
        print("✅ Botão inserir clicado.")
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
        print("✅ Profissional salvo.")
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
