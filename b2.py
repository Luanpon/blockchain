from hashlib import sha256
import json
import time
import random

from flask import Flask,request
import requests

global listaNos
global flagMinerar
global ipMaster
global blockchain

listaNos = []

flagMinerar = True

class Bloco:

    def __init__(self,indice,dados,hashAnterior):
        self.indice = indice
        self.nonce = 0
        self.dados = dados
        self.hashAnterior = hashAnterior
        self.hash = None

    def calcula_hash(self):

        dicionarioBloco = {
            "indice": self.indice,
            "nonce": self.nonce,
            "dados": self.dados,
            "hashAnterior": self.hashAnterior
        }

        stringBloco = json.dumps(dicionarioBloco, sort_keys=True)
        return sha256(stringBloco.encode()).hexdigest()


class Blockchain:

    def __init__(self):
        self.dificuldade = 2
        self.cadeia = []
        self.dadosNaoMinerados = []

    def adicionar_dados(self,dados):
        self.dadosNaoMinerados.append(dados)

    def criar_bloco_genesis(self):
        blocoGenesis = Bloco(0,[],"")
        blocoGenesis.hash = blocoGenesis.calcula_hash()
        self.cadeia.append(blocoGenesis)

    @property
    def ultimo_bloco(self):
        return self.cadeia[-1]

    def minerar(self,bloco):

        global flagMinerar

        bloco.nonce = 0
        bloco.hash = bloco.calcula_hash()
        while not bloco.hash.startswith("0"*self.dificuldade) and flagMinerar:
            bloco.nonce += 2
            bloco.hash = bloco.calcula_hash()

    def criar_novo_bloco(self):
        bloco = Bloco(self.ultimo_bloco.indice+1,
                      self.dadosNaoMinerados,
                      self.ultimo_bloco.hash)

        return bloco

    def validar_mineracao(self,bloco,hashBloco,ipNo):

        global flagMinerar
        global listaNos

        flagMinerar = False

        if (
            hashBloco.startswith("0"*self.dificuldade) and
            hashBloco == bloco.calcula_hash() and
            self.ultimo_bloco.hash == bloco.hashAnterior
        ):
            self.dadosNaoMinerados = []
            self.cadeia.append(bloco)

            dadosBlocos = []

            for b in self.cadeia:
                dadosBlocos.append(b.__dict__)

            file = open("cadeia.txt", "w+")
            file.write(json.dumps({"cadeia": dadosBlocos}))
            file.close()

            for i in range(len(listaNos)):
                if listaNos[i]["ip"] == ipNo:
                    listaNos[i]["saldo"] += 1

            file = open("nos.txt", "w+")
            file.write(json.dumps({"listaNos": listaNos}))
            file.close()

        flagMinerar = True

    def validar_cadeia(self,cadeia):

        for i in range(1, len(cadeia)-1, 1):

            blocoAuxiliar = Bloco(cadeia[i]["indice"], cadeia[i]["dados"], cadeia[i]["hashAnterior"])
            blocoAuxiliar.nonce = cadeia[i]["nonce"]
            blocoAuxiliar.hash = cadeia[i]["hash"]

            if cadeia[i]["hashAnterior"] != cadeia[i-1]["hash"]:
                return False
            if cadeia[i]["hash"] != blocoAuxiliar.calcula_hash():
                return False

        return True

aplicacao = Flask(__name__)
blockchain = Blockchain()

try:
    file2 = open("nos.txt","r")
    dadosFile2 = file2.read()
    if dadosFile2!=None and dadosFile2!="":
        dadosFile2 = json.loads(dadosFile2)
        listaNos = dadosFile2["listaNos"]
except:
    pass
finally:
    try:
        file2.close()
    except:
        pass

try:
    file2 = open("cadeia.txt","r")
    dadosFile2 = file2.read()
    if dadosFile2!=None and dadosFile2!="":
        dadosFile2 = json.loads(dadosFile2)
        for dado in dadosFile2["cadeia"]:
            novoBloco = Bloco(dado["indice"],dado["dados"],dado["hashAnterior"])
            novoBloco.hash = dado["hash"]
            novoBloco.nonce = dado["nonce"]
            blockchain.cadeia.append(novoBloco)
except:
    pass
finally:
    try:
        file2.close()
    except:
        pass

if len(blockchain.cadeia) == 0:
    blockchain.criar_bloco_genesis()

@aplicacao.route('/minerar',methods=['GET'])
def minerar():

    global blockchain
    global flagMinerar
    global listaNos
    global ipMaster

    ipMaster = "http://127.0.0.1:5000/"

    headers = {'Content-Type': "application/json"}
    dadosJson = {"ip": request.host_url}

    requisicao = requests.post("{}listar_nos".format(ipMaster),
                               data=json.dumps(dadosJson), headers=headers)

    listaNos = requisicao.json()["listaNos"]

    for no in listaNos:
        if testar_conexao(no):
            dadosJson = {"listaNos": listaNos}
            requisicao = requests.post("{}atualizar_nos".format(no["ip"]),
                                       data=json.dumps(dadosJson), headers=headers)

    atualizar_cadeia()

    while True:

        if len(blockchain.dadosNaoMinerados)>0:

            bloco = blockchain.criar_novo_bloco()
            blockchain.minerar(bloco)

            if flagMinerar:

                for no in listaNos:
                    if testar_conexao(no):

                        headers = {'Content-Type': "application/json"}

                        dadosJson = {
                            "indice": bloco.indice,
                            "dados": bloco.dados,
                            "hashAnterior":bloco.hashAnterior,
                            "nonce":bloco.nonce,
                            "hash": bloco.hash,
                            "ip": request.host_url
                        }

                        requisicao = requests.post("{}validar_mineracao".format(no["ip"]),
                                      data=json.dumps(dadosJson),headers=headers)


@aplicacao.route('/validar_mineracao',methods=['POST'])
def validar_mineracao():

    global blockchain
    global ipMaster
    global listaNos

    requisicao = request.get_json()

    bloco = Bloco(requisicao["indice"],
                  requisicao["dados"],
                  requisicao["hashAnterior"])

    bloco.nonce = requisicao["nonce"]
    bloco.hash = requisicao["hash"]

    blockchain.validar_mineracao(bloco,bloco.hash,requisicao["ip"])
    atualizar_cadeia()

    headers = {'Content-Type': "application/json"}

    dadosJson = {
        "listaNos": listaNos
    }

    requisicao = requests.post("{}atualiza_nos".format(ipMaster),
                               data=json.dumps(dadosJson), headers=headers)

    return json.dumps({"status": 1})

def atualizar_cadeia():

    global blockchain
    global listaNos

    listaCadeias = []
    todasListasNos = []

    for no in listaNos:
        if testar_conexao(no):
            requisicao = requests.get("{}obter_cadeia".format(no["ip"]))
            listaCadeias.append(requisicao.json()["cadeia"])

            requisicao = requests.get("{}listar_nos".format(no["ip"]))
            todasListasNos.append(requisicao.json()["listaNos"])

    cadeiaAtual = []
    for bloco in blockchain.cadeia:
        cadeiaAtual.append(bloco.__dict__)

    for cadeia in listaCadeias:

        if (
            ( listaCadeias.count(cadeia) > listaCadeias.count(cadeiaAtual) ) or
            ( not blockchain.validar_cadeia(cadeiaAtual) and blockchain.validar_cadeia(cadeia) ) or
            len(cadeia) > len(cadeiaAtual)
        ):
            blockchain.cadeia = []
            for i in range(len(cadeia)):
                novoBloco = Bloco(cadeia[i]["indice"],cadeia[i]["dados"],cadeia[i]["hashAnterior"])
                novoBloco.hash = cadeia[i]["hash"]
                novoBloco.nonce = cadeia[i]["nonce"]
                blockchain.cadeia.append(novoBloco)

            dadosBlocos = []

            for bloco in blockchain.cadeia:
                dadosBlocos.append(bloco.__dict__)

            file = open("cadeia.txt", "w+")
            file.write(json.dumps({"cadeia": dadosBlocos}))
            file.close()

            cadeiaAtual = []
            for bloco in blockchain.cadeia:
                cadeiaAtual.append(bloco.__dict__)

    for lista in todasListasNos:
        if todasListasNos.count(lista) > todasListasNos.count(listaNos):
            listaNos = lista


@aplicacao.route('/obter_cadeia',methods=['GET'])
def obter_cadeia():

    global blockchain

    dadosBlocos = []

    for bloco in blockchain.cadeia:
        dadosBlocos.append(bloco.__dict__)

    return json.dumps({"cadeia": dadosBlocos})


@aplicacao.route('/listar_nos',methods=['GET'])
def listar_nos():

    global listaNos
    return json.dumps({"listaNos": listaNos})


@aplicacao.route('/adicionar_dados',methods=['POST'])
def adicionar_dados():

    global blockchain

    requisicao = request.get_json()
    blockchain.dadosNaoMinerados.append(requisicao["dados"])
    return json.dumps({"status": requisicao["dados"]})

@aplicacao.route('/notificar_dados',methods=['GET'])
def notificar_dados():

    global listaNos
    global blockchain

    headers = {'Content-Type': "application/json"}

    stringDados = ""
    for i in range(random.randint(3,15)):

        #stringDados += random.choice(["cras ", "eget ", "ipsum ", "eget ", "urna ", "condimentum ", "ornare ",
        #                              "pellentesque ", "egestas ", "turpis ", "a ", "commodo ", "pretium ",
        #                              "elit ", "dolor ", "iaculis ", "nisl ", "eget ", "laoreet ", "lacus ",
        #                              "felis ", "nec ", "risus ", "proin ", "quis ", "erat ", "fringilla ",
        #                              "facilisis ", "turpis ", "eget ", "dictum ", "leo ", "aliquam ", "ac ",
        #                              "feugiat ", "ligula ", "eget ", "egestas ", "augue ", "proin ", "ullamcorper ",
        #                              "mauris ", "vel ", "nisi ", "faucibus ", "volutpat ", "nullam ", "dignissim ",
        #                              "consectetur ", "risus ", "eu ", "tempor ", "morbi ", "molestie ", "vestibulum ",
        #                              "tincidunt ", "maecenas ", "sagittis ", "eros ", "vitae ", "consectetur ",
        #                              "ultricies ", "elit ", "erat ", "vestibulum ", "eros ", "quis ", "vestibulum ",
        #                              "velit ", "leo ", "eget ", "enim ", "nulla ", "vel ", "tincidunt ", "felis ",
        #                              "proin ", "dapibus ", "ipsum ", "ut ", "blandit ", "imperdiet ", "sapien ",
        #                              "lectus ", "molestie ", "nisl ", "non ", "facilisis ", "lorem ", "neque ", "at ",
        #                              "ex "])

        stringDados += random.choice(["SUSPENDISSE ", "POTENTI ", "PRAESENT ", "EUISMOD ", "MAGNA ", "ID ", "SEM ",
                                      "VULPUTATE ", "NON ", "CURSUS ", "TORTOR ", "DAPIBUS ", "NULLA ", "A ",
                                      "LOBORTIS ", "ARCU ", "ETIAM ", "MAXIMUS ", "NISL ", "AC ", "ANTE ", "DAPIBUS ",
                                      "VULPUTATE ", "FUSCE ", "A ", "ANTE ", "GRAVIDA ", "DAPIBUS ", "EROS ", "AC ",
                                      "ALIQUAM ", "TORTOR ", "INTEGER ", "FAUCIBUS ", "ULLAMCORPER ", "LUCTUS ",
                                      "VESTIBULUM ", "EGET ", "EX ", "IN ", "URNA ", "MOLESTIE ", "DIGNISSIM ", "IN ",
                                      "LACINIA ", "RUTRUM ", "SOLLICITUDIN ", "CRAS ", "DAPIBUS ", "MI ", "A ",
                                      "MOLESTIE ", "LAOREET ", "DONEC ", "CONSECTETUR ", "MASSA ", "MAURIS ", "SIT ",
                                      "AMET ", "TRISTIQUE ", "NEQUE ", "FINIBUS ", "VITAE ", "IN ", "CONSEQUAT ",
                                      "LIGULA ", "NIBH ", "IN ", "VULPUTATE ", "LACUS ", "AUCTOR ", "AT ", "DONEC ",
                                      "NON ", "LACINIA ", "JUSTO ", "SIT ", "AMET ", "FINIBUS ", "MAGNA ", "AENEAN ",
                                      "MOLLIS ", "LIBERO ", "PURUS ", "UT ", "SAGITTIS ", "ANTE ", "LAOREET ", "UT ",
                                      "FUSCE ", "ALIQUET ", "NEQUE ", "A ", "LIBERO ", "LOBORTIS ", "LUCTUS "])

    dadosJson = {
        "dados": stringDados
    }

    for no in listaNos:
        if testar_conexao(no):
            requisicao = requests.post("{}adicionar_dados".format(no["ip"]),
                                       data=json.dumps(dadosJson), headers=headers)


    return json.dumps({"status":1})

@aplicacao.route('/atualizar_nos',methods=['POST'])
def atualizar_nos():

    global listaNos
    requisicao = request.get_json()

    listaNos = requisicao["listaNos"]

    file = open("nos.txt","w+")
    file.write(json.dumps({"listaNos": listaNos}))
    file.close()

    return json.dumps({"status":1})

def testar_conexao(no):
    try:

        headers = {'Content-Type': "application/json"}

        dadosJson = {
            "testeConexao": ""
        }

        requisicao = requests.post("{}obter_cadeia".format(no["ip"]),
                                   data=json.dumps(dadosJson), headers=headers)

        return True

    except:

        return False


if __name__ == '__main__':
    aplicacao.run(host="0.0.0.0",port=5001)