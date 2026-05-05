import os
from flask import Flask
from flask_cors import CORS
import fdb

def get_db_connection():
    return fdb.connect(
        database=r'C:\Users\Aluno\Desktop\BANCO\BANCO.FDB',
        user='SYSDBA',
        password='sysdba'
    )

app = Flask(__name__)
CORS(app, supports_credentials=True,
     origins=["", #front
              "http://10.92.3.164:5000" #back
              ""]) #pc


app.config['SECRET_KEY'] = ''

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


try:
    con = fdb.connect(
        host='localhost',
        database=r'C:\Users\Aluno\Desktop\BANCO\BANCO.FDB',
        user='SYSDBA',
        password='sysdba',
        charset='UTF8'
    )
    print("Conexão com Firebird estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar no banco: {e}")
    con = None


from view import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)