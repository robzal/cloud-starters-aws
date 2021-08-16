import sys
import boto3
import io
import os
import shutil
import mimetypes
import logging
import zipfile
import re
import json
import botocore.session
import ast
from botocore.client import Config
from boto3.session import Session


logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
This lambda reads a pipeline event file which contains
CodeCommit Repo, Branch and Commit details
as well as the Pipeline Execution Context variables.

It is typically used to return a buildspec.yaml file as an output artefact
and exports the pipeline context variables as CodePipeline uservariables

This lambda uses to checks out the appropriate Git CommitID and retrieves and outputs the requested
files (os.environ.get('FETCH_FILE_LIST') back into the pipeline for the next stage.

"""

class ConfigData:
    def __init__(self):
        self.aws_region = ""
        self.working_dir = "" 
        self.event_bucket_name = "" 
        self.event_bucket_rules_key = ""
        self.fetch_file_list = ""
        self.rules = ""
        self.next_target = ""
        # self.app_code = ""        
        # self.pipeline_name = ""
        # self.repository_name = ""
        # self.branch_name = ""
        # self.commit_id = ""        
        self.jobid = ""
        self.job_data = ""        
        self.input_bucket_name = ""
        self.input_bucket_key = ""
        self.output_bucket_name = ""
        self.output_bucket_key = ""
        self.artifact_creds = ""
        self.send_pipeline_result = True

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
    config_data.fetch_file_list = os.environ.get('FETCH_FILE_LIST', '')
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
    #config_data.input_bucket_name = os.environ.get('EVENT_BUCKET_NAME', '')
    #config_data.input_bucket_key = os.environ.get('EVENT_BUCKET_NAME', config_data.repository_name)
    #config_data.output_bucket_name = os.environ.get('OUTPUT_BUCKET_NAME', '')
    #config_data.output_bucket_key = os.environ.get('OUTPUT_BUCKET_KEY', (config_data.repository_name or 'output') + ".zip")

def read_event(config_data, event_data, event):
    try:
        logger.info("Reading event data")
        config_data.jobid =  event['CodePipeline.job']['id']
        config_data.job_data = event['CodePipeline.job']['data']
        config_data.input_bucket_name = config_data.job_data['inputArtifacts'][0]['location']['s3Location']['bucketName']
        config_data.input_bucket_key = config_data.job_data['inputArtifacts'][0]['location']['s3Location']['objectKey']
        config_data.output_bucket_name = config_data.job_data['outputArtifacts'][0]['location']['s3Location']['bucketName']
        config_data.output_bucket_key = config_data.job_data['outputArtifacts'][0]['location']['s3Location']['objectKey']
        config_data.artifact_creds = config_data.job_data['artifactCredentials']
        try:
            logger.info('Reading user data')
            js = config_data.job_data['actionConfiguration']['configuration']['UserParameters']
            logger.info(js)
            userdata = json.loads(js)
            try:
                logger.info('Reading user data - pipeline_name')
                event_data.pipeline_name = userdata['PIPELINE_NAME']
            except:
                pass
            try:
                logger.info('Reading user data - repository_name')
                event_data.repository_name = userdata['REPOSITORY_NAME']
            except:
                pass
            try:
                logger.info('Reading user data - app_code')
                event_data.app_code = userdata['APP_CODE']
            except:
                pass
            try:
                logger.info('Reading user data - send_pipeline_result')
                config_data.send_pipeline_result = ast.literal_eval(userdata['SEND_PIPELINE_RESULT'])
            except:
                pass
            try:
                logger.info('Reading user data - fetch_file_list')
                config_data.fetch_file_list = userdata['FETCH_FILE_LIST']
            except:
                pass
        except:
            pass
    except Exception as error:
        logger.info('Reading user data failed')
        logger.info(str(error))
        raise error
    
def read_source_artifact(config_data, event_data):
    logger.info("Reading source artifact")
    bucket_name = config_data.input_bucket_name
    key = config_data.input_bucket_key
    #S3 service with creds
    try:
        #try using artefact creds
        key_id = config_data.artifact_creds['accessKeyId']
        key_secret = config_data.artifact_creds['secretAccessKey']
        session_token = config_data.artifact_creds['sessionToken']
        session = Session(aws_access_key_id=key_id,
            aws_secret_access_key=key_secret,
            aws_session_token=session_token)
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        s3obj = s3.get_object(Bucket=bucket_name, Key=key)
    except:
        #try using current session
        session = boto3.session.Session()
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        s3obj = s3.get_object(Bucket=bucket_name, Key=key)
        
    ref = json.loads(s3obj['Body'].read())
    logger.info('Repo reference to use:')
    logger.info(ref)

    # TODO check empty values dont overwrite uservar values
    logger.info("Getting Context")
    event_data.app_code = ref['app_code']
    event_data.pipeline_name = ref['pipeline_name']
    event_data.repository_name = ref['repository_name'] 
    event_data.branch_name = ref['branch_name']
    event_data.commit_id = ref['commit_id']
    event_data.stack_name = ref['stack_name']
    event_data.environment = ref['environment'] 
    event_data.env_file = ref['env_file'] 
    logger.info("Getting Params")
    event_data.params = ""

def get_source_commit(config_data,event_data):
    logger.info('Fetching data from git repo')
    #CodeCommit Service
    codecommit = boto3.client('codecommit', region_name=config_data.aws_region)

    #get blobs in repo with commit ref
    repo_ref = event_data.commit_id or event_data.branch_name
    logger.info('using args')
    args = {'repositoryName': event_data.repository_name, 'afterCommitSpecifier': repo_ref}
    logger.info(str(args))
    logger.info('fetch file list: {} '.format(config_data.fetch_file_list))
    logger.info('Fetching ....')
    response = codecommit.get_differences(**args)
    blob_list = [difference['afterBlob'] for difference in response['differences']]
    while 'NextToken' in response:
        logger.info('Still Fetching ....')
        args['NextToken'] = response['NextToken']
        response = codecommit.get_differences(**args)
        blob_list += [difference['afterBlob'] for difference in response['differences']]

    logger.info('Got the blobs, Now storing locally')
    #clear dir, fetch files and write them to disk    
    os.chdir(config_data.working_dir) 
    shutil.rmtree(config_data.working_dir, ignore_errors=True)

    buf = io.BytesIO()
    for blob in blob_list:
        path = blob['path']
        if (path in config_data.fetch_file_list.split(',') or config_data.fetch_file_list == ''):
            try:
                content = (codecommit.get_blob(repositoryName=event_data.repository_name, blobId=blob['blobId']))['content']

                try:
                    os.makedirs(os.path.dirname(config_data.working_dir + "/" + path), exist_ok=True)
                except:
                    pass
                with open(path, "wb") as f:
                    f.write(content)
            except Exception as error:
                logger.info("error writing {}".format(path))
                logger.info(str(error))

def zip_source_commit(config_data,event_data):
    logger.info('Zipping data from git repo')
    config_data.zipfilename = event_data.repository_name + '.zip'
    zf = zipfile.ZipFile(config_data.zipfilename, "w")
    for dirname, subdirs, files in os.walk(config_data.working_dir):
        shortdirname = re.sub('^%s' % config_data.working_dir, "", dirname)
        #logger.info(shortdirname)
        if config_data.zipfilename in files:
            files.remove(config_data.zipfilename)        
        for filename in files:
            #logger.info(filename)
            zf.write(os.path.join(dirname, filename), shortdirname + "/" + filename)
    zf.close()

def write_dest_artifact(config_data,event_data):
    
    logger.info('Uploading data from git repo')
    bucket_name = config_data.output_bucket_name
    key = config_data.output_bucket_key
    #S3 service with creds
    try:
        #try using artefact creds
        logger.info('Trying pipeline event artifact credentials')
        key_id = config_data.artifact_creds['accessKeyId']
        key_secret = config_data.artifact_creds['secretAccessKey']
        session_token = config_data.artifact_creds['sessionToken']
        session = Session(aws_access_key_id=key_id,
            aws_secret_access_key=key_secret,
            aws_session_token=session_token)
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        with open(config_data.zipfilename,'rb') as f:
            buf=io.BytesIO(f.read())
        s3obj = s3.put_object(Bucket=bucket_name, Key=key, Body=(buf))

    except:
        #try using current session
        logger.info('Well that didnt work. Trying current session credentials instead')
        session = boto3.session.Session()
        s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        with open(config_data.zipfilename,'rb') as f:
            buf=io.BytesIO(f.read())
        s3obj = s3.put_object(Bucket=bucket_name, Key=key, Body=(buf))
    
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

def lambda_handler(event, context):

    try:
        config_data = ConfigData()
        event_data = EventData()
        #get config
        read_os(config_data, event_data)
        read_event(config_data, event_data, event)
        
        #get got repo reference from trigger file
        read_source_artifact(config_data, event_data)
        #write to local OS working directory
        get_source_commit(config_data,event_data)
        #zips what is in working directory
        zip_source_commit(config_data,event_data)
        #upload zip file to output artifact directory
        write_dest_artifact(config_data,event_data)
    
        outputVars = event_to_json(event_data)
        logger.info("outputVars")
        logger.info(outputVars)
        send_codepipeline_result(config_data, True, outputVars)

    except Exception as error:
        send_codepipeline_result(config_data, False, str(error))
