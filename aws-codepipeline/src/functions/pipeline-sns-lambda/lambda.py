import sys
import io
import os
import logging
import json
import boto3
import botocore.session
from botocore.client import Config
from boto3.session import Session


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

    logger.info('CodePipeline Notification Lambda event')
    logger.info(event)
