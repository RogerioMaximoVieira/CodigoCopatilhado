from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("--headless")


# Inicializa o driver do Chrome
# Abre o NAVEGADOR
driver = webdriver.Chrome()
# Roda em Headless
# driver = webdriver.Chrome(options=options)

# Abre a página da Mega-Sena
driver.get("https://www.loteriasonline.caixa.gov.br/silce-web/#/mega-sena")
driver.maximize_window()
# Espera a página carregar
time.sleep(2)

def abrir_arquivo_jogos_gerar_lista(arquivo):
    import csv
    # Abre o arquivo csv
    with open(arquivo, 'r') as csv_file:
        # Lê o arquivo usando o delimitador tabulação
        csv_reader = csv.reader(csv_file, delimiter='\t')
        # Cria uma lista de listas para armazenar as linhas
        linhas = []
        # Itera sobre as linhas do arquivo
        for linha in csv_reader:
            # print(linha)
            # Remove o caractere de nova linha
            linha_limpa = [item.rstrip() for item in linha]
            linhas.append(linha_limpa)
        return linhas
    
# Clicar na opção SIM maior de Idade
termo_de_uso = driver.find_element(By.XPATH,"//a[@title='Sim'][contains(.,'Sim')]")
termo_de_uso.click()


# Clicar no Menu Mega-Sena
email_input = driver.find_element(By.XPATH, "//a[@ui-sref='mega-sena'][contains(.,'Mega-Sena')]")
email_input.click()

# Preenche os jogos de 6 dezenas cada
lista_jogos = abrir_arquivo_jogos_gerar_lista('jogosMegaSena.csv')

for jogo in lista_jogos:
    for dezena in jogo:
        dezena_input = driver.find_element(By.XPATH, f"//a[@id='n{dezena}']")
        dezena_input.click()                            

    # Clica no botão "Adicionar Jogo"
    add_jogo = driver.find_element(By.XPATH, "//button[@id='colocarnocarrinho']")
    add_jogo.click()
    # rola a página para cima em 500 pixels
    driver.execute_script("window.scrollBy(0,-500);")

    # Espera a página carregar
    time.sleep(3)
    
time.sleep(5)
# Clicar na opção de Acessar
acessar_input = driver.find_element(By.XPATH, "//span[normalize-space()='Acessar']")
acessar_input.click()

time.sleep(2)

# Adicionar o CPF
cpf_input = driver.find_element(By.XPATH, "//input[@id='username']")
cpf_input.send_keys("00000000000") # Seu CPF

# Clincar em Proximo

proximo_submit = driver.find_element(By.XPATH, "//button[@id='button-submit']")
proximo_submit.click()

# Receber código por E-mail
email_receber_codigo = driver.find_element(By.XPATH, "//button[normalize-space()='Receber código']")
email_receber_codigo.click()

# Receber código por E-mail
# codigo_email = input('Código de Ativação: ')
# input_codigo = driver.find_element(By.XPATH, "//input[@id='codigo']")
# input_codigo.send_keys(codigo_email)

# Tempo de espera para pegar o codigo manual
time.sleep(20)

# Clicar em enviar após inserir o código
enviar_clic = driver.find_element(By.XPATH, "//button[normalize-space()='Enviar']")
enviar_clic.click()

# inserir a senha
senha_input = driver.find_element(By.XPATH, "//input[@id='password']")
senha_input.send_keys("000000") # Sua Senha
senha_input.send_keys(Keys.RETURN)

time.sleep(20)

driver.quit()