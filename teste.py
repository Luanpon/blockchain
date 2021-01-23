
from flask import Flask,request
import requests
import json
import os
import errno

aplicacao = Flask(__name__)

#filename = "./teste/teste.txt"
#if not os.path.exists(os.path.dirname(filename)):
    # try:
    #     os.makedirs(os.path.dirname(filename))
    # except OSError as exc:
    #     if exc.errno != errno.EEXIST:
    #         raise

@aplicacao.route('/add',methods=['GET'])
def f1():

    num = 0

    try:
        file = open("db/teste.txt","r")
        num = int(file.read())
        file.close()
    except:
        pass

    try:
        file = open("db/teste.txt", "w+")
        num = num + 1
        file.write(str(num))
        file.close()
    except Exception as e:
        print(e)

    return "ok"

@aplicacao.route('/',methods=['GET'])
def f2():

    try:
        file = open("db/teste.txt", "r")
        num = int(file.read())
        file.close()
        return str(num)
    except:
        return "erro"


if __name__ == '__main__':
    aplicacao.run(host="0.0.0.0",port=5000)






