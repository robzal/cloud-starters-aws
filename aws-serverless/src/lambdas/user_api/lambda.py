import sys
import os

from logger import *
from config import *
from User import User
from flask import Flask, redirect, url_for, request, jsonify
import awsgi

logger = Logger().logger
config = Config().config


app = Flask(__name__)

@app.route('/users',methods = ['POST', 'GET'])
def users():
   return 'return all users'

@app.route('/users/<id>',methods = ['POST', 'GET'])
def get_user(id):
   if request.method == 'GET':
       return 'return user {}'.format(id)
   else:
       return 'return user {}'.format(id)

def handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
   app.run(debug = True)