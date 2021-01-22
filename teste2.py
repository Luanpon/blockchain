from flask import Flask,request
import requests
import json

aplicacao = Flask(__name__)

@aplicacao.route('/',methods=['GET'])
def f1():

    try:
        file = open("pasta/teste.txt", "w+")
        file.write("sucesso")
        file.close()

        file = open("pasta/teste.txt", "r")
        m = file.read()
        file.close()
        return m
    except Exception as e:
        return "erro: " + str(e)



if __name__ == '__main__':
    aplicacao.run(host="0.0.0.0",port=5000)






