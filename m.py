
from flask import Flask,request
import requests
import json

aplicacao = Flask(__name__)

global listaNos
global listasAtualizacao

listaNos = []
listasAtualizacao = []

@aplicacao.route('/listar_nos',methods=['POST'])
def lista_nos():

    requisicao = request.get_json()

    estaNaLista = False

    for no in listaNos:
        if no["ip"] == requisicao["ip"]:
            estaNaLista = True

    if not estaNaLista:
        listaNos.append({"ip": requisicao["ip"],
                         "saldo": 0})

    return json.dumps({"listaNos": listaNos})


@aplicacao.route('/atualiza_nos',methods=['POST'])
def atualiza_nos():

    global listasAtualizacao
    global listaNos

    requisicao = request.get_json()

    listasAtualizacao.append(requisicao["listaNos"])

    nosOnline = 0

    for no in listaNos:
        try:

            headers = {'Content-Type': "application/json"}

            dadosJson = {
                "testeConexao": ""
            }

            requisicao = requests.post("{}listar_nos".format(no["ip"]),
                                       data=json.dumps(dadosJson), headers=headers)

            nosOnline += 1

        except:
            pass

    listasAtualizacao = remove_duplicadas(listasAtualizacao)

    print("comparacao",listasAtualizacao,nosOnline)
    if len(listasAtualizacao) == nosOnline:
        listaMaster = listaNos

        for lista in listasAtualizacao:
            if listasAtualizacao.count(lista)>listasAtualizacao.count(listaMaster):
                listaMaster = lista

        listaNos = listaMaster
        print("listaMaster",listaMaster)
        listasAtualizacao = []
        print("listasAtualizacao",listasAtualizacao)

    return json.dumps({"status":1})


def remove_duplicadas(lista):

    novaLista = []

    for elemento in lista:
        if elemento not in novaLista:
            novaLista.append(elemento)

    return novaLista


@aplicacao.route('/',methods=['GET'])
def teste():
    global listaNos
    return json.dumps({"listaNos":listaNos})


if __name__ == '__main__':
    aplicacao.run(port=5000)



