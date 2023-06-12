import sys
import io
import os
import logging
import re
import json
import boto3
import botocore.session
from botocore.client import Config
from boto3.session import Session
import jsonpickle


logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This lambda is wired to listen to codecommit events.
It reads a pipeline rule file in S3 - os.environ.get('EVENT_BUCKET_NAME') - os.environ.get('EVENT_BUCKET_RULES_KEY'
to see if any CodePipeline pipelines should be run in response to this branch/commit.
If so, this lambda creates the necessary codepipeline event file and puts into the S3 event folder, also in os.environ.get('EVENT_BUCKET_NAME')
with the necessary commit and execution context details in it, from where it will be detected by the pipeline source listener
'''

class ConfigData:
    def __init__(self):
        self.aws_region = ""
        self.working_dir = "" 
        self.event_bucket_name = "" 
        self.event_bucket_rules_key = ""
        self.rules = ""
        self.next_target = ""

class EventData:
    def __init__(self):
        self.app_code = ""        
        self.pipeline_name = ""
        self.repository_name = ""        
        self.branch_name = ""
        self.commit_id = ""        
        self.stack_name = ""        
        self.environment = ""        
        self.env_file = ""   
        self.params = ""     

def read_os(config_data, event_data):
    config_data.aws_region = os.environ.get('AWSREGION', 'ap-southeast-2')
    config_data.working_dir = os.environ.get('LAMBDA_WORKING_DIR', '/tmp')
    config_data.event_bucket_name = os.environ.get('EVENT_BUCKET_NAME','')
    config_data.event_bucket_rules_key = os.environ.get('EVENT_BUCKET_RULES_KEY', '')
    event_data.app_code = os.environ.get('APP_CODE', '') 
    event_data.repository_name = os.environ.get('REPOSITORY_NAME', '') 

def read_event(config_data, event_data, event):
    try:
        logger.info("Reading event data")
        event_data.branch_name = event['detail']['referenceFullName'].replace("refs/heads/","")
        logger.info("Event branch name")
        logger.info(event_data.branch_name)
        event_data.commit_id = event['detail']['commitId']
        logger.info("Event commit id")
        logger.info(event_data.commit_id)
        arn = event['resources'][0]
        patt = '(.*):(.*):(.*):(.*):(.*):(.*)'
        m = re.search(patt, arn, re.IGNORECASE)
        event_data.repository_name =  m.group(6)
        logger.info("Event repo")
        logger.info(event_data.repository_name)
    except Exception as error:
        logger.info('Read event error')
        logger.info(str(error))

def read_rules(config_data, event_data):
    logger.info("Reading rules files")
    bucket_name = config_data.event_bucket_name
    key = config_data.event_bucket_rules_key
    #S3 service with creds
    #try using current session
    session = boto3.session.Session()
    s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
    s3obj = s3.get_object(Bucket=bucket_name, Key=key)
        
    rules = json.loads(s3obj['Body'].read())
    logger.info('Rules data to check:')
    logger.info(rules['rules'])
    config_data.rules = rules['rules']

def process_rules(config_data, event_data):
    #check rules for this execution context, and see if another needs to be queued after it.
    #find this branch's rule set
    logger.info('Processing rules')
    config_data.next_target = False

    rules = [rule for rule in config_data.rules if re.search(rule['branch_name'], event_data.branch_name.replace("refs/heads/",""), re.IGNORECASE) ]
    if len(rules) > 0: 
        logger.info('Rule found')
        logger.info(rules[0])
        #for this branch,take the first target
        for target in rules[0]['targets']:
            logger.info('Target')
            logger.info(rules[0]['targets'][0])
            config_data.next_target = target
            break    

def queue_next_event(config_data, event_data):
    if config_data.next_target:
        logger.info('Creating next pipeline event file')

        # TODO make sure empty vals dont overwrite
        event_data.app_code = config_data.next_target['app_code']
        event_data.pipeline_name = config_data.next_target['pipeline_name']
        event_data.repository_name = config_data.next_target['repository_name'] 
        event_data.branch_name = config_data.next_target['branch_name']
        logger.info('Commit ID')
        logger.info(event_data.commit_id)
        #event_data.commit_id = config_data.next_target['commit_id']
        event_data.stack_name = config_data.next_target['stack_name'].replace('$BRANCH_NAME',event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        event_data.environment = config_data.next_target['environment'].replace('$BRANCH_NAME',event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        event_data.env_file = config_data.next_target['env_file'].replace('$BRANCH_NAME',event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        event_data.params = ""

        bucket_name = "{}".format(config_data.event_bucket_name)
        key = "events/{}/{}".format(event_data.app_code, event_data.pipeline_name)

        #S3 service with creds
        #try using current session
        session = boto3.session.Session()
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        j = jsonpickle.encode(event_data, unpicklable=False).encode("utf-8")
        buf = io.BytesIO(j)
        s3obj = s3.put_object(Bucket=bucket_name, Key=key, Body=(buf))
    else:
        logger.info('No further Pipeline Stages to run')

def handler(event, context):

    try:
        logger.info("CodeCommit event")
        logger.info(event)
        config_data = ConfigData()
        event_data = EventData()
        #get context
        read_os(config_data, event_data)
        read_event(config_data, event_data, event)
        read_rules(config_data, event_data)

        #process the pipeline rules
        process_rules(config_data, event_data)
        queue_next_event(config_data, event_data)

    except Exception as error:
        logger.info('CodeCommit event error')
        logger.info(str(error))

