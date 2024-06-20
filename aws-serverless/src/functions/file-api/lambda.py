import sys
import os

from logger import *
from config import *
from flask import Flask, redirect, url_for, request, jsonify
import awsgi
# from User import User

logger = Logger().logger
config = Config().config


app = Flask(__name__)

@app.route('/files',methods = ['POST', 'GET'])
def users():
   return 'return all files'

@app.route('/files/<id>',methods = ['POST', 'GET'])
def get_user(id):
   if request.method == 'GET':
       return 'return file {}'.format(id)
   else:
       return 'return file {}'.format(id)

def handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
   app.run(debug = True)