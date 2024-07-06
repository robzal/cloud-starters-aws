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

from ProcessConfig import *
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

        config['sqs_queue_url'] = os.environ.get('SQS_QUEUE_URL', '')
        config['processor_lambda_sqs_batch_size'] = os.environ.get('PROCESSOR_LAMBDA_SQS_BATCH_SIZE', '10')
        config['msg_provided'] = os.environ.get('SQS_DIRECT_LAMBDA_STREAM', 'false')
        config['process_name'] =  os.environ.get('PROCESS_NAME', 'DemoQueue')

    except Exception as error:
        logger.info('Config Read error')
        logger.info(str(error))

def read_db_config(event):
    try:
        logger.info("Reading db config data")

        process_config = ProcessConfig()
        proc_name = config['process_name']
        try:
            config['max_concurrent_processor_lambdas'] =  process_config.get_item(proc_name, 'max_concurrent_processor_lambdas').value
        except Exception:
            pass
        try:
            config['processor_concurrency_query_minutes'] =  process_config.get_item(proc_name, 'processor_concurrency_query_minutes').value
        except Exception:
            pass
        try:
            config['processor_stop'] =  process_config.get_item(proc_name, 'processor_stop').value
        except Exception:
            pass
        try:
            config['processor_lambda_sqs_batch_size'] =  process_config.get_item(proc_name, 'processor_sqs_batch_size').value
        except Exception:
            pass

    except Exception as error:
        logger.info('DB Config Read error')
        logger.info(str(error))

def read_messages(event):

    try:
         
        logger.info('getting (next) messages')
        sqs_messages = []

        if config['msg_provided'] == "false":
            # message(s) not passed n. Go and get it/them
            logger.info('retrieving messages from SQS queue')
            msg_count = int(config['processor_lambda_sqs_batch_size'] )
            response = sqs.receive_message(QueueUrl=config['sqs_queue_url'], MaxNumberOfMessages=msg_count)

            if 'Messages' not in response or len(response['Messages']) == 0:
                logger.info('no SQS messages right now.')
            else:
                # there cn be multiple record in the message
                for message in response['Messages']:
                    logger.info('loading message')
                    sqs_message = {}
                    sqs_message['receipt_handle'] =  message['ReceiptHandle']
                    sqs_message['records'] = json.loads(message['Body'])['Records']
                    sqs_messages.append(sqs_message)
        else:
            # TODO extract messages from lambda event
            logger.info('reading message(s) from lambda event')

            if 'Records' not in event or len(event['Records']) == 0:
                logger.info('no SQS messages right now.')
            else:
                # there cn be multiple record in the message
                for message in event['Records']:
                    logger.info('loading message')
                    sqs_message = {}
                    sqs_message['receipt_handle'] =  message['receiptHandle']
                    sqs_message['records'] = json.loads(message['body'])['Records']
                    sqs_messages.append(sqs_message)

        return sqs_messages

    except Exception as error:
        logger.info('Message Read error')
        logger.info(str(error))
        raise error

def process_messages(sqs_messages):
    try:
         
        if len(sqs_messages) == 0:
            logger.info('no messages to process right now. Exiting')
        else:
            # we can retrieve multiple message if desired
            for sqs_message in sqs_messages:
                logger.info('processing message')
                receipt_handle = sqs_message['receipt_handle']
                records = sqs_message['records']
                
                for rec in records:
                    logger.info('message file key')
                    filename = rec['s3']['object']['key']
                    logger.info(filename)

                    processed_file = ProcessedFile()
                    processed_file.add_update_item(filename)

                sqs.delete_message(QueueUrl=config['sqs_queue_url'], ReceiptHandle=receipt_handle)
                logger.info('message cleared')

    except Exception as error:
        logger.info('Message Process error')
        logger.info(str(error))
        raise error

def handler(event, context):

    logger.info("Starting SQS Process Execution Lambda")
    logger.info(event)

    #get os config
    read_env_config(event)

    #get config overrides from DDB table
    read_db_config(event)

    messages = read_messages(event)
    # grab a message and process it
    process_messages(messages)


if __name__ == '__main__':
    SF_Record = {
    }

    handler(SF_Record,'')
