import io
import os
import logging
import re
import json
import botocore.session
import boto3
from botocore.client import Config
from boto3.session import Session
import jsonpickle


logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This lambda typically runs at the end of a CodePipeline execution, one which was initiated by the new pipeline rules mechanism.
This lambda reads a pipeline rule file in S3 - os.environ.get('EVENT_BUCKET_NAME') - os.environ.get('EVENT_BUCKET_RULES_KEY'
to see if any CodePipeline pipelines should be run after this pipeline.
If so, this lambda creates the necessary next event file and puts into the appropriate S3 event folder, also in os.environ.get('EVENT_BUCKET_NAME')
with the necessary next git branch and execution context details in it, from where it will be detected by the pipeline
'''

class ConfigData:
    def __init__(self):
        self.aws_region = ""
        self.working_dir = "" 
        self.event_bucket_name = "" 
        self.event_bucket_rules_key = ""
        self.rules = ""
        self.next_target = ""
        self.send_pipeline_result = True
        # This execution context
        # self.app_code = ""        
        # self.pipeline_name = ""
        # self.repository_name = ""        
        # self.branch_name = ""
        # self.commit_id = ""        
        # self.stack_name = ""        
        # self.environment = ""        
        # self.env_file = ""   
        # self.params = ""     

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

def read_os(config_data,event_data):
    config_data.aws_region = os.environ.get('AWSREGION', 'ap-southeast-2')
    config_data.working_dir = os.environ.get('LAMBDA_WORKING_DIR', '/tmp')
    config_data.event_bucket_name = os.environ.get('EVENT_BUCKET_NAME', '')
    config_data.event_bucket_rules_key = os.environ.get('EVENT_BUCKET_RULES_KEY', '')
    event_data.app_code = os.environ.get('APP_CODE', '') 
    event_data.repository_name = os.environ.get('REPOSITORY_NAME', '') 

    # some env vars for local debugging
    #event_data.pipeline_name = os.environ.get('PIPELINE_NAME', 'master')
    #event_data.branch_name = os.environ.get('BRANCH_NAME', 'master')
    #event_data.commit_id = os.environ.get('COMMIT_ID', '')
    #event_data.stack_name = os.environ.get('STACK_NAME', '') 
    #event_data.environment = os.environ.get('ENVIRONMENT', '') 
    #event_data.env_file = os.environ.get('ENV_FILE', '') 
    #event_data.params = os.environ.get('EVENT_PARAMS', '') 
    # try:
    #     send_pipeline_result = ast.literal_eval(os.environ.get('SEND_PIPELINE_RESULT', 'True'))
    #     logger.info("user vars send result value: " + send_pipeline_result)
    # except:
    #     pass

def read_event(config_data, event_data, event):
    try:
        logger.info("Reading event data")
        config_data.jobid =  event['CodePipeline.job']['id']
        config_data.job_data = event['CodePipeline.job']['data']

        # this data is all needed, so if it aint passed in, throw an exception
        logger.info('Reading context from user data')
        js = config_data.job_data['actionConfiguration']['configuration']['UserParameters']
        logger.info(js)
        userdata = json.loads(js)
        logger.info("Getting Context")
        event_data.app_code = userdata['APP_CODE']
        event_data.pipeline_name = userdata['PIPELINE_NAME']
        event_data.repository_name = userdata['REPOSITORY_NAME']
        event_data.branch_name = userdata['BRANCH_NAME']
        event_data.commit_id = userdata['COMMIT_ID']
        event_data.stack_name = userdata['STACK_NAME']
        event_data.environment = userdata['ENVIRONMENT']
        event_data.env_file = userdata['ENV_FILE']
        logger.info("Getting Params")
        event_data.params = userdata['PARAMS']
        logger.info(event_data.params)
    except Exception as error:
        logger.info('Reading user data failed')
        logger.info(str(error))
        raise error


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
        #for this branch,see if this execution is part of a rule pipeline and check if there are any still to run after this one
        for i, target in enumerate(rules[0]['targets']):
            if target['pipeline_name'] == event_data.pipeline_name and target['stack_name'] == event_data.stack_name and i < (len(rules[0]['targets']) - 1):
                logger.info('Rule found')
                logger.info(rules[0]['targets'][i+1])
                config_data.next_target = rules[0]['targets'][i+1]
                break

def queue_next_event(config_data, this_event_data, next_event_data):
    if config_data.next_target:
        logger.info('Creating next pipeline trigger file')

        # TODO make sure empty vals dont overwrite those set earlier
        next_event_data.app_code = config_data.next_target['app_code']
        next_event_data.pipeline_name = config_data.next_target['pipeline_name']
        if this_event_data.repository_name != config_data.next_target['repository_name'] or this_event_data.branch_name != config_data.next_target['branch_name']:
            next_event_data.commit_id = ""
        else:
            next_event_data.commit_id = this_event_data.commit_id
        next_event_data.repository_name = config_data.next_target['repository_name'] 
        next_event_data.branch_name = config_data.next_target['branch_name']
        next_event_data.stack_name = config_data.next_target['stack_name'].replace('$BRANCH_NAME',next_event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        next_event_data.environment = config_data.next_target['environment'].replace('$BRANCH_NAME',next_event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        next_event_data.env_file = config_data.next_target['env_file'].replace('$BRANCH_NAME',next_event_data.branch_name.replace("refs/heads/","").replace("/","-"))
        next_event_data.params = this_event_data.params

        bucket_name = "{}".format(config_data.event_bucket_name)
        key = "events/{}/{}".format(next_event_data.app_code, next_event_data.pipeline_name)

        #S3 service with creds
        #try using current session
        session = boto3.session.Session()
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        j = jsonpickle.encode(next_event_data, unpicklable=False).encode("utf-8")
        buf = io.BytesIO(j)
        s3obj = s3.put_object(Bucket=bucket_name, Key=key, Body=(buf))
    else:
        logger.info('No further Pipeline Stages to run')

def send_codepipeline_result(config_data, result, details=None):
    
    code_pipeline = boto3.client('codepipeline')
    if result:
        logger.info('Lambda job succeeded' )
        logger.info('jobID ' + config_data.jobid)
        if config_data.send_pipeline_result:
            code_pipeline.put_job_success_result(jobId=config_data.jobid, outputVariables=details)   
    else:
        logger.info('Lambda job failed')
        logger.info('jobID ' + config_data.jobid)
        logger.info(details)
        if config_data.send_pipeline_result:
            code_pipeline.put_job_failure_result(jobId=config_data.jobid, failureDetails={'type': 'JobFailed', 'message': details})    

def event_to_json(event_data):
        return {'app_code': event_data.app_code, \
        'pipeline_name': event_data.pipeline_name, \
        'repository_name': event_data.repository_name, \
        'branch_name': event_data.branch_name, \
        'commit_id': event_data.commit_id, \
        'stack_name': event_data.stack_name, \
        'environment': event_data.environment, \
        'env_file': event_data.env_file, \
        'params': event_data.params}

def handler(event, context):

    try:
        logger.info('Post pipeline processing event')
        config_data = ConfigData()
        this_event_data = EventData()
        next_event_data = EventData()
        #get config
        read_os(config_data,this_event_data)
        read_event(config_data, this_event_data, event)
        read_rules(config_data, this_event_data)

        #process the pipeline rules
        process_rules(config_data, this_event_data)
        queue_next_event(config_data, this_event_data, next_event_data)
        send_codepipeline_result(config_data, True, event_to_json(next_event_data))
    except Exception as error:
        logger.info('Post pipeline processing error')
        logger.info(str(error))
        send_codepipeline_result(config_data, False, str(error))

