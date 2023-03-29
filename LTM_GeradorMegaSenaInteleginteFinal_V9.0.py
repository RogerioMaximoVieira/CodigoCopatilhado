# Importação das Bibliotecas Python para uso no Projeto
from time import sleep
from random import sample
import numpy as np
from datetime import datetime
import json
import requests
import pyfiglet
import os
import re
from prettytable import PrettyTable
from bs4 import BeautifulSoup
import csv
import sqlite3
from tqdm import tqdm
import logging
import urllib3
import math
from termcolor import colored

# Isso desativará as mensagens de aviso para todas as solicitações HTTP feitas com urllib3 em seu script
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class BancoDeDados:
    def __init__(self):
        self.nome_banco = 'historico_mega.db'
        self.pasta_bd = 'BD_HISTORICO_MEGA'
        self.caminho_bd = os.path.join(self.pasta_bd, self.nome_banco)

        # verifica se a pasta existe e a cria, caso contrário
        if not os.path.exists(self.pasta_bd):
            os.makedirs(self.pasta_bd)

        # conecta ao banco de dados ou cria o banco se ele não existir
        self.conexao = sqlite3.connect(self.caminho_bd)
        self.cursor = self.conexao.cursor()
        self.criar_tabela()

    def selecionar_dezenas_mais_sorteadas(self, quantidade):
        self.cursor.execute(f'''SELECT dezena, count(dezena) as frequencia FROM (
            SELECT dezena1 as dezena FROM resultado_mega UNION ALL
            SELECT dezena2 as dezena FROM resultado_mega UNION ALL
            SELECT dezena3 as dezena FROM resultado_mega UNION ALL
            SELECT dezena4 as dezena FROM resultado_mega UNION ALL
            SELECT dezena5 as dezena FROM resultado_mega UNION ALL
            SELECT dezena6 as dezena FROM resultado_mega
        ) GROUP BY dezena ORDER BY frequencia DESC LIMIT {quantidade}''')

        dezenas = self.cursor.fetchall()
        lista_dezenas = []
        for dez in dezenas:
            lista_dezenas.append(dez[0])
        return [f" Dezena {dezena[0]:>2}: {dezena[1]:>3} vezes" for i, dezena in enumerate(dezenas)], lista_dezenas

    def selecionar_dezenas_menos_sorteadas(self, quantidade):
        self.cursor.execute(f'''SELECT dezena, count(dezena) as frequencia FROM (
            SELECT dezena1 as dezena FROM resultado_mega UNION ALL
            SELECT dezena2 as dezena FROM resultado_mega UNION ALL
            SELECT dezena3 as dezena FROM resultado_mega UNION ALL
            SELECT dezena4 as dezena FROM resultado_mega UNION ALL
            SELECT dezena5 as dezena FROM resultado_mega UNION ALL
            SELECT dezena6 as dezena FROM resultado_mega
        ) GROUP BY dezena ORDER BY frequencia LIMIT {quantidade}''')

        dezenas = self.cursor.fetchall()
        lista_dezenas = []
        for dez in dezenas:
            lista_dezenas.append(dez[0])
        return [f" Dezena {dezena[0]:>2}: {dezena[1]:>3} vezes" for i, dezena in enumerate(dezenas, 1)], lista_dezenas

    def criar_tabela(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS resultado_mega (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            concurso INTEGER NOT NULL,
            dezena1 INTEGER NOT NULL,
            dezena2 INTEGER NOT NULL,
            dezena3 INTEGER NOT NULL,
            dezena4 INTEGER NOT NULL,
            dezena5 INTEGER NOT NULL,
            dezena6 INTEGER NOT NULL
        )''')
        self.conexao.commit()

    def inserir_resultados(self, resultados):
        # Consulta o último concurso registrado no banco de dados
        self.cursor.execute('SELECT MAX(concurso) FROM resultado_mega')
        ultimo_concurso_bd = self.cursor.fetchone()[0]
        # Verifica se é a primeira vez que está sendo inserido um resultado no banco de dados
        if ultimo_concurso_bd is None:
            ultimo_concurso_bd = 0
        # Cria uma lista para armazenar os resultados que serão inseridos no banco de dados
        resultados_para_inserir = []
        # Filtra os resultados para pegar somente os que ainda não foram registrados no banco de dados
        for resultado in resultados:
            concurso = resultado['concurso']
            if concurso > ultimo_concurso_bd:
                dezenas = resultado['dezenas']
                data = resultado['data']
                resultados_para_inserir.append((data, concurso, *dezenas))
        # Insere os resultados no banco de dados
        if len(resultados_para_inserir) > 0:
            self.cursor.executemany('''INSERT INTO resultado_mega (data, concurso, dezena1, dezena2, dezena3, dezena4, dezena5, dezena6)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', resultados_para_inserir)
            self.conexao.commit()
            # print(f'{len(resultados_para_inserir)} resultados inseridos com sucesso.')
        # else:
        #     print('Não há novos resultados para inserir no banco de dados.')

    def obter_ultimo_id_concurso(self):
        self.cursor.execute('SELECT MAX(id) FROM resultado_mega')
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado[0] is not None else 0

    def deletar_resultado_por_concurso(self, concurso):
        self.cursor.execute('DELETE FROM resultado_mega WHERE concurso = ?', (concurso,))
        print(f'{Cores.fg.yellow} Concurso {concurso} apagado com sucesso do BD{Cores.fim}')
        self.conexao.commit()

    def verifica_jogo_bd(self, jogo):

        self.cursor.execute('SELECT * FROM resultado_mega')
        lista_acertos = []
        for row in self.cursor.fetchall():
            numeros_sorteio = [str(num).zfill(2) for num in row[3:]]
            numeros_jogo = [str(num).zfill(2) for num in jogo]
            acertos = len(set(numeros_sorteio).intersection(set(numeros_jogo)))
            lista_acertos.append(acertos)
        return lista_acertos

    def fechar_conexao(self):
        self.conexao.close()


class Cores:
    fim = '\33[m'

    class fg:  # Cores de Letras
        black = '\033[1;30m'
        red = '\033[1;31m'
        green = '\033[1;32m'
        yellow = '\033[1;33m'
        blue = '\033[1;34m'
        pink = '\033[1;35m'
        cyan = '\033[1;36m'
        lightgrey = '\033[1;37m'
        branco = '\33[1;40m'

    class bg:  # Cores de Fundo
        red = '\033[1;41m'
        green = '\033[1;42m'
        orange = '\033[1;43m'
        blue = '\033[1;44m'
        purple = '\033[1;45m'
        cyan = '\033[1;46m'
        lightgrey = '\033[1;47m'


class GeradorNumerosCartelaMega:

    @staticmethod
    def gerar_numeros_linha1():
        linha1 = list()
        for i in range(1, 11):
            linha1.append(i)
        return linha1

    @staticmethod
    def gerar_numeros_linha2():
        linha2 = list()
        for i in range(11, 21):
            linha2.append(i)
        return linha2

    @staticmethod
    def gerar_numeros_linha3():
        linha3 = list()
        for i in range(21, 31):
            linha3.append(i)
        return linha3

    @staticmethod
    def gerar_numeros_linha4():
        linha4 = list()
        for i in range(31, 41):
            linha4.append(i)
        return linha4

    @staticmethod
    def gerar_numeros_linha5():
        linha5 = list()
        for i in range(41, 51):
            linha5.append(i)
        return linha5

    @staticmethod
    def gerar_numeros_linha6():
        linha6 = list()
        for i in range(51, 61):
            linha6.append(i)
        return linha6

    @staticmethod
    def gerar_numeros_coluna1():
        coluna1 = list()
        for i in range(1, 61, 10):
            coluna1.append(i)
        return coluna1

    @staticmethod
    def gerar_numeros_coluna2():
        coluna2 = list()
        for i in range(2, 62, 10):
            coluna2.append(i)
        return coluna2

    @staticmethod
    def gerar_numeros_coluna3():
        coluna3 = list()
        for i in range(3, 63, 10):
            coluna3.append(i)
        return coluna3

    @staticmethod
    def gerar_numeros_coluna4():
        coluna4 = list()
        for i in range(4, 64, 10):
            coluna4.append(i)
        return coluna4

    @staticmethod
    def gerar_numeros_coluna5():
        coluna5 = list()
        for i in range(5, 65, 10):
            coluna5.append(i)
        return coluna5

    @staticmethod
    def gerar_numeros_coluna6():
        coluna6 = list()
        for i in range(6, 66, 10):
            coluna6.append(i)
        return coluna6

    @staticmethod
    def gerar_numeros_coluna7():
        coluna7 = list()
        for i in range(7, 67, 10):
            coluna7.append(i)
        return coluna7

    @staticmethod
    def gerar_numeros_coluna8():
        coluna8 = list()
        for i in range(8, 68, 10):
            coluna8.append(i)
        return coluna8

    @staticmethod
    def gerar_numeros_coluna9():
        coluna9 = list()
        for i in range(9, 69, 10):
            coluna9.append(i)
        return coluna9

    @staticmethod
    def gerar_numeros_coluna10():
        coluna10 = list()
        for i in range(10, 70, 10):
            coluna10.append(i)
        return coluna10


class GeradorDeNumeros:

    @staticmethod
    def gerar_pares():
        lista_pares = []
        for i in range(2, 61, 2):
            lista_pares.append(i)
        return lista_pares

    @staticmethod
    def gerar_impares():
        lista_impares = []
        for i in range(1, 61, 2):
            lista_impares.append(i)
        return lista_impares

    @staticmethod
    def gerar_primos():
        lista_primos = []
        for num in range(2, 61):
            for i in range(2, num):
                if (num % i) == 0:
                    break
            else:
                lista_primos.append(num)
        return lista_primos

    @staticmethod
    def gerar_fibonacci():
        lista_fibonacci = [1, 1]
        while lista_fibonacci[-1] < 60:
            lista_fibonacci.append(lista_fibonacci[-1] + lista_fibonacci[-2])
        return lista_fibonacci

    @staticmethod
    def gerar_multiplos_de_3():
        lista_multiplos_de_3 = []
        for i in range(3, 61, 3):
            lista_multiplos_de_3.append(i)
        return lista_multiplos_de_3


class GeradorNumerosEstrategiaVizinhos:
    def __init__(self):
        self.numeros_selecionados_para_sorteio = []

    def obter_ultimo_jogo_mega_sena(self):
        todos_jogos = self.todos_jogos_mega_sena()
        concurso = todos_jogos[0]["concurso"]
        data = todos_jogos[0]['data']
        dezenas = todos_jogos[0]['dezenas']
        ultimo_resultado = f"{data} - {concurso} - {dezenas}"
        return ultimo_resultado, data, concurso, dezenas

    def obter_jogo_mega_sena(self, concurso):
        todos_jogos = self.todos_jogos_mega_sena()
        for jogo in todos_jogos:
            if jogo['concurso'] == concurso:
                data = jogo['data']
                dezenas = jogo['dezenas']
                jogo_mega = f"{data} - {concurso} - {dezenas}"
                return jogo_mega
        # Se chegou aqui, o concurso não foi encontrado
        return f"O concurso {concurso} não foi encontrado na base de dados."

    def todos_jogos_mega_sena(self):
        url = 'http://loteriascaixa-api.herokuapp.com/api/mega-sena/'
        resposta = requests.get(url=url)
        ultimo_jogo_mega_sena = json.loads(resposta.content)
        return ultimo_jogo_mega_sena

    def gerar_numeros_vizinhos(self):
        ultimo_jogo_mega_sena = self.todos_jogos_mega_sena()

        dez1 = list()
        dez2 = list()
        dez3 = list()
        dez4 = list()
        dez5 = list()
        dez6 = list()
        # -----------------------------------------ESTRATEGIA-LTM-VIZINHOS----------------------------------------#
        for ind, dez in enumerate(ultimo_jogo_mega_sena[0]['dezenas']):
            num = int(dez)
            if ind == 0:
                dez1 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            elif ind == 1:
                dez2 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            elif ind == 2:
                dez3 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            elif ind == 3:
                dez4 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            elif ind == 4:
                dez5 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            elif ind == 5:
                dez6 = [num, num + 1, num + 2, num - 1, num - 2, num + 10, num + 20, num - 10, num - 20, num + 9,
                        num + 18, num - 9, num - 18, num + 11, num + 22, num - 11, num - 22]
            else:
                continue

        unificacao_das_listas = dez1 + dez2 + dez3 + dez4 + dez5 + dez6
        numeros_selecionads_para_sorteio = list()

        for numero in unificacao_das_listas:
            if numero > 0 and numero <= 60:
                if numero not in numeros_selecionads_para_sorteio:
                    numeros_selecionads_para_sorteio.append(numero)
                else:
                    continue
            else:
                continue
        return numeros_selecionads_para_sorteio

    @staticmethod
    def gerador_de_1_a_60():
        numeros_para_sorteio = list()
        for dezena in range(1, 61):
            numeros_para_sorteio.append(dezena)
        return numeros_para_sorteio

    @staticmethod
    def data_hora():
        atual = datetime.now()
        data_hora = atual.strftime("%Y%m%d%H%M%S")
        return data_hora


def print_bonito():
    print(f'{Cores.fg.cyan}#' + '=' * 90 + f'#{Cores.fim}')


# Configurar a primeira execução do Windows para mostrar as cores do programa Python
print_bonito()
os.system('reg add HKEY_CURRENT_USER\Console /v VirtualTerminalLevel /t REG_DWORD /d 0x00000001 /f')
dezenas_moldura = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 20, 21, 30, 31, 40, 41, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
                   60]
dezenas_centro = [12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 28, 29, 32, 33, 34, 35, 36, 37, 38, 39, 42,
                  43, 44, 45, 46, 47, 48, 49]
dezenas_menor_30 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                    28, 29, 30]
dezenas_maior_30 = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                    56, 57, 58, 59, 60]
quadrante1 = [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25]  # 2 ou 1
quadrante2 = [6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 26, 27, 28, 29, 30]  # 2 ou 1
quadrante3 = [31, 32, 33, 34, 35, 41, 42, 43, 44, 45, 51, 52, 53, 54, 55]  # 1
quadrante4 = [36, 37, 38, 39, 40, 46, 47, 48, 49, 50, 56, 57, 58, 59, 60]  # 2 ou 1

# Lista final com todos os jogos gerados com base nas regras de necio
lista_de_jogos_filtrados = list()


def menu(lista_menu):
    print_bonito()
    print('SISTEMA GERADOR INTELIGENTE DE JOGOS DA MEGA-SENA v6.0'.center(90))
    print_bonito()
    contador = 0
    for item in lista_menu:
        print(f'    {Cores.fg.yellow}[{contador}] - {Cores.fg.blue}{item}{Cores.fim}')
        contador += 1
    while True:
        try:
            print_bonito()
            opc = int(re.sub(r'[^0-9]', '', input(f'{Cores.fg.green} Digite a opção desejada: {Cores.fim} ')))
            print_bonito()
        except (ValueError, TypeError):
            print_bonito()
            print(f'{Cores.fg.red} Opção invalida, digite novamente!{Cores.fim}')
            continue
        except (KeyboardInterrupt):
            print(f'{Cores.fg.red} O usuário preferiu interromper!{Cores.fim}')
            print_bonito()
            return 0
        else:
            return opc


def validar_jogo_se_tem_sequencia(jogo, lista_tomada_decisao):
    for i in range(len(jogo) - 2):
        if jogo[i] == jogo[i + 1] - 1 and jogo[i] == jogo[i + 2] - 2:
            # Se existe uma sequência de três ou mais números consecutivos, não faz nada
            return
    # Se não existe uma sequência de três ou mais números consecutivos, adiciona o jogo na lista
    lista_tomada_decisao.append(30)


# Segue abaixo uma função que recebe dois jogos (o atual e o anterior) e verifica se há 0 ou 1 número em comum entre eles:
def verifica_jogos_anteriores(jogo_atual, jogo_anterior):
    '''Verifica se o jogo atual tem 0 ou 1 número em comum com o jogo anterior.'''
    jogo_anterior = list(map(int, jogo_anterior))
    num_comuns = len(set(jogo_atual).intersection(set(jogo_anterior)))
    return num_comuns


def validador_inteligente_jogos(jogo, jogo_anterior=None, lista_negra=None):
    dezenas_menor_30 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                        27, 28, 29, 30]
    dezenas_maior_30 = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
                        55, 56, 57, 58, 59, 60]

    # Lista final com todos os jogos gerados com base nas regras de necio
    lista_de_jogos_filtrados = []
    lista_de_jogos_filtrados.clear()

    chamar_funcoes_num = GeradorDeNumeros()
    numeros_sorteados = sorted(jogo)
    # print(numeros_sorteados)
    # FUNCAO PARES
    lista_pares = chamar_funcoes_num.gerar_pares()
    # FUNCAO IMPARES
    lista_impares = chamar_funcoes_num.gerar_impares()
    # FUNCAO PRIMOS
    lista_primos = chamar_funcoes_num.gerar_primos()
    # FUNCAO FIBONACCI
    lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
    # FUNCAO MULTIPLOS DE 3
    lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

    # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
    total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
    total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
    total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
    total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
    total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
    total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
    total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

    # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
    total_impares = 14 - total_pares
    valores_validos_par_impar = f'{total_pares}-{total_impares}'
    # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
    lista_tomada_decisao = []
    # REQUISITO-01 Pares e Impares
    msg = f'{Cores.fg.yellow} Aguarde estamos selcionando os jogos... total de jogos descartados >>> {Cores.fg.red}{{}}{Cores.fim}'
    cont = 1
    print('AQUII')
    while True:
        if valores_validos_par_impar == '7-7' or valores_validos_par_impar == '6-8' or valores_validos_par_impar == '8-6':
            lista_tomada_decisao.append(1)
        else:
            cont += 1
            break

        # REQUISITO-02 Primos
        if total_primos >= 1 and total_primos <= 5:
            lista_tomada_decisao.append(2)
        else:
            break

            # REQUISITO-03 Fibonacci
        if total_fibonacci <= 5:
            lista_tomada_decisao.append(3)
        else:
            cont += 1
            break

        # REQUISITO-04 Multiplos de 3
        if total_multiplos3 >= 1 and total_multiplos3 <= 7:
            lista_tomada_decisao.append(4)
        else:
            cont += 1
            break

            # REQUISITO-05 Dezenas Menores igual a 30
        if total_dezenas_menor_30 == 7:
            lista_tomada_decisao.append(5)
        else:
            cont += 1
            break

            # REQUISITO-06 Dezenas maiores que 30
        if total_dezenas_maior_30 == 7:
            lista_tomada_decisao.append(6)
        else:
            cont += 1
            break

            # REQUISITO-07 validano se tem dezenas etre as 25 mais ou 15 menos sorteadas
        banco = BancoDeDados()
        _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(45)
        _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
        num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
        num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
        if num_mais == 10 and num_menos == 4:
            lista_tomada_decisao.append(7)
        else:
            cont += 1
            break

            # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
        if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(41, 61):
            lista_tomada_decisao.append(8)
        else:
            cont += 1
            break

        # REQUISITO-09 verifica se o jogo tem de 0 a 1 numero do ultimo jogo
        nums_anterior = verifica_jogos_anteriores(numeros_sorteados, jogo_anterior)
        if nums_anterior <= 1:
            lista_tomada_decisao.append(9)
        else:
            cont += 1
            break

        # Verifica se algum número está na lista negra
        for num in numeros_sorteados:
            if num in lista_negra:
                lista_tomada_decisao.append(10)
                cont += 1
                break
            else:
                cont += 1
                break

        print(msg.format(cont), end='\r', flush=True)

        # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
        # caso atendam, será incluso na lista final
        if len(lista_tomada_decisao) == 10:
            if numeros_sorteados not in lista_de_jogos_filtrados:
                lista_de_jogos_filtrados.append(numeros_sorteados)
                return lista_de_jogos_filtrados


def gerador_inteligente_jogos(cenário, quantidade_jogos, lista_numeros_para_jogos=None, jogo_anterior=None,
                              lista_negra=None):
    """
    Gerador de jogos inteligentes da Mega-Sena.
    :param quantidade_jogos: Quantidade de jogos a serem gerados.
    :param jogo_anterior: MOstra o jogo anterior.
    :param lista_numeros_para_jogos: Lista com os numeros a ser usada para gerar numeros.
    :param numeros_adicionais: Números adicionais que devem estar presentes em cada jogo gerado.
    :return: Lista com os jogos gerados.
    """
    chamar_funcoes_num = GeradorDeNumeros()
    lista_de_jogos_filtrados.clear()
    if quantidade_jogos > 0:
        msg = f'{Cores.fg.yellow} Aguarde estamos selcionando os jogos... total de jogos descartados >>> {Cores.fg.red}{{}}{Cores.fim}'
        cont = 0
        while len(lista_de_jogos_filtrados) < quantidade_jogos:
            # Gerando os numeros aleatórios com base na lista numeros_selecionads_para_sorteio
            numeros_sorteados = sample(lista_numeros_para_jogos, 6)
            # Ordenando a lista do menor para o maior
            numeros_sorteados = sorted(set(numeros_sorteados))

            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            gerardor_num_cartela = GeradorNumerosCartelaMega()
            gerar_numeros_linha1 = gerardor_num_cartela.gerar_numeros_linha1()
            gerar_numeros_linha2 = gerardor_num_cartela.gerar_numeros_linha2()
            gerar_numeros_linha3 = gerardor_num_cartela.gerar_numeros_linha3()
            gerar_numeros_linha4 = gerardor_num_cartela.gerar_numeros_linha4()
            gerar_numeros_linha5 = gerardor_num_cartela.gerar_numeros_linha5()
            gerar_numeros_linha6 = gerardor_num_cartela.gerar_numeros_linha6()
            gerar_numeros_coluna1 = gerardor_num_cartela.gerar_numeros_coluna1()
            gerar_numeros_coluna2 = gerardor_num_cartela.gerar_numeros_coluna2()
            gerar_numeros_coluna3 = gerardor_num_cartela.gerar_numeros_coluna3()
            gerar_numeros_coluna4 = gerardor_num_cartela.gerar_numeros_coluna4()
            gerar_numeros_coluna5 = gerardor_num_cartela.gerar_numeros_coluna5()
            gerar_numeros_coluna6 = gerardor_num_cartela.gerar_numeros_coluna6()
            gerar_numeros_coluna7 = gerardor_num_cartela.gerar_numeros_coluna7()
            gerar_numeros_coluna8 = gerardor_num_cartela.gerar_numeros_coluna8()
            gerar_numeros_coluna9 = gerardor_num_cartela.gerar_numeros_coluna9()
            gerar_numeros_coluna10 = gerardor_num_cartela.gerar_numeros_coluna10()
            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_moldura = len(np.intersect1d(numeros_sorteados, dezenas_moldura))
            total_dezenas_centro = len(np.intersect1d(numeros_sorteados, dezenas_centro))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))
            total_quadrante1 = len(np.intersect1d(numeros_sorteados, quadrante1))
            total_quadrante2 = len(np.intersect1d(numeros_sorteados, quadrante2))
            total_quadrante3 = len(np.intersect1d(numeros_sorteados, quadrante3))
            total_quadrante4 = len(np.intersect1d(numeros_sorteados, quadrante4))
            total_soma_dezenas = sum(numeros_sorteados)  # SOMA DAS DEZENAS
            total_linha1 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha1))
            total_linha2 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha2))
            total_linha3 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha3))
            total_linha4 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha4))
            total_linha5 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha5))
            total_linha6 = len(np.intersect1d(numeros_sorteados, gerar_numeros_linha6))
            total_coluna1 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna1))
            total_coluna2 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna2))
            total_coluna3 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna3))
            total_coluna4 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna4))
            total_coluna5 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna5))
            total_coluna6 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna6))
            total_coluna7 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna7))
            total_coluna8 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna8))
            total_coluna9 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna9))
            total_coluna10 = len(np.intersect1d(numeros_sorteados, gerar_numeros_coluna10))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 6 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares
            if valores_validos_par_impar == '2-4' or valores_validos_par_impar == '3-3' or valores_validos_par_impar == '4-2':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos == 1 or total_primos == 2 or total_primos == 3:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

            # REQUISITO-03 Fibonacci
            if total_fibonacci == 0 or total_fibonacci == 1 or total_fibonacci == 2:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 == 1 or total_multiplos3 == 2 or total_multiplos3 == 3:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

            # REQUISITO-05 Dezenas na Moldura da Cartela
            if total_dezenas_moldura == 2 or total_dezenas_moldura == 3 or total_dezenas_moldura == 4:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

            # REQUISITO-06 Dezenas no Centro da Cartela
            if total_dezenas_centro == 2 or total_dezenas_centro == 3 or total_dezenas_centro == 4:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

            # REQUISITO-07 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 2 or total_dezenas_menor_30 == 3 or total_dezenas_menor_30 == 4:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

            # REQUISITO-08 Dezenas maiores que 30
            if total_dezenas_maior_30 == 2 or total_dezenas_maior_30 == 3 or total_dezenas_maior_30 == 4:
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue

            # REQUISITO-09 Dezenas do Quadrante 01 (Cartela dividida ao meio na horizontal e vertical)
            if total_quadrante1 == 1 or total_quadrante1 == 2:
                lista_tomada_decisao.append(9)
            else:
                cont += 1
                continue

            # REQUISITO-10 Dezenas do Quadrante 02 (Cartela dividida ao meio na horizontal e vertical)
            if total_quadrante2 == 1 or total_quadrante2 == 2:
                lista_tomada_decisao.append(10)
            else:
                cont += 1
                continue

            # REQUISITO-11 Dezenas do Quadrante 03 (Cartela dividida ao meio na horizontal e vertical)
            if total_quadrante3 == 1 or total_quadrante3 == 2:
                lista_tomada_decisao.append(11)
            else:
                cont += 1
                continue

            # REQUISITO-12 Dezenas do Quadrante 04 (Cartela dividida ao meio na horizontal e vertical)
            if total_quadrante4 == 1 or total_quadrante4 == 2:
                lista_tomada_decisao.append(12)
            else:
                cont += 1
                continue

            # REQUISITO-13 Soma das 6 dezenas
            if total_soma_dezenas >= 150 and total_soma_dezenas <= 230:
                lista_tomada_decisao.append(13)
            else:
                cont += 1
                continue

            # REQUISITO-14 Linha 01
            if total_linha1 == 0 or total_linha1 == 1 or total_linha1 == 2:
                lista_tomada_decisao.append(14)
            else:
                cont += 1
                continue

            # REQUISITO-15 Linha 02
            if total_linha2 == 0 or total_linha2 == 1 or total_linha2 == 2:
                lista_tomada_decisao.append(15)
            else:
                cont += 1
                continue

            # REQUISITO-16 Linha 03
            if total_linha3 == 0 or total_linha3 == 1 or total_linha3 == 2:
                lista_tomada_decisao.append(16)
            else:
                cont += 1
                continue

            # REQUISITO-17 Linha 04
            if total_linha4 == 0 or total_linha4 == 1 or total_linha4 == 2:
                lista_tomada_decisao.append(17)
            else:
                cont += 1
                continue

            # REQUISITO-18 Linha 05
            if total_linha5 == 0 or total_linha5 == 1 or total_linha5 == 2:
                lista_tomada_decisao.append(18)
            else:
                cont += 1
                continue

            # REQUISITO-19 Linha 06
            if total_linha6 == 0 or total_linha6 == 1 or total_linha6 == 2:
                lista_tomada_decisao.append(19)
            else:
                cont += 1
                continue

            # REQUISITO-20 Coluna 01
            if total_coluna1 == 0 or total_coluna1 == 1:
                lista_tomada_decisao.append(20)
            else:
                cont += 1
                continue

                # REQUISITO-21 Coluna 02
            if total_coluna2 == 0 or total_coluna2 == 1:
                lista_tomada_decisao.append(21)
            else:
                cont += 1
                continue

            # REQUISITO-22 Coluna 03
            if total_coluna3 == 0 or total_coluna3 == 1:
                lista_tomada_decisao.append(22)
            else:
                cont += 1
                continue

            # REQUISITO-23 Coluna 04
            if total_coluna4 == 0 or total_coluna4 == 1:
                lista_tomada_decisao.append(23)
            else:
                cont += 1
                continue

            # REQUISITO-24 Coluna 05
            if total_coluna5 == 0 or total_coluna5 == 1:
                lista_tomada_decisao.append(24)
            else:
                cont += 1
                continue

            # REQUISITO-25 Coluna 06
            if total_coluna6 == 0 or total_coluna6 == 1:
                lista_tomada_decisao.append(25)
            else:
                cont += 1
                continue

            # REQUISITO-26 Coluna 07
            if total_coluna7 == 0 or total_coluna7 == 1:
                lista_tomada_decisao.append(26)
            else:
                cont += 1
                continue

            # REQUISITO-27 Coluna 08
            if total_coluna8 == 0 or total_coluna8 == 1:
                lista_tomada_decisao.append(27)
            else:
                cont += 1
                continue

            # REQUISITO-28 Coluna 09
            if total_coluna9 == 0 or total_coluna9 == 1:
                lista_tomada_decisao.append(28)
            else:
                cont += 1
                continue

            # REQUISITO-29 Coluna 10
            if total_coluna10 == 0 or total_coluna10 == 1:
                lista_tomada_decisao.append(29)
            else:
                cont += 1
                continue

            # REQUISITO-30 validano jogos com sequência maior que 2
            if numeros_sorteados:
                validar_jogo_se_tem_sequencia(numeros_sorteados, lista_tomada_decisao)
            else:
                cont += 1
                continue

            # REQUISITO-31 validano se tem dezenas etre as 25 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(35)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if (num_mais > 0 and num_mais <= 4) and num_menos <= 2:
                lista_tomada_decisao.append(31)
            else:
                cont += 1
                continue

            # REQUISITO-32 validano se o jogo já teve acerto de 4 numeros em jogos passados
            banco = BancoDeDados()
            resultado = banco.verifica_jogo_bd(numeros_sorteados)
            if 3 in resultado or 4 in resultado:
                lista_tomada_decisao.append(32)
            else:
                cont += 1
                continue

            # REQUISITO-33 verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(41, 61):
                lista_tomada_decisao.append(33)
            else:
                cont += 1
                continue

            # 1 Bug, como a lista estava sendo passada como string ele sempre repondia 0
            # REQUISITO-34 verifica se o jogo tem de 0 a 1 numero do ultimo jogo

            nums_anterior = verifica_jogos_anteriores(numeros_sorteados, jogo_anterior)
            if nums_anterior <= 1:
                lista_tomada_decisao.append(34)
            else:
                cont += 1
                continue

            # Verifica se algum número está na lista negra
            if len(lista_negra) > 0:
                for num in numeros_sorteados:
                    if num in lista_negra:
                        cont += 1
                        break
                else:
                    cont += 1
                    lista_tomada_decisao.append(35)
            else:
                cont += 1
                continue

            print(msg.format(cont), end='\r', flush=True)

            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos, caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 35:
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
            else:
                cont += 1
                continue

        # Aqui será apresentado os jogos escolhidos conforme a quantidade desejada
        print_bonito()
        print(
            f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> SORTEANDO {quantidade_jogos} JOGOS <<<<<<<<<<<<<<<<<<<<<<<<<<<     {Cores.fim}')
        print_bonito()
        print(
            f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
        print_bonito()

        if cenário == 'NORMAL':
            max_length = max(len(str(num)) for lista_jogos in lista_de_jogos_filtrados for num in lista_jogos)
            for indice, lista_jogos in enumerate(lista_de_jogos_filtrados):
                print(
                    f'{Cores.fg.cyan} Jogo-Normal-{indice + 1:02d}: [{", ".join(str(num).rjust(max_length) for num in lista_jogos)}]{Cores.fim}')

        if cenário == 'EXTRA':
            max_length = max(len(str(num)) for lista_jogos in lista_de_jogos_filtrados for num in lista_jogos)
            for indice, lista_jogos in enumerate(lista_de_jogos_filtrados):
                print(
                    f'{Cores.fg.cyan} Jogo-Extra-{indice + 1:02d}: [{", ".join(str(num).rjust(max_length) for num in lista_jogos)}]{Cores.fim}')

        return lista_de_jogos_filtrados

    else:
        print_bonito()
        print(f'{Cores.fg.yellow} OK, saindo sem gerar jogos{Cores.fim}')
        # break


def gravar_jogos_filtrados(lista_de_jogos):
    gerador = GeradorNumerosEstrategiaVizinhos()
    data_hora = gerador.data_hora()
    # Define o nome e caminho do arquivo
    nome_arquivo = f"LTM_jogos_com_34_filtros_{data_hora}.csv"
    caminho_arquivo = os.path.join(os.getcwd(), "ARQUIVO_JOGOS", nome_arquivo)

    # Verifica se a pasta ARQUIVO_JOGOS existe, caso não exista, cria a pasta
    if not os.path.exists(os.path.join(os.getcwd(), "ARQUIVO_JOGOS")):
        os.makedirs(os.path.join(os.getcwd(), "ARQUIVO_JOGOS"))

    # Grava o arquivo na pasta ARQUIVO_JOGOS
    with open(caminho_arquivo, 'w') as arquivo:
        for indice, lista_jogos in enumerate(lista_de_jogos):
            saida_arquivo = f'Jogo {indice + 1}: {lista_jogos}\n'
            arquivo.write(saida_arquivo)
    print_bonito()
    print(f'{Cores.fg.yellow} Jogos salvo no arquivo = {Cores.fg.red}{nome_arquivo}{Cores.fim}')


def imprimir_jogos(lista_jogos):
    lista = lista_jogos

    jogos = [
        [lista[0], lista[1], lista[3], lista[9], lista[12], lista[13]],
        [lista[0], lista[1], lista[4], lista[5], lista[7], lista[11]],
        [lista[0], lista[2], lista[3], lista[5], lista[6], lista[10]],
        [lista[0], lista[2], lista[10], lista[11], lista[12], lista[13]],
        [lista[0], lista[5], lista[7], lista[8], lista[11], lista[13]],
        [lista[1], lista[2], lista[3], lista[7], lista[8], lista[9]],
        [lista[1], lista[2], lista[4], lista[6], lista[8], lista[12]],
        [lista[1], lista[3], lista[5], lista[6], lista[9], lista[11]],
        [lista[2], lista[4], lista[6], lista[7], lista[9], lista[12]],
        [lista[3], lista[7], lista[8], lista[10], lista[11], lista[12]],
        [lista[4], lista[5], lista[8], lista[9], lista[10], lista[13]]
    ]
    # Ordena cada jogo em ordem crescente
    jogos_ordenados = [sorted(jogo) for jogo in jogos]
    print(f'{Cores.fg.cyan} ----------------------------{Cores.fim}')
    print(f'{Cores.fg.cyan} # DESDOBRAMENTO 14 DEZENAS #{Cores.fim}')
    print(f'{Cores.fg.cyan} ----------------------------{Cores.fim}')
    # Imprime cada jogo com o prefixo "Jogo-" e o número do jogo
    for i, jogo in enumerate(jogos_ordenados, 1):
        print(f"{Cores.fg.cyan} Jogo-{i:02} = {'-'.join(str(x).zfill(2) for x in jogo)}{Cores.fim}")


def listar_desdobramento_jogos(lista_jogos):
    lista = lista_jogos

    jogos = [
        [lista[0], lista[1], lista[3], lista[9], lista[12], lista[13]],
        [lista[0], lista[1], lista[4], lista[5], lista[7], lista[11]],
        [lista[0], lista[2], lista[3], lista[5], lista[6], lista[10]],
        [lista[0], lista[2], lista[10], lista[11], lista[12], lista[13]],
        [lista[0], lista[5], lista[7], lista[8], lista[11], lista[13]],
        [lista[1], lista[2], lista[3], lista[7], lista[8], lista[9]],
        [lista[1], lista[2], lista[4], lista[6], lista[8], lista[12]],
        [lista[1], lista[3], lista[5], lista[6], lista[9], lista[11]],
        [lista[2], lista[4], lista[6], lista[7], lista[9], lista[12]],
        [lista[3], lista[7], lista[8], lista[10], lista[11], lista[12]],
        [lista[4], lista[5], lista[8], lista[9], lista[10], lista[13]]
    ]
    return jogos


def solicitar_dezenas():
    numeros_selecionados = []
    while True:
        # Solicita ao usuário a quantidade de dezenas
        qtd_dezenas = int(
            input(f"{Cores.fg.green} Quantas dezenas deseja informar para gerar jogos inteligentes? {Cores.fim}"))
        print_bonito()
        # Verifica se a quantidade de dezenas é válida
        if qtd_dezenas < 1 or qtd_dezenas > 60:
            print(f"{Cores.fg.red} Quantidade de dezenas inválida! Informe um valor entre 1 e 60.{Cores.fim}")
            print_bonito()
            continue
        # Solicita ao usuário as dezenas
        while len(numeros_selecionados) < qtd_dezenas:
            dezena = int(input(f"{Cores.fg.green} Informe a {len(numeros_selecionados) + 1}ª dezena: {Cores.fim}"))
            print_bonito()
            if dezena < 1 or dezena > 60:
                print(f"{Cores.fg.red} Dezena inválida! Informe um valor entre 1 e 60.{Cores.fim}")
                print_bonito()
            elif dezena in numeros_selecionados:
                print(f"{Cores.fg.yellow} Dezena já selecionada! Informe outra.{Cores.fim}")
                print_bonito()
            else:
                numeros_selecionados.append(dezena)
                print(f"{Cores.fg.yellow} Dezena adicionada com sucesso!{Cores.fim}")
                print_bonito()

        # Exibe as dezenas selecionadas
        print(f"{Cores.fg.blue} Dezenas selecionadas: {Cores.fg.pink}{sorted(numeros_selecionados)}{Cores.fim}")
        print_bonito()
        return numeros_selecionados


def obter_e_salvar_resultado_mega_sena():
    url = 'http://loteriascaixa-api.herokuapp.com/api/mega-sena/'
    nome_arquivo = 'resultado_mega.csv'
    resposta = requests.get(url)
    ultimo_jogo_mega_sena = json.loads(resposta.content)
    resultados_csv = []
    try:
        for resultado in ultimo_jogo_mega_sena:
            data = resultado['data']
            concurso = resultado['concurso']
            dezenas = [str(dezena) for dezena in resultado['dezenas']]
            resultados_csv.append([data, concurso] + dezenas)
        with open(nome_arquivo, 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerows(resultados_csv)
        print(
            f'{Cores.fg.yellow} Histórico de jogos da Mega-Sena baixado com sucesso! {Cores.fg.red}>> resultado_mega.csv{Cores.fim}')
    except:
        print(f'{Cores.fg.yellow} Erro ao baixar o Histórico de jogos da Mega-Sena, contate o ADM!{Cores.fim}')


def baixar_tabela_atraso():
    url = "https://www.mazusoft.com.br/mega/tabela-sequencia-atraso.php"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        tabela = soup.find(id='tb2')
        dezenas = []
        dezenas_15_atraso = []
        dezenas_15_ultimos = []
        cont = 0
        for tr in tabela.find_all('tr')[1:]:  # ignora o cabeçalho da tabela
            tds = tr.find_all('td')
            dezena = tds[0].find('b').text
            atraso = tds[1].find('b').text[:-1]  # remove o "x" do final
            perc_atraso = tds[2].text.strip().split('\n')[-1]
            if cont < 15:
                dezenas_15_atraso.append(dezena)
                cont += 1
            else:
                cont += 1
                if cont > 45:
                    dezenas_15_ultimos.append(dezena)
            dezenas.append((dezena, atraso, perc_atraso))

        return dezenas, dezenas_15_atraso, dezenas_15_ultimos
    else:
        print(f"{Cores.fg.red} Erro ao baixar a tabela{Cores.fim}")


def split_table(table1, table2, table3):
    """Divide as tabelas em 3 partes e as exibe lado a lado"""
    # Calcula a largura de cada tabela
    width1 = len(str(table1).split('\n')[0])
    width2 = len(str(table2).split('\n')[0])
    width3 = len(str(table3).split('\n')[0])
    max_width = max(width1, width2, width3)

    # Adiciona espaços para preencher as tabelas até a largura máxima
    table1_str = str(table1).ljust(max_width)
    table2_str = str(table2).ljust(max_width)
    table3_str = str(table3).ljust(max_width)

    # Dividir as tabelas em linhas
    table1_lines = table1_str.split('\n')
    table2_lines = table2_str.split('\n')
    table3_lines = table3_str.split('\n')

    # Calcula o número de linhas de cada tabela
    num_lines1 = len(table1_lines)
    num_lines2 = len(table2_lines)
    num_lines3 = len(table3_lines)
    max_lines = max(num_lines1, num_lines2, num_lines3)

    # Adiciona linhas vazias para preencher as tabelas até o número máximo de linhas
    table1_lines += [''] * (max_lines - num_lines1)
    table2_lines += [''] * (max_lines - num_lines2)
    table3_lines += [''] * (max_lines - num_lines3)

    # Junta as linhas de cada tabela lado a lado
    table_lines = []
    for i in range(max_lines):
        line = f'{table1_lines[i]} {table2_lines[i]} {table3_lines[i]}'
        table_lines.append(line)

    # Retorna as tabelas combinadas como uma única string
    return '\n'.join(table_lines)


def exibir_tabelas_lado_a_lado(dezenas_20_1, dezenas_20_2, dezenas_20_3):
    # Cria uma tabela vazia com o cabeçalho
    table1 = PrettyTable(['Dezena', 'Atraso', '% Atraso'])
    # Adiciona as linhas na tabela
    for row in dezenas_20_1:
        # Se o atraso estiver vazio, adiciona 0
        atraso = row[1] if row[1] else '0'
        table1.add_row([row[0], atraso, row[2]])

    # Cria uma tabela vazia com o cabeçalho
    table2 = PrettyTable(['Dezena', 'Atraso', '% Atraso'])
    # Adiciona as linhas na tabela
    for row in dezenas_20_2:
        # Se o atraso estiver vazio, adiciona 0
        atraso = row[1] if row[1] else '0'
        table2.add_row([row[0], atraso, row[2]])

    # Cria uma tabela vazia com o cabeçalho
    table3 = PrettyTable(['Dezena', 'Atraso', '% Atraso'])
    # Adiciona as linhas na tabela
    for row in dezenas_20_3:
        # Se o atraso estiver vazio, adiciona 0
        atraso = row[1] if row[1] else '0'
        table3.add_row([row[0], atraso, row[2]])

    # Exibe as tabelas lado a lado
    print(f'{Cores.fg.branco}{split_table(table1, table2, table3)}{Cores.fim}')


def pesquisar_14_dezenas_lindas(cenario, jogo_anterior=None, lista_negra=None):
    # Lista final com todos os jogos gerados com base nas regras de necio
    lista_de_jogos_filtrados = []
    lista_de_jogos_filtrados.clear()
    dezenas_menor_30 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                        27, 28, 29, 30]
    dezenas_maior_30 = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
                        55, 56, 57, 58, 59, 60]
    gerador = GeradorNumerosEstrategiaVizinhos()
    _, _, _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
    msg = f'{Cores.fg.yellow} Aguarde estamos selcionando os jogos... total de jogos descartados >>> {Cores.fg.red}{{}}{Cores.fim}'
    if cenario == 1:

        # as_14_dezenas_lindas = None
        cont = 0
        while True:
            print(msg.format(cont), end='\r', flush=True)
            lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
            jogo_14_dezenas = sample(lista_numeros_vizinhos, 14)

            chamar_funcoes_num = GeradorDeNumeros()
            numeros_sorteados = sorted(jogo_14_dezenas)
            # print(numeros_sorteados)
            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 14 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares

            if valores_validos_par_impar == '7-7' or valores_validos_par_impar == '6-8' or valores_validos_par_impar == '8-6':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos >= 1 and total_primos <= 5:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

                # REQUISITO-03 Fibonacci
            if total_fibonacci <= 5:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 >= 1 and total_multiplos3 <= 7:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

                # REQUISITO-05 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 7:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

                # REQUISITO-06 Dezenas maiores que 30
            if total_dezenas_maior_30 == 7:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

                # REQUISITO-07 validano se tem dezenas etre as 25 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(45)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if num_mais == 10 and num_menos == 4:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

                # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(41, 61):
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue

            # REQUISITO-09 verifica se o jogo tem de 0 a 1 numero do ultimo jogo
            nums_anterior = verifica_jogos_anteriores(numeros_sorteados, jogo_anterior)
            if nums_anterior <= 1:
                lista_tomada_decisao.append(9)
            else:
                cont += 1
                continue

            # Verifica se algum número está na lista negra
            if len(lista_negra) > 0:
                for num in numeros_sorteados:
                    if num in lista_negra:
                        cont += 1
                        break
                else:
                    cont += 1
                    lista_tomada_decisao.append(10)
            else:
                cont += 1
                continue

            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
            # caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 10:
                print_bonito()
                print(
                    f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
                    return lista_de_jogos_filtrados[0]


    elif cenario == 2:
        as_14_dezenas_lindas = None
        gerador_de_1_a_60 = gerador.gerador_de_1_a_60()

        # as_14_dezenas_lindas = None
        cont = 0
        while True:
            print(msg.format(cont), end='\r', flush=True)
            jogo_14_dezenas = sample(gerador_de_1_a_60, 14)
            chamar_funcoes_num = GeradorDeNumeros()
            numeros_sorteados = sorted(jogo_14_dezenas)
            # print(numeros_sorteados)
            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 14 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares

            if valores_validos_par_impar == '7-7' or valores_validos_par_impar == '6-8' or valores_validos_par_impar == '8-6':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos >= 1 and total_primos <= 5:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

                # REQUISITO-03 Fibonacci
            if total_fibonacci <= 5:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 >= 1 and total_multiplos3 <= 7:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

                # REQUISITO-05 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 7:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

                # REQUISITO-06 Dezenas maiores que 30
            if total_dezenas_maior_30 == 7:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

                # REQUISITO-07 validano se tem dezenas etre as 25 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(45)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if num_mais == 10 and num_menos == 4:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

                # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(41, 61):
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue

            # REQUISITO-09 verifica se o jogo tem de 0 a 1 numero do ultimo jogo
            nums_anterior = verifica_jogos_anteriores(numeros_sorteados, jogo_anterior)
            if nums_anterior <= 1:
                lista_tomada_decisao.append(9)
            else:
                cont += 1
                continue

            # Verifica se algum número está na lista negra
            if len(lista_negra) > 0:
                for num in numeros_sorteados:
                    if num in lista_negra:
                        cont += 1
                        break
                else:
                    cont += 1
                    lista_tomada_decisao.append(10)
            else:
                cont += 1
                continue

            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
            # caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 10:
                print_bonito()
                print(
                    f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
                    return lista_de_jogos_filtrados[0]

                # V9


def pesquisar_13_14_20_dezenas(cenario, lista_dezenas):
    # Lista final com todos os jogos gerados com base nas regras de necio
    lista_de_jogos_filtrados = []
    lista_de_jogos_filtrados.clear()
    dezenas_menor_30 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                        27, 28, 29, 30]
    dezenas_maior_30 = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
                        55, 56, 57, 58, 59, 60]
    # gerador = GeradorNumerosEstrategiaVizinhos()
    # _, _, _,  jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
    msg = f'{Cores.fg.yellow} Aguarde estamos selcionando os jogos... total de jogos descartados >>> {Cores.fg.red}{{}}{Cores.fim}'
    if cenario == 20:

        # as_14_dezenas_lindas = None
        cont = 0
        while True:
            print(msg.format(cont), end='\r', flush=True)
            # lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
            jogo_20_dezenas = sample(lista_dezenas, 20)
            # print('jogo_20_dezenas', jogo_20_dezenas)
            chamar_funcoes_num = GeradorDeNumeros()
            numeros_sorteados = sorted(jogo_20_dezenas)

            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 20 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares

            if valores_validos_par_impar == '10-10' or valores_validos_par_impar == '9-11' or valores_validos_par_impar == '11-9':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos >= 1 and total_primos <= 5:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

                # REQUISITO-03 Fibonacci
            if total_fibonacci <= 2:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 >= 1 and total_multiplos3 <= 6:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

                # REQUISITO-05 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 10:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

                # REQUISITO-06 Dezenas maiores que 30
            if total_dezenas_maior_30 == 10:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

                # REQUISITO-07 validano se tem dezenas etre as 45 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(40)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(20)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if num_mais == 14 and num_menos == 6:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

                # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(40, 61):
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue
            # print('Inicio 21 fim 40')
            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
            # caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 8:
                print_bonito()
                print(
                    f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
                    return lista_de_jogos_filtrados[0]


    elif cenario == 13:

        # as_14_dezenas_lindas = None
        cont = 0
        while True:
            print(msg.format(cont), end='\r', flush=True)
            # lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
            jogo_13_dezenas = sample(lista_dezenas, 13)

            chamar_funcoes_num = GeradorDeNumeros()
            numeros_sorteados = sorted(jogo_13_dezenas)
            # print(numeros_sorteados)
            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 13 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares

            if valores_validos_par_impar == '7-6' or valores_validos_par_impar == '6-7':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos >= 3 and total_primos <= 8:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

                # REQUISITO-03 Fibonacci
            if total_fibonacci <= 2:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 >= 2 and total_multiplos3 <= 6:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

                # REQUISITO-05 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 7:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

                # REQUISITO-06 Dezenas maiores que 30
            if total_dezenas_maior_30 == 6:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

                # REQUISITO-07 validano se tem dezenas etre as 45 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(45)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if num_mais == 8 and num_menos == 5:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

                # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(40, 61):
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue

            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
            # caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 8:
                print_bonito()
                print(
                    f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
                    return lista_de_jogos_filtrados[0]

    elif cenario == 14:

        # as_14_dezenas_lindas = None
        cont = 0
        while True:
            print(msg.format(cont), end='\r', flush=True)
            # lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
            jogo_14_dezenas = sample(lista_dezenas, 14)

            chamar_funcoes_num = GeradorDeNumeros()
            numeros_sorteados = sorted(jogo_14_dezenas)
            # print(numeros_sorteados)
            # FUNCAO PARES
            lista_pares = chamar_funcoes_num.gerar_pares()
            # FUNCAO IMPARES
            lista_impares = chamar_funcoes_num.gerar_impares()
            # FUNCAO PRIMOS
            lista_primos = chamar_funcoes_num.gerar_primos()
            # FUNCAO FIBONACCI
            lista_fibonacci = chamar_funcoes_num.gerar_fibonacci()
            # FUNCAO MULTIPLOS DE 3
            lista_multiplos_de_3 = chamar_funcoes_num.gerar_multiplos_de_3()

            # Gerando a saida com o total de dezes para cada tipo com base nas 6 sorteadas
            total_pares = len(np.intersect1d(numeros_sorteados, lista_pares))  # lista_pares
            total_pares = len(np.intersect1d(numeros_sorteados, lista_impares))  # lista_pares
            total_primos = len(np.intersect1d(numeros_sorteados, lista_primos))
            total_fibonacci = len(np.intersect1d(numeros_sorteados, lista_fibonacci))
            total_multiplos3 = len(np.intersect1d(numeros_sorteados, lista_multiplos_de_3))
            total_dezenas_menor_30 = len(np.intersect1d(numeros_sorteados, dezenas_menor_30))
            total_dezenas_maior_30 = len(np.intersect1d(numeros_sorteados, dezenas_maior_30))

            # Formatando a saida de pares e impares como strinf '2-4' '3-3' '4-2'
            total_impares = 14 - total_pares
            valores_validos_par_impar = f'{total_pares}-{total_impares}'
            # Lsita com o retorno das regras de negistr de cada um dos 29 filtros para tomada de decisão se o jogo será impresso ou não.
            lista_tomada_decisao = []
            # REQUISITO-01 Pares e Impares

            if valores_validos_par_impar == '7-7':
                lista_tomada_decisao.append(1)
            else:
                cont += 1
                continue

            # REQUISITO-02 Primos
            if total_primos >= 3 and total_primos <= 8:
                lista_tomada_decisao.append(2)
            else:
                cont += 1
                continue

                # REQUISITO-03 Fibonacci
            if total_fibonacci <= 2:
                lista_tomada_decisao.append(3)
            else:
                cont += 1
                continue

            # REQUISITO-04 Multiplos de 3
            if total_multiplos3 >= 2 and total_multiplos3 <= 6:
                lista_tomada_decisao.append(4)
            else:
                cont += 1
                continue

                # REQUISITO-05 Dezenas Menores igual a 30
            if total_dezenas_menor_30 == 7:
                lista_tomada_decisao.append(5)
            else:
                cont += 1
                continue

                # REQUISITO-06 Dezenas maiores que 30
            if total_dezenas_maior_30 == 7:
                lista_tomada_decisao.append(6)
            else:
                cont += 1
                continue

                # REQUISITO-07 validano se tem dezenas etre as 45 mais ou 15 menos sorteadas
            banco = BancoDeDados()
            _, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(45)
            _, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
            num_mais = len(set(numeros_sorteados).intersection(dezenas_mais))
            num_menos = len(set(numeros_sorteados).intersection(dezenas_menos))
            if num_mais == 9 and num_menos == 5:
                lista_tomada_decisao.append(7)
            else:
                cont += 1
                continue

                # REQUISITO-08 Verifica se o jogo está entre essas condições [inicio entre 01 a 20 e final de 41 a 60]
            if numeros_sorteados[0] in range(1, 21) and numeros_sorteados[-1] in range(40, 61):
                lista_tomada_decisao.append(8)
            else:
                cont += 1
                continue

            # Aqui onde tomamos a decisão de qual jogo gerado aleatório atende os os 13 requisitos,
            # caso atendam, será incluso na lista final
            if len(lista_tomada_decisao) == 8:
                print_bonito()
                print(
                    f'{Cores.fg.blue}#          >>>>>>>>>>>>>>>>>>>>>>>>> TOTAL DE JOGOS DESCARTADOS NOS FILTROS >>> {Cores.fg.red}{cont}{Cores.fim}')
                if numeros_sorteados not in lista_de_jogos_filtrados:
                    lista_de_jogos_filtrados.append(numeros_sorteados)
                    return lista_de_jogos_filtrados[0]


def calcular_num_combinacoes(numeros, k):
    if isinstance(numeros, int):
        n = numeros
    else:
        n = len(numeros)
    num_combinacoes = math.comb(n, k)
    return num_combinacoes


def print_mega_sena_table(jogo, data, concurso):
    # tabela de 6x10 com os números de 1 a 60
    table = [[i + j * 10 for i in range(1, 11)] for j in range(6)]
    # converte os elementos de jogo em inteiros
    jogo = [int(num) for num in jogo]
    # imprime a nova linha com o título
    print(f'{"":19}╔{"═" * 49}╗')
    # adiciona cor ao texto da data e do concurso
    data_text = colored(f'{data}', 'blue', attrs=['bold'])
    concurso_text = colored(f'{concurso}', 'blue', attrs=['bold'])
    print(f'{"":19}║ {"Data:":<8} {data_text}    ║    {"Concurso:  ":<10} {concurso_text} {"   ║"}')
    # imprime a tabela formatada com as bordas duplas e as linhas de divisão
    indent = ' ' * 19  # string com 15 espaços
    print(f'{indent}╠════╦════╦════╦════╦════╦════╦════╦════╦════╦════╣')
    for row in table:
        print(f'{indent}║', end='')
        for cell in row[:9]:
            if cell in jogo:
                print(colored(f' {cell:02} ', 'white', 'on_green', attrs=['bold']), end='|')
            else:
                print(f' {cell:02} ', end='|')
        if row[9] in jogo:
            print(colored(f' {row[9]:02} ', 'white', 'on_green', attrs=['bold']), end='║\n')
        else:
            print(f' {row[9]:02} ', end='║\n')
        if row != table[-1]:
            print(f'{indent}╠════╬════╬════╬════╬════╬════╬════╬════╬════╬════╣')
    print(f'{indent}╚════╩════╩════╩════╩════╩════╩════╩════╩════╩════╝')


def boas_vindas():
    # titulo = 'Bem-vindo ao nosso sistema inteligente para gerar jogos de loteria!'
    titulo = 'Bem-vindo ao nosso sistema para gerar jogos de Mega-Sena inteligente!'
    texto = f'Com a nossa ferramenta, você pode criar jogos de 6 números e desdobramentos de 14 dezenas com garantia de 4 acertos, acertando as 6 entre as 14. Além disso, você pode baixar o histórico da Mega em um arquivo CSV e aplicar suas próprias validações para imprimir os melhores jogos baseados em 34 requisitos. Estamos animados para ajudá-lo a aumentar suas chances de ganhar na loteria! LTM agradeçe a sua preferência!'
    indent = ' ' * 15  # string com 15 espaços
    tamanho_tabela = 80
    tamanho_texto = len(texto)

    linha_superior = '╔' + '═' * (tamanho_tabela - 2) + '╗'
    linha_inferior = '╚' + '═' * (tamanho_tabela - 2) + '╝'
    linha_vazia = '║' + ' ' * (tamanho_tabela - 2) + '║'
    linha_titulo = '║' + ' ' + titulo.center(tamanho_tabela - 4) + ' ║'

    print(' ' * 7 + linha_superior)
    print(' ' * 7 + linha_titulo)
    print(' ' * 7 + '╠' + '═' * (tamanho_tabela - 2) + '╣')

    # quebrar o texto em linhas para caber na tabela
    linhas_texto = []
    while len(texto) > tamanho_tabela - 4:
        indice_espaco = texto[:tamanho_tabela - 4].rfind(' ')
        linha_atual = texto[:indice_espaco]
        linhas_texto.append(linha_atual.center(tamanho_tabela - 2))
        texto = texto[indice_espaco + 1:]
    linhas_texto.append(texto.center(tamanho_tabela - 2))

    for linha in linhas_texto:
        print(' ' * 7 + '║{}║'.format(linha))

    print(' ' * 7 + linha_vazia)
    print(' ' * 7 + linha_inferior)


# ----------------------------------------------------------------------------------------------------#
################################### INICIO DO PROGRAMA PRINCIPAL #####################################
# ----------------------------------------------------------------------------------------------------#

print_bonito()
print()
print(pyfiglet.figlet_format('    LTM', font='starwars', justify='center'))
print_bonito()
boas_vindas()
print_bonito()
print(f'{Cores.fg.black} Criado por                              : {Cores.fg.branco}Rogério Máximo Vieira{Cores.fim} ')
print(f'{Cores.fg.black} Linguágem                               : {Cores.fg.branco}Python 3.10{Cores.fim} ')
print(f'{Cores.fg.black} Sugestões e melhorias enviar e-mail para: {Cores.fg.branco}roncelio33@gmail.com{Cores.fim} ')

print_bonito()
gerador = GeradorNumerosEstrategiaVizinhos()
# resultado_atual, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
_, data, concurso, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()

# INSERIR ATUALIZAR RESULTADOS DA MEGA NO BD
todos_resulados_mega = gerador.todos_jogos_mega_sena()
banco = BancoDeDados()
resultados = sorted(todos_resulados_mega, key=lambda r: r['concurso'])
ultimo_id = banco.obter_ultimo_id_concurso()
for id in tqdm(range(ultimo_id + 1, len(todos_resulados_mega) + 1)):
    banco.inserir_resultados(resultados)
print_bonito()

as_15_mais_sorteadas, dezenas_mais = banco.selecionar_dezenas_mais_sorteadas(25)
as_15_menos_sorteadas, dezenas_menos = banco.selecionar_dezenas_menos_sorteadas(15)
tabela = PrettyTable()
tabela.field_names = ["Posição (+)", "As 15 mais sorteadas", "Posição (-)", "As 15 menos sorteadas"]
for i, (mais_sort, menos_sort) in enumerate(zip(as_15_mais_sorteadas, as_15_menos_sorteadas)):
    posicao = i + 1
    tabela.add_row([posicao, mais_sort, posicao, menos_sort])
print(f'{Cores.fg.branco}{tabela}{Cores.fim}')
print_bonito()

saida_tabela, dezenas_15_atraso, dezenas_15_ultimos = baixar_tabela_atraso()

dezenas_20_1 = saida_tabela[:20]
dezenas_20_2 = saida_tabela[20:40]
dezenas_20_3 = saida_tabela[40:60]
exibir_tabelas_lado_a_lado(dezenas_20_1, dezenas_20_2, dezenas_20_3)

print_bonito()
print()
print(pyfiglet.figlet_format('        MEGA-SENA', justify='center'))
print_bonito()
print_mega_sena_table(jogo_anterior, data, concurso)

while True:
    try:
        opcao = menu(['Permite sair da aplicação ou pressione o atalho (Ctrl + C)',
                      'Permite gerar jogos usando a estratégia do vizinho',
                      'Permite gerar jogos aleatórios de 1 a 60',
                      'Permite gerar jogos informando as dezenas de 6 a 60',
                      'Permite baixar histórico de todos os jogos da Mega-Sena .csv',
                      'Permite apagar um concurso do Banco de Dados',
                      'Permite ver os requisitos aplicados nesse APP para gerar os jogos',
                      'Permite gerar combinações de 13, 14 e 20 dezenas com base em uma lista'])

        if opcao == 1:
            while True:
                gerador = GeradorNumerosEstrategiaVizinhos()
                lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
                print(
                    f'{Cores.fg.yellow} Total números na lista de vizinhos do último concurso: {Cores.fg.red}{len(lista_numeros_vizinhos)}{Cores.fim}')
                print_bonito()
                print(f'{Cores.fg.yellow} Números vizinhos do último concurso:{Cores.fim}')
                print_bonito()

                # Código para mostrar os numeros na telas alinhados em linhas de 15
                lista_numeros_vizinhos_print = lista_numeros_vizinhos
                lista_numeros_vizinhos_print.sort()
                for i in range(0, len(lista_numeros_vizinhos_print), 15):
                    linha = lista_numeros_vizinhos_print[i:i + 15]
                    print(' [', ' '.join(str(n).rjust(2) for n in linha), ']')
                print_bonito()
                try:
                    # pede ao usuário para informar as dezenas que não deseja sair nos jogos
                    lista_negra_str = input(
                        f'{Cores.fg.green} Informe as dezenas que não deseja que saiam nos jogos ou 0 {Cores.fg.red}(separe por vírgula):{Cores.fim} ')
                    # transforma a string em uma lista de inteiros
                    lista_negra = [int(d) for d in lista_negra_str.split(',')]
                except:
                    lista_negra = [0]

                # Função para pegar 14 dezenas com base em analise de alguns requisitos.
                as_14_dezenas_lindas = pesquisar_14_dezenas_lindas(cenario=1, lista_negra=lista_negra)
                print_bonito()
                # Mostra as 14 dezenas escolhifas para gerar o desdobrmamento e mostra os 11 jogos gerados
                print(f'{Cores.fg.yellow} 14 DEZENAS: {Cores.fg.pink}{as_14_dezenas_lindas}{Cores.fim}')
                print_bonito()
                imprimir_jogos(as_14_dezenas_lindas)
                print_bonito()

                quantidade_jogos = int(
                    input(f'{Cores.fg.green} Quantos jogos inteligentes você deseja gerar? {Cores.fim}'))
                if quantidade_jogos > 0:
                    num_combin = calcular_num_combinacoes(lista_numeros_vizinhos, k=6)

                    # Laço de repetição para gerar os jogos conforme a quantidade informada pelo usuario.
                    # _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                    _, _, _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                    lista_de_jogos_filtrados = gerador_inteligente_jogos('NORMAL', quantidade_jogos,
                                                                         lista_numeros_vizinhos,
                                                                         jogo_anterior=jogo_anterior,
                                                                         lista_negra=lista_negra)
                    gravar_jogos_filtrados(lista_de_jogos_filtrados)

                print_bonito()
                gerar_novos = input(f'{Cores.fg.green} Deseja gerar outros jogos? {Cores.fim}').upper()
                if gerar_novos[0] == 'S':
                    continue
                else:
                    break
        elif opcao == 2:
            while True:
                gerador = GeradorNumerosEstrategiaVizinhos()
                gerador_de_1_a_60 = gerador.gerador_de_1_a_60()
                print(f'{Cores.fg.yellow} Números de 1 a 60: {Cores.fg.red}{len(gerador_de_1_a_60)}{Cores.fim}')
                print_bonito()

                gerador_de_1_a_60_print = gerador_de_1_a_60
                gerador_de_1_a_60_print.sort()
                for i in range(0, len(gerador_de_1_a_60_print), 15):
                    linha = gerador_de_1_a_60_print[i:i + 15]
                    print(' [', ' '.join(str(n).rjust(2) for n in linha), ']')
                print_bonito()
                try:
                    # pede ao usuário para informar as dezenas que não deseja sair nos jogos
                    lista_negra_str = input(
                        f'{Cores.fg.green} Informe as dezenas que não deseja que saiam nos jogos ou 0 {Cores.fg.red}(separe por vírgula):{Cores.fim} ')
                    # transforma a string em uma lista de inteiros
                    lista_negra = [int(d) for d in lista_negra_str.split(',')]
                except:
                    lista_negra = [0]
                    # Função para pegar 14 dezenas com base em analise de alguns requisitos.
                as_14_dezenas_lindas = pesquisar_14_dezenas_lindas(cenario=2, lista_negra=lista_negra)
                # Mostra as 14 dezenas escolhifas para gerar o desdobrmamento e mostra os 11 jogos gerados
                print_bonito()
                print(f'{Cores.fg.yellow} 14 DEZENAS: {Cores.fg.pink}{as_14_dezenas_lindas}{Cores.fim}')
                print_bonito()
                imprimir_jogos(as_14_dezenas_lindas)
                print_bonito()

                quantidade_jogos = int(
                    input(f'{Cores.fg.green} Quantos jogos inteligentes você deseja gerar? {Cores.fim}'))
                # Laço de repetição para gerar os jofos conforme a quantidade informada pelo usuario.
                # _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                if quantidade_jogos > 0:
                    _, _, _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                    lista_de_jogos_filtrados = gerador_inteligente_jogos('NORMAL', quantidade_jogos, gerador_de_1_a_60,
                                                                         jogo_anterior=jogo_anterior,
                                                                         lista_negra=lista_negra)

                    gravar_jogos_filtrados(lista_de_jogos_filtrados)
                print_bonito()
                gerar_novos = input(f'{Cores.fg.green} Deseja gerar outros jogos? {Cores.fim}').upper()
                if gerar_novos[0] == 'S':
                    continue
                else:
                    break
        elif opcao == 3:
            gerador = GeradorNumerosEstrategiaVizinhos()
            numeros_selecionados = solicitar_dezenas()

            numeros_selecionados_print = numeros_selecionados
            numeros_selecionados_print.sort()
            for i in range(0, len(numeros_selecionados_print), 15):
                linha = numeros_selecionados_print[i:i + 15]
                print(' [', ' '.join(str(n).rjust(2) for n in linha), ']')

            print_bonito()
            quantidade_jogos = int(input(f'{Cores.fg.green} Quantos jogos inteligentes você deseja gerar? {Cores.fim}'))
            if quantidade_jogos > 0:
                # Laço de repetição para gerar os jofos conforme a quantidade informada pelo usuario.
                # _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                _, _, _, jogo_anterior = gerador.obter_ultimo_jogo_mega_sena()
                lista_de_jogos_filtrados = gerador_inteligente_jogos('NORMAL', quantidade_jogos, numeros_selecionados,
                                                                     jogo_anterior=jogo_anterior)
                gravar_jogos_filtrados(lista_de_jogos_filtrados)

        elif opcao == 4:
            obter_e_salvar_resultado_mega_sena()

        elif opcao == 5:
            conc = int(input(f'{Cores.fg.green} informe o número do concurso que deseja apagar:{Cores.fim} '))
            print_bonito()
            banco = BancoDeDados()
            opc_apgar = input(f'{Cores.fg.green} Deseja seguir? {Cores.fim}').upper()
            if opc_apgar[0] == 'S':
                print_bonito()
                banco.deletar_resultado_por_concurso(conc)
            else:
                print_bonito()
                print(f'{Cores.fg.yellow} OK, saindo sem a limpeza...{Cores.fim} ')
        elif opcao == 6:

            print(
                f'{Cores.fg.yellow} REQUISITO-01 - Seleção de números pares e impares {Cores.fg.blue}[2-4, 3-3 e 4-2]{Cores.fim}')
            print(f'{Cores.fg.yellow} REQUISITO-02 - Seleção de números Primos {Cores.fg.blue}[1 a 3]{Cores.fim}')
            print(f'{Cores.fg.yellow} REQUISITO-03 - Seleção de números Fibonacci {Cores.fg.blue}[0 a 2]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-04 - Seleção de números Múltiplos  de 03 {Cores.fg.blue}[1 a 3]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-05 - Seleção de Dezenas na Moldura da Cartela{Cores.fg.blue}[2 a 4]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-06 - Seleção de Dezenas no Centro da Cartela {Cores.fg.blue}[2 a 4]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-07 - Seleção de Dezenas Menores igual a 30 {Cores.fg.blue}[2 a 4]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-08 - Seleção de Dezenas maiores que 30 {Cores.fg.blue}[2 a 4]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-09 - Seleção de Dezenas do Quadrante 01 da Cartela {Cores.fg.blue}[1 a 2]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-10 - Seleção de Dezenas do Quadrante 02 da Cartela {Cores.fg.blue}[1 a 2]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-11 - Seleção de Dezenas do Quadrante 03 da Cartela {Cores.fg.blue}[1 a 2]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-12 - Seleção de Dezenas do Quadrante 04 da Cartela {Cores.fg.blue}[1 a 2]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-13 - Seleção da Soma das 6 dezenas {Cores.fg.blue}[150 a 230]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-14 - Seleção de dezenas na Linha 01 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-15 - Seleção de dezenas na Linha 02 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-16 - Seleção de dezenas na Linha 03 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-17 - Seleção de dezenas na Linha 04 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-18 - Seleção de dezenas na Linha 05 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-19 - Seleção de dezenas na Linha 06 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-20 - Seleção de dezenas na Coluna 01 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-21 - Seleção de dezenas na Coluna 02 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-22 - Seleção de dezenas na Coluna 03 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-23 - Seleção de dezenas na Coluna 04 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-24 - Seleção de dezenas na Coluna 05 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-25 - Seleção de dezenas na Coluna 06 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-26 - Seleção de dezenas na Coluna 07 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-27 - Seleção de dezenas na Coluna 08 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-28 - Seleção de dezenas na Coluna 09 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-29 - Seleção de dezenas na Coluna 10 da Cartela{Cores.fg.blue}[0 a 1]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-30 - Seleção de jogos com sequência menor igual a {Cores.fg.blue}[ 2 ]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-31 - Seleção de dezenas entre as 25 mais e 15 menos sorteadas{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-32 - Seleção de jogos que já tiveram 04 acertos em jogos anteriores{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-33 - Seleção de jogos que tenha inicio e fim {Cores.fg.blue}[entre 01 a 20 e final de 41 a 60]{Cores.fim}')
            print(
                f'{Cores.fg.yellow} REQUISITO-34 - Seleção de jogos que tenha números do ultimo jogo {Cores.fg.blue}[0 a 1]{Cores.fim}')
            sleep(10)
        elif opcao == 7:
            try:
                # pede ao usuário para informar as dezenas que não deseja sair nos jogos
                while True:
                    total_dezenas = int(input(
                        f'{Cores.fg.green} Informe a quantidade de dezenas deseja gerar combinações 13, 14 ou 20:{Cores.fim} '))
                    if total_dezenas in [13, 14, 20]:
                        break
                    else:
                        print(f'{Cores.fg.red} Opção invalida{Cores.fim}')
                        print_bonito()
                        continue

                print_bonito()
                total_cobim = int(input(
                    f'{Cores.fg.green} Informe a quantidade de combinações deseja gerar com {Cores.fg.red}{total_dezenas}:{Cores.fim} '))
                print_bonito()
                opc = menu(['Permite sair da aplicação ou pressione o atalho (Ctrl + C)',
                            'Permite gerar as combinações a partir da lista que você informar',
                            'Permite gerar as combinações a partir da lista vizinhos',
                            'Permite gerar as combinações a partir das dezenas 1 a 60'])
                # opc = input(f'{Cores.fg.green} Desejar gerar os jogos de sua lista ou da lista de vizinhos {Cores.fg.red}[ M / V ] {total_dezenas}:{Cores.fim} ').upper()
                # print_bonito()
                if opc == 1:
                    lista_dezenas_combin_str = input(
                        f'{Cores.fg.green} Informe as dezenas que deseja gerar a combinação de {total_dezenas} dezenas ou 0 {Cores.fg.red}(separado por vírgula):{Cores.fim} ')
                    # transforma a string em uma lista de inteiros
                    lista_dezenas_combin = [int(d) for d in lista_dezenas_combin_str.split(',')]
                    for combin in range(1, total_cobim + 1):
                        as_13_20_dezenas_lindas = pesquisar_13_14_20_dezenas(cenario=total_dezenas,
                                                                             lista_dezenas=lista_dezenas_combin)
                        print_bonito()
                        print(
                            f'{Cores.fg.yellow} COMBINAÇÂO-{combin} - {total_dezenas} DEZENAS: {Cores.fg.pink}{as_13_20_dezenas_lindas}{Cores.fim}')

                elif opc == 2:
                    lista_numeros_vizinhos = gerador.gerar_numeros_vizinhos()
                    # Código para mostrar os numeros na telas alinhados em linhas de 15
                    lista_numeros_vizinhos_print = lista_numeros_vizinhos
                    lista_numeros_vizinhos_print.sort()
                    print(
                        f'{Cores.fg.yellow} Total números na lista de vizinhos do último concurso: {Cores.fg.red}{len(lista_numeros_vizinhos)}{Cores.fim}')
                    print_bonito()
                    print(f'{Cores.fg.yellow} Números vizinhos do último concurso:{Cores.fim}')
                    print_bonito()
                    for i in range(0, len(lista_numeros_vizinhos_print), 15):
                        linha = lista_numeros_vizinhos_print[i:i + 15]
                        print(' [', ' '.join(str(n).rjust(2) for n in linha), ']')

                    for combin in range(1, total_cobim + 1):
                        as_13_20_dezenas_lindas = pesquisar_13_14_20_dezenas(cenario=total_dezenas,
                                                                             lista_dezenas=lista_numeros_vizinhos)
                        print_bonito()
                        print(
                            f'{Cores.fg.yellow} COMBINAÇÂO-{combin} - {total_dezenas} DEZENAS: {Cores.fg.pink}{as_13_20_dezenas_lindas}{Cores.fim}')
                    # print_bonito()

                elif opc == 3:
                    gerador = GeradorNumerosEstrategiaVizinhos()
                    gerador_de_1_a_60 = gerador.gerador_de_1_a_60()
                    print(f'{Cores.fg.yellow} Números de 1 a 60: {Cores.fg.red}{len(gerador_de_1_a_60)}{Cores.fim}')
                    print_bonito()

                    gerador_de_1_a_60_print = gerador_de_1_a_60
                    gerador_de_1_a_60_print.sort()
                    for i in range(0, len(gerador_de_1_a_60_print), 15):
                        linha = gerador_de_1_a_60_print[i:i + 15]
                        print(' [', ' '.join(str(n).rjust(2) for n in linha), ']')
                    # print_bonito()
                    for combin in range(1, total_cobim + 1):
                        as_13_20_dezenas_lindas = pesquisar_13_14_20_dezenas(cenario=total_dezenas,
                                                                             lista_dezenas=lista_numeros_vizinhos)
                        print_bonito()
                        print(
                            f'{Cores.fg.yellow} COMBINAÇÂO-{combin} - {total_dezenas} DEZENAS: {Cores.fg.pink}{as_13_20_dezenas_lindas}{Cores.fim}')

                elif opc == 0:
                    print(f'{Cores.fg.red} Finalizando...{Cores.fim}')
                    break

                else:
                    print(f'{Cores.fg.red} Opção invalida{Cores.fim}')
                    break

            except:
                lista_dezenas_combin = [0]


        elif opcao == 0:
            print(f'{Cores.fg.red} Finalizando...{Cores.fim}')
            break
        else:
            print(f'{Cores.fg.red} Opção invalida{Cores.fim}')
            continue
    except (ValueError, EOFError, KeyError, TypeError):
        print_bonito()
        print(f'{Cores.fg.red} ERRO-01-Problema apresentado com os dados de entrada! {Cores.fim}')

    except KeyboardInterrupt:
        print(f'{Cores.fg.red} O usuario preferiu interromper!{Cores.fim}')
        print_bonito()

print(
    f'{Cores.fg.cyan}#==========================================================================================#{Cores.fim}')
print(
    f'{Cores.fg.cyan}#------------------------------------------------------------------------------------------#{Cores.fim}')
print(
    f'{Cores.fg.cyan}#---------------------------- LTM LHE DESEJA UMA BOA SORTE! -------------------------------#{Cores.fim}')
print(
    f'{Cores.fg.cyan}#------------------------------------------------------------------------------------------#{Cores.fim}')
print(
    f'{Cores.fg.cyan}#==========================================================================================#{Cores.fim}')

sleep(5)
