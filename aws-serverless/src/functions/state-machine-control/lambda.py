import sys
import os

import json
import boto3
import botocore.session
from botocore.session import Session
from botocore.client import Config

from time import sleep
from logger import *
from config import *

logger = Logger().logger
config = Config().config

lambd = boto3.client('lambda')
sfn = boto3.client('stepfunctions')
sqs = boto3.client('sqs')
cw = boto3.client('cloudwatch')


'''
This lambda, normally running in a step function controls instantiating SQS message processing lambdas if there are messages in the queue. 

'''

#creating separately named exceptions for easier handling in SFNs. Nothing special about them though
class AlreadyRunningException(Exception):
    pass
class ProcessException(Exception):
    pass
class CapacityException(Exception):
    pass
class StillProcessingException(Exception):
    pass

def read_env_config(event):
    try:
        logger.info("Reading config data")

        config['environment'] = os.environ.get('ENVIRONMENT', '')
        config['app_code'] = os.environ.get('APP_CODE', '')
        config['sqs_queue_url'] = os.environ.get('SQS_QUEUE_URL', '')
        config['sqs_queue_arn'] = os.environ.get('SQS_QUEUE_ARN', '')
        config['step_function_arn'] = os.environ.get('STEP_FUNCTION_ARN', '')
        config['dynamo_control_table_arn'] = os.environ.get('DYNAMODB_CONTROL_TABLE_ARN', '')
        config['processor_lambda_name'] = os.environ.get('PROCESSOR_LAMBDA_NAME', '')
        config['processor_lambda_arn'] = os.environ.get('PROCESSOR_LAMBDA_NAME', '')

        config['max_concurrent_processor_lambdas'] = "5"

    except Exception as error:
        logger.info('Config Read error')
        logger.info(str(error))

def read_processor_config():
    pass

def check_other_sfn_running():
    logger.info(config)
    response = sfn.list_executions(
        stateMachineArn=config['step_function_arn'],
        statusFilter='RUNNING',
        maxResults=1
    )
    if 'executions' not in response or len(response['executions']) in [0,1]:
        logger.info('No other current Executions. Good to keep going')
        return False
    else:
        logger.info('Other current Executions in progress. Dont continue')
        return True

def check_messages_exist():
    response = sqs.get_queue_attributes(
        QueueUrl=config['sqs_queue_url'],
        AttributeNames=[
            'ApproximateNumberOfMessages'
        ]
    )
    logger.info('Queue Attributes')
    logger.info(response)
    
    if 'Attributes' not in response or response['Attributes']['ApproximateNumberOfMessages'] == '0':
        logger.info('No current messages. Dont continue' )
        return False
    else:
        logger.info('Messages in the queue. Good to keep going')
        return True

def spare_lambda_capacity():
    # TODO code to get current executions and subtract from max concurrency
    return int(config['max_concurrent_processor_lambdas'])

        # metric_stats = {
        #     "Namespace": "AWS/Lambda",
        #     "StartTime": (current_time - datetime.timedelta(seconds=10)).isoformat(),
        #     "EndTime": current_time.isoformat(),
        #     "FunctionName": "serverless-demo-admin-Process-Queue-Control-Lambda",
        #     "Period": 60,
        #      {
        #           "MetricName": "ConcurrentExecutions ",
        #           "Statistics": ["Max"],
        #           "Unit": "Count"
        #       }
        # }
        # response = cw.get_metric_statistics(**metric_stats)
        # if response["Datapoints"]:
        #     return response["Datapoints"][0][stats["Statistics"][0]]

def start_processors(count):
    try:
        for p in range(1, count):
            response = lambd.invoke(
                FunctionName=config['processor_lambda_arn'],
                InvocationType='Event',
                Payload='{}',
            )

            print(response)

            # Expected Output:
            # {
            #     'Payload': '',
            #     'StatusCode': 202,
            #     'ResponseMetadata': {
            #         '...': '...',
            #     },
            # }
            sleep(0.25)
        return True

    except Exception as error:
        logger.info('Config Read error')
        logger.info(str(error))
        return False

def handler(event, context):

    logger.info("Starting SQS Process Control Lambda")
    logger.info(event)

    #get os config
    read_env_config(event)

    #get processor config
    read_processor_config()

    # we only want one step function actually controlling processing
    if check_other_sfn_running():
        raise AlreadyRunningException()
       
    # read queue length for messages to process
    if check_messages_exist():
            
        # check lambda capacity
        spare = spare_lambda_capacity()
        if spare > 0:
            logger.info('start processors')
            # run needed lambdas
            if start_processors(spare):
                raise StillProcessingException()
            else:
                raise ProcessException() 
        else:
            raise CapacityException()
        
    else:
        return


if __name__ == '__main__':
    SF_Record = {
    }
    handler(SF_Record,'')
