import sys
import os
import csv
import logging
import re

import json
import boto3
import botocore.session
from botocore.session import Session
from botocore.client import Config
import jsonpickle
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, BooleanAttribute
)
from handlers.CustomerHistory import CustomerHistory
from handlers.CustomerHistory import CustomerHistoryDDB
from handlers.Customer import Customer
from handlers.Customer import CustomerDDB
from handlers.MetadataLUT import MetadataLUT
from handlers.MetadataLUT import MetadataLUTDDB
from handlers.CSCLookup import CSCLookup
from handlers.CSCLookup import CSCLookupDDB

logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This lambda is wired to listen to S3 dataload bucket events, 
for which it will then process the originating files' data. 

'''

class ConfigData:
    def __init__(self):
        self.aws_region = ""
        self.aws_profile = ""
        self.s3_bucket_name = ""
        self.s3_file_name = ""
        self.s3_file_version = ""
        self.action = "EDIT"

def read_os(config_data):
    config_data.aws_region = os.environ.get('AWS_REGION', 'ap-southeast-2')
    config_data.aws_profile = os.environ.get('AWS_PROFILE', '')
    config_data.s3_bucket_name = os.environ.get('DATALOAD_BUCKET_NAME', '') 
    config_data.s3_file_name = os.environ.get('DATALOAD_FILE_NAME', '')
    config_data.s3_file_version = os.environ.get('DATALOAD_FILE_VERSION', '')
    config_data.user_table = os.environ.get('DDB_CUSTOMER_TABLE_NAME', '') 

def read_event(config_data, event):
    try:
        logger.info("Reading event data")
        config_data.s3_bucket_name = event['Records'][0]['s3']['bucket']['name']
        config_data.s3_file_name = event['Records'][0]['s3']['object']['key']
        config_data.s3_file_version = event['Records'][0]['s3']['object']['versionId']

    except Exception as error:
        logger.info('Read event error')
        logger.info(str(error))

def process_data(config_data):
    logger.info("Evaluating file {} for possible load actions".format(config_data.s3_file_name))

    if (config_data.s3_file_name == "users.csv"):
        logger.info("File {} configured to load user data in {}.".format(config_data.s3_file_name,config_data.user_table))
        csv_data = read_file(config_data)
        load_users(config_data,csv_data)
    elif (config_data.s3_file_name == "users_delete.csv"):
        logger.info("File {} configured to delete user data in {}.".format(config_data.s3_file_name,config_data.user_table))
        csv_data = read_file(config_data)
        delete_users(config_data,csv_data)
    else:
        logger.info ("File {} has no data load actions associated with it".format(config_data.s3_file_name))

def read_file(config_data):

    bucket = config_data.s3_bucket_name
    key = config_data.s3_file_name
    versionId = config_data.s3_file_version
    logger.info ('Reading S3 Data File: Bucket {}, Key {}, Version {}'.format(bucket,key,versionId))
    try:
        #default session
        session = boto3.session.Session()
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        s3obj = s3.get_object(Bucket=bucket, Key=key, VersionId=versionId)
    except:
        #dev session
        session = boto3.session.Session(profile_name=config_data.aws_profile)
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        s3obj = s3.get_object(Bucket=bucket, Key=key, VersionId=versionId)

    logger.info ('Reading S3 Data File')
    filedata = s3obj['Body'].read()
    return filedata      

def load_users(config_data, data):

    logger.info('Loading User Data from S3 DataLoad bucket')
    data = data.decode("utf-8")
    lines = data.replace("\r\n","\n").split("\n")
    logger.info("{} rows found".format(len(lines)))
    customer = Customer()
    customer.load_customer_record(lines)

def delete_users(config_data, data):

    logger.info('Loading User Data from S3 DataLoad bucket')
    data = data.decode("utf-8")
    lines = data.replace("\r\n","\n").split("\n")
    logger.info("{} rows found".format(len(lines)))
    customer = Customer()
    customer.delete_customer_record(lines)

def lambda_handler(event, context):

    try:
        logger.info("Dataload via S3 event")
        logger.info(event)
        config_data = ConfigData()

        #get config
        read_os(config_data)
        read_event(config_data, event)

        #process the data load
        process_data(config_data)

    except Exception as error:
        logger.info('DataLoad via S3 error')
        logger.info(str(error))
        print (str(error))
