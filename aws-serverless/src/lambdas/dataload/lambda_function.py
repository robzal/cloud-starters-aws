import sys
import os
import csv
import re

import json
import boto3
import botocore.session
from botocore.session import Session
from botocore.client import Config

from logger import *
from config import *

from User import User

logger = Logger().logger
config = Config().config


'''
This lambda is wired to listen to S3 dataload bucket events, 
for which it will then process the originating files' data. 

'''

def read_event(event):
    try:
        logger.info("Reading event data")
        config['s3_bucket_name'] = ""
        config['s3_file_name'] = ""
        config['s3_file_version'] = ""

        config['s3_bucket_name'] = event['Records'][0]['s3']['bucket']['name']
        config['s3_file_name'] = event['Records'][0]['s3']['object']['key']
        config['s3_file_version'] = event['Records'][0]['s3']['object']['versionId']

        config['environment'] = os.environ.get('ENVIRONMENT', '')
        config['app_code'] = os.environ.get('APP_CODE', '')
        config['user_table'] = os.environ.get('USER_TABLE', '')
        config['report_table'] = os.environ.get('REPORT_TABLE', '')
        config['timezone'] = os.environ.get('TZ', '')
        config['s3_data_load_bucket'] = os.environ.get('DATA_LOAD_BUCKET', '')

    except Exception as error:
        logger.info('Read event error')
        logger.info(str(error))

def process_data():

    if config['s3_file_name'] == "":
        logger.info("Skipping data Load. No file name detected")
    else:
        if (config['s3_file_name'] == "users.csv"):
            logger.info("File {} configured to load user data in {}.".format(config['s3_file_name'],config['user_table']))
            u = User()
            u.loads3csv(config['s3_data_load_bucket'], config['s3_file_name'])
            u.save(config['user_table'], u.items)
        elif (config['s3_file_name'] == "users_delete.csv"):
            logger.info("File {} configured to delete user data in {}.".format(config['s3_file_name'],config['user_table']))
            u = User()
            u.loads3csv(config['s3_data_load_bucket'], config['s3_file_name'])
            u.delete(config['user_table'], u.items)
        else:
            logger.info ("File {} has no data load actions associated with it".format(config['s3_file_name']))

def lambda_handler(event, context):

    try:
        logger.info("Dataload via S3 event")
        logger.info(event)

        #get config
        read_event(event)

        #process the data load
        process_data()

    except Exception as error:
        logger.info('DataLoad via S3 error')
        logger.info(str(error))

if __name__ == '__main__':
    SF_Record = json.dumps({'request': 'event'})
    lambda_handler(SF_Record,'')
