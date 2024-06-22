import sys
import os

import json
import boto3
import botocore.session
from botocore.session import Session
from botocore.client import Config
from datetime import datetime

from time import sleep
from logger import *
from config import *

from ProcessedFile import *

logger = Logger().logger
config = Config().config

sqs = boto3.client('sqs')
ddb = boto3.client('dynamodb')


'''
This lambda, normally running in a step function processes SQS queue messages there are messages in the queue. 

'''

#creating separately named exceptions for easier handling in SFNs. Nothing special about them though
class ProcessException(Exception):
    pass

def read_env_config(event):
    try:
        logger.info("Reading config data")

        config['environment'] = os.environ.get('ENVIRONMENT', '')
        config['app_code'] = os.environ.get('APP_CODE', '')
        config['sqs_queue_url'] = os.environ.get('SQS_QUEUE_URL', '')
        config['sqs_queue_arn'] = os.environ.get('SQS_QUEUE_ARN', '')
        config['dynamo_files_table_arn'] = os.environ.get('DYNAMODB_FILES_TABLE_ARN', '')
        config['processor_lambda_timeout_secs'] = os.environ.get('PROCESSOR_LAMBDA_TIMEOUT_SECS', '300')
        config['processor_lambda_sqs_batch_size'] = os.environ.get('PROCESSOR_LAMBDA_SQS_BATCH_SIZE', '10')

    except Exception as error:
        logger.info('Config Read error')
        logger.info(str(error))

def process_message():
    try:
        logger.info('retrieving (next) message')
        msg_count = int(config['processor_lambda_sqs_batch_size'] )
        response = sqs.receive_message(QueueUrl=config['sqs_queue_url'], MaxNumberOfMessages=msg_count)

        if 'Messages' not in response or len(response['Messages']) == 0:
            logger.info('no more messages right now. exiting')
        else:
            # we can retrieve multiple message if desired
            for message in response['Messages']:
                logger.info('processing message')
                receipt_handle = message['ReceiptHandle']
                records = json.loads(message['Body'])['Records']
                # TODO - write data to DDB
                logger.info('message file key')
                filename = records[0]['s3']['object']['key']
                logger.info(filename)

                processed_file = ProcessedFile()
                processed_file.add_update_item(filename)

                sqs.delete_message(QueueUrl=config['sqs_queue_url'], ReceiptHandle=receipt_handle)
                logger.info('message cleared')

    except Exception as error:
        logger.info('Message Process error')
        logger.info(str(error))
        return False

def handler(event, context):

    logger.info("Starting SQS Process Execution Lambda")
    logger.info(event)

    #get os config
    read_env_config(event)

    # grab a message and process it
    process_message()


if __name__ == '__main__':
    SF_Record = {
    }
    handler(SF_Record,'')
