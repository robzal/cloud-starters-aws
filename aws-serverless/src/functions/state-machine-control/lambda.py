import sys
import os

import json
import boto3
import botocore.session
from botocore.session import Session
from botocore.client import Config

from time import sleep
from datetime import timedelta
import datetime
import pytz

from ProcessConfig import *

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
class KillSwitchException(Exception):
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
        config['max_concurrent_processor_lambdas'] =  os.environ.get('PROCESSOR_LAMBDA_MAX_CONCURRENT', '10')
        config['processor_concurrency_query_minutes'] =  os.environ.get('PROCESSOR_LAMBDA_EXECUTION_QUERY_MINS', '2')
        config['processor_stop'] =  os.environ.get('PROCESSOR_STOP', '0')

    except Exception as error:
        logger.info('Config Read error')
        logger.info(str(error))

def read_db_config(event):
    try:
        logger.info("Reading db config data")

        process_config = ProcessConfig()
        try:
            config['max_concurrent_processor_lambdas'] =  process_config.get_item('ParserQueue', 'max_concurrent_processor_lambdas').value
        except Exception:
            pass
        try:
            config['processor_concurrency_query_minutes'] =  process_config.get_item('ParserQueue', 'processor_concurrency_query_minutes').value
        except Exception:
            pass
        try:
            config['processor_stop'] =  process_config.get_item('ParserQueue', 'processor_stop').value
        except Exception:
            pass

    except Exception as error:
        logger.info('DB Config Read error')
        logger.info(str(error))

def check_kill_switch():

    logger.info(config['processor_stop'])
    if config['processor_stop'] == '0':
        logger.info('No kill switch. Good to keep going')
        return False
    else:
        logger.info('Kill Switch activated. Dont continue')
        return True

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

    spare = 0
    try:
        tz = pytz.timezone('UTC')
        function_name = config['processor_lambda_name'] 
        query_mins = int(config['processor_concurrency_query_minutes'])
        max_concurrent_lambda_count = int(config['max_concurrent_processor_lambdas'])
        stat = [
        {
            "Id": "lambdacount",
            "MetricStat": {
                "Metric": {
                    "Namespace": "AWS/Lambda",
                    "MetricName": "ConcurrentExecutions",
                    "Dimensions": [
                        {
                            "Name": "FunctionName",
                            "Value": function_name
                        }
                    ]
                },
                "Period": 60,
                "Stat": "Maximum",
                "Unit": "Count"
            }
        }
        ]

        response = cw.get_metric_data(
            MetricDataQueries= stat,
            StartTime=datetime.datetime.now(tz) - timedelta(minutes=query_mins),
            EndTime=datetime.datetime.now(tz)
        )

        logger.debug("metric response " + str(response))
        if response["MetricDataResults"][0]["Values"]:
            logger.info ("Recent ConcurrentExecution data available")
            logger.info (response["MetricDataResults"][0]["Values"][0])
            current_concurrent_lambda_count = int(response["MetricDataResults"][0]["Values"][0])

            if max_concurrent_lambda_count - current_concurrent_lambda_count > 0:
                spare = max_concurrent_lambda_count - current_concurrent_lambda_count
                logger.info ("Some SQS Processor capacity available. Able to launch {} lambdas".format(str(spare)))
            else:
                spare = 0
                logger.info ("No SQS Processor capacity available")
        else:
            logger.info ("No ConcurrentExecution data available. Safe to launch")
            spare = max_concurrent_lambda_count

    except Exception as error:
        logger.info('Error determining current lambda capacity.')
        logger.info(str(error))
    logger.info ("SQS Processor capacity available = {}".format(str(spare)))
    return spare

def start_processors(count):
    try:
        for p in range(0, count):
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
        logger.info('Start Processor error')
        logger.info(str(error))
        return False

def handler(event, context):

    logger.info("Starting SQS Process Control Lambda")
    logger.info(event)

    #get os config
    read_env_config(event)

    #get config overrides from DDB table
    read_db_config(event)

    # check he kill switch
    if check_kill_switch():
        raise KillSwitchException()
       
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
