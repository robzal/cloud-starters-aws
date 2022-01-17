import os
import json
import boto3
import botocore
import csv
from botocore.session import Session
from botocore.client import Config
import logging

logger = logging.getLogger()

class DDBClass(object):

    def __init__(self):
        self.session = boto3.session.Session()
        self.ddb_client = self.session.client('dynamodb')
        self.fields=[]
        self.keys=[]
        self.items=[]
        self.save_batch_size=25
    
    def key_range_expression(self, key, range, indexname=None):
        pass

    def key_expression(self, keys):
        pass

    def create_field_mapping(self, header=None):
        pass

    def read_item(self, data, field_mapping):
        pass

    def read_key(self, data):
        pass

    def test_data(self):
        pass

    def test_keys(self):
        pass

    def scan (self, tablename, indexname, limit=100, filters=None):

        # TODO filters
        do_next_scan = True
        exclusivestartkey = None
        self.items = []
        while do_next_scan:
            do_next_scan = False
            response = ""
            if indexname:
                if exclusivestartkey:
                    response = self.ddb_client.scan(
                        TableName=tablename,
                        IndexName=indexname,
                        Select='ALL_PROJECTED_ATTRIBUTES',
                        Limit=limit,
                        ExclusiveStartKey=exclusivestartkey,
                    )
                else:
                    response = self.ddb_client.scan(
                        TableName=tablename,
                        IndexName=indexname,
                        Select='ALL_PROJECTED_ATTRIBUTES',
                        Limit=limit
                    )
            else:
                if exclusivestartkey:
                    response = self.ddb_client.scan(
                        TableName=tablename,
                        Select='ALL_ATTRIBUTES',
                        Limit=limit,
                        ExclusiveStartKey=exclusivestartkey
                    )
                else:
                    response = self.ddb_client.scan(
                        TableName=tablename,
                        Select='ALL_ATTRIBUTES',
                        Limit=limit
                    )

            if 'LastEvaluatedKey' in response:
                do_next_scan = True
                exclusivestartkey = response['LastEvaluatedKey']
            responseJSON = json.dumps(response)
            data = json.loads(responseJSON)
            logger.info('Retrieved {} tasks for batch'.format(data['Count']))

            for i in data['Items']:
                self.items.append(i)
                # TODO create and add class object

    def query (self, tablename, indexname, key, keyrange=[], limit=100, filters=None):

        # TODO filters

        keyexp, keyexpvalues = self.key_range_expression(key, keyrange, indexname)

        do_next_scan = True
        exclusivestartkey = None
        self.items = []
        while do_next_scan:
            do_next_scan = False
            response = ""
            if indexname:
                if exclusivestartkey:
                    response = self.ddb_client.query(
                        TableName=tablename,
                        IndexName=indexname,
                        Select='ALL_PROJECTED_ATTRIBUTES',
                        Limit=limit,
                        ExclusiveStartKey=exclusivestartkey,
                        KeyConditionExpression=keyexp,
                        ExpressionAttributeValues=keyexpvalues
                    )
                else:
                    response = self.ddb_client.query(
                        TableName=tablename,
                        IndexName=indexname,
                        Select='ALL_PROJECTED_ATTRIBUTES',
                        Limit=limit,
                        KeyConditionExpression=keyexp,
                        ExpressionAttributeValues=keyexpvalues
                    )
            else:
                if exclusivestartkey:
                    response = self.ddb_client.query(
                        TableName=tablename,
                        Select='ALL_ATTRIBUTES',
                        Limit=limit,
                        ExclusiveStartKey=exclusivestartkey,
                        KeyConditionExpression=keyexp,
                        ExpressionAttributeValues=keyexpvalues
                    )
                else:
                    response = self.ddb_client.query(
                        TableName=tablename,
                        Select='ALL_ATTRIBUTES',
                        Limit=limit,
                        KeyConditionExpression=keyexp,
                        ExpressionAttributeValues=keyexpvalues
                    )

            if 'LastEvaluatedKey' in response:
                do_next_scan = True
                exclusivestartkey = response['LastEvaluatedKey']
            responseJSON = json.dumps(response)
            data = json.loads(responseJSON)
            logger.info('Retrieved {} tasks for batch'.format(data['Count']))

            for i in data['Items']:
                self.items.append(i)
                # TODO create and add class object

    def query_keys (self, tablename, keys):

        keyvalues = self.key_expression(keys)
        self.items = []
        while keyvalues:
            response = self.ddb_client.batch_get_item(
                RequestItems={
                tablename:
                    {'Keys': keyvalues
                    }
                }
            )

            if 'UnprocessedKeys' in response:
                keyvalues = response['UnprocessedKeys']
            else:
                keyvalues = []
            responseJSON = json.dumps(response)
            data = json.loads(responseJSON)
            logger.info('Retrieved {} tasks for batch'.format(len(data['Responses'][tablename])))

            for i in data['Responses'][tablename]:
                self.items.append(i)
                # TODO create and add class object

    def save (self, tablename, items):

        remaining_items = []
        batch_items = []
        self.items = []
        for i in items: 
            batch_item = json.loads(json.dumps(
                {"PutRequest": {
                        "Item": i
                    }
                }        
            ))
            batch_items.append(batch_item)

        while batch_items:
            items_to_send = batch_items[:self.save_batch_size]
            batch_items = batch_items[self.save_batch_size:]
            response = self.ddb_client.batch_write_item(
                RequestItems={tablename: items_to_send})
            unprocessed_items = response['UnprocessedItems']

            if unprocessed_items and unprocessed_items[tablename]:
                batch_items.extend(unprocessed_items[tablename])

            logger.info("Batch write sent %s, unprocessed: %s",
                        len(items_to_send), len(remaining_items))

        self.items.extend(items)
        # TODO create and add class object

    def delete (self, tablename, items):

        remaining_items = []
        batch_items = []
        self.items = []
        for i in items: 
            key = self.read_key(i)
            batch_item = json.loads(json.dumps(
                {"DeleteRequest": {
                        "Key": key
                    }
                }        
            ))
            batch_items.append(batch_item)

        while batch_items:
            items_to_send = batch_items[:self.save_batch_size]
            batch_items = batch_items[self.save_batch_size:]
            response = self.ddb_client.batch_write_item(
                RequestItems={tablename: items_to_send})
            unprocessed_items = response['UnprocessedItems']

            if unprocessed_items and unprocessed_items[tablename]:
                batch_items.extend(unprocessed_items[tablename])

            logger.info("Batch write sent %s, unprocessed: %s",
                        len(items_to_send), len(remaining_items))

    def delete_keys (self, tablename, item_keys):

        remaining_items = []
        batch_items = []
        self.items = []
        for i in item_keys: 
            batch_item = json.loads(json.dumps(
                {"DeleteRequest": {
                        "Key": i
                    }
                }        
            ))
            batch_items.append(batch_item)

        while batch_items:
            items_to_send = batch_items[:self.save_batch_size]
            batch_items = batch_items[self.save_batch_size:]
            response = self.ddb_client.batch_write_item(
                RequestItems={tablename: items_to_send})
            unprocessed_items = response['UnprocessedItems']

            if unprocessed_items and unprocessed_items[tablename]:
                batch_items.extend(unprocessed_items[tablename])

            logger.info("Batch write sent %s, unprocessed: %s",
                        len(items_to_send), len(remaining_items))

    def loads3csv (self, s3_bucket, s3_key, header_row=True):

        # reads from S3 file into a json format ready to pass along
        s3_client = self.session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
        s3obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)

        logger.debug ('Reading S3 Data File: bucket:{}, key:{}'.format(s3_bucket,s3_key))
        filedata = s3obj['Body'].read()
        data = filedata.decode("utf-8")
        lines = data.replace("\r\n","\n").split("\n")
        logger.info("{} rows found".format(len(lines)))

        field_mapping = {}
        if len(lines) > 0:
            if header_row:
                field_mapping = self.create_field_mapping(lines[0])
                lines.pop(0)
            else:
                field_mapping = self.create_field_mapping()

        self.items = []
        for line in lines:
            if len(line) > 0:
                try:
                    cells = line.split(",")
                    item = self.read_item(cells, field_mapping)
                    self.items.append(item)
                except Exception as ex:
                    logger.error ('Error ' + str(ex))
