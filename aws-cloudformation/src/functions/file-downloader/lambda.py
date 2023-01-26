import logging
import sys
import io
import argparse
from crhelper import CfnResource
import requests
import boto3
from boto3.session import Session
import botocore.session
from botocore.client import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
helper = CfnResource()


def copy_web_file(source_url, dest_bucket, dest_key):

    logger.info('Downloading Web File {} into S3 {}/{}'.format(source_url,dest_bucket,dest_key))

    #Download a Web File into local bucket
    r = requests.get(source_url, allow_redirects=True)

    session = boto3.session.Session()
    s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))

    s3obj = s3.put_object(Bucket=dest_bucket, Key=dest_key, Body=(r.content))
    return dest_key


def copy_s3_file(source_bucket, source_key, dest_bucket, dest_key):

    logger.info('Downloading S3 Object {}/{} into S3 {}/{}'.format(source_bucket,source_key,dest_bucket,dest_key))

    #Copy a source S3 File into local bucket
    session = boto3.session.Session()
    s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
    response = s3.copy_object(
        Bucket=dest_bucket,
        CopySource="{}/{}".format(source_bucket,source_key),
        Key=dest_key
    )
    return dest_key

@helper.create
@helper.update
def copy_file(event,context):
    source_url = ""
    source_bucket = ""
    source_key = ""
    dest_bucket = ""
    dest_key = ""
    try:
        try:
            source_url = event['ResourceProperties']['SourceURL']
        except:
            source_bucket = event['ResourceProperties']['SourceBucketName']
            source_key = event['ResourceProperties']['SourceBucketKey']
        dest_bucket = event['ResourceProperties']['DestinationBucketName']
        dest_key = event['ResourceProperties']['DestinationBucketKey']
        upload_ref = "not complete"
        if source_url != "":
            # download a file from a web URL
            upload_ref = copy_web_file(source_url, dest_bucket, dest_key)
        else:
            # download a file from an S3 bucket
            upload_ref = copy_s3_file(source_bucket, source_key, dest_bucket, dest_key)
        helper.Data['UploadReference'] = upload_ref
    except Exception as error:
        print (str(error))
        logger.info("error writing {}/{}/{} to {}/{}".format(source_bucket, source_key,source_url,dest_bucket,dest_key))
        logger.info(str(error))
        raise Exception("error writing {}/{}/{} to {}/{}".format(source_bucket, source_key,source_url,dest_bucket,dest_key))

@helper.delete
def no_op(event,context):
    pass

def handler(event, context):
    if "StackId" in event:
        helper(event, context)
    else:
        logger.error("CFN stackid not found so dont go any further")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--source-url', default="")    
    parser.add_argument('--source-bucket', default="")    
    parser.add_argument('--source-key', default="")    
    parser.add_argument('--dest-bucket', default="")    
    parser.add_argument('--dest-key', default="")    
    args = parser.parse_args()

    source_url = args.source_url
    source_bucket = args.source_bucket
    source_key = args.source_key
    dest_bucket = args.dest_bucket
    dest_key = args.dest_key
    upload_ref = "not complete"
    if source_url != "":
        # download a file from a web URL
        upload_ref = copy_web_file(source_url, dest_bucket, dest_key)
    else:
        # download a file from an S3 bucket
        upload_ref = copy_s3_file(source_bucket, source_key, dest_bucket, dest_key)
    print (upload_ref)

