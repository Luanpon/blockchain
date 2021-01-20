
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

            requisicao = requests.post("{}obter_cadeia".format(no["ip"]),
                                       data=json.dumps(dadosJson), headers=headers)

            nosOnline += 1

        except:
            pass

    if len(listasAtualizacao) == nosOnline:
        listaMaster = listasAtualizacao[0]

        for lista in listasAtualizacao:
            if listasAtualizacao.count(lista)>listasAtualizacao.count(listaMaster):
                listaMaster = lista

        listaNos = listaMaster
        print(listaMaster)
        listasAtualizacao = []

    return json.dumps({"status":1})


if __name__ == '__main__':
    aplicacao.run(port=5000)



