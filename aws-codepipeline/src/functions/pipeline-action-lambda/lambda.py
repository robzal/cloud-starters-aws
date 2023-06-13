import sys
import boto3
import io
import os
import mimetypes
import logging
import re
import json
import botocore.session
import ast
from botocore.client import Config
from boto3.session import Session
import jsonpickle


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_codepipeline_result(jobid, result):
    
    code_pipeline = boto3.client('codepipeline')
    if result:
        logger.info('Lambda Pipeline job succeeded' )
        logger.info('jobID ' + jobid)
        code_pipeline.put_job_success_result(jobId=jobid)   
    else:
        logger.info('Lambda job failed')
        logger.info('jobID ' + jobid)
        detail = {
            'type': 'JobFailed',
            'message': 'Lambda job failed'
        }
        code_pipeline.put_job_failure_result(jobId=jobid,failureDetails=detail)    

def handler(event, context):

    logger.info('CodePipeline Action Lambda event')
    logger.info(event)
    jobid = 'unknown'
    try:
        logger.info('CodePipeline Action Lambda Job ID')
        jobid =  event['CodePipeline.job']['id']
        logger.info('jobID ' + jobid)

        # Add custom action logic here returning True or False

        send_codepipeline_result(jobid, True)
    except Exception as error:
        logger.info('CodePipeline Action Lambda')
        logger.info(str(error))
        logger.info('jobID ' + jobid)    
        send_codepipeline_result(jobid, False)
