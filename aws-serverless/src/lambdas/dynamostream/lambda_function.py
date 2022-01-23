import os
import json
import boto3
import re

from logger import *
from config import *

from User import User

logger = Logger().logger
config = Config().config

class DDBStream(object):

    def process(self, records: list) -> list:

        new_records = []
        modified_records = []

        for record in records:
            if record['eventName'] not in ['INSERT', 'MODIFY']:
                logger.info('the following stream event doesnt require processing', extra={'data': record['eventName']})
                continue

            new_record_json = record['dynamodb']['NewImage']
            new_record_key = record['dynamodb']['Keys']
            old_record_json = {}


            if record['eventName'] == 'MODIFY':
                logger.info('dynamodb stream MODIFY for {}'.format(new_record_key))
                old_record_json = record['dynamodb']['OldImage']
                modified_records.append(new_record_json)
            else:
                logger.info('dynamodb stream INSERT for {}'.format(new_record_key))
                new_records.append(new_record_json)

        return new_records, modified_records


def lambda_handler(event, context):
    logger.info('stream event data')
    logger.info(event)
    stream = DDBStream()
    new_records, modified_records = stream.process(event['Records'])

    if new_records:
        logger.info('found {} records to be processed'.format(len(new_records)))

    else:
        logger.info('no records require to be processed')
