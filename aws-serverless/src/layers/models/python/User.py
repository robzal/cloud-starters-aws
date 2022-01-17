import os
import json
import boto3
import botocore
import csv
from botocore.session import Session
from botocore.client import Config
import logging
from DDBClass import DDBClass

logger = logging.getLogger()

class User(DDBClass):
    def __init__(self):
        super().__init__()
        # fill in any specific constructor details here

    def key_range_expression(self, key, range, indexname=None):

        # TODO add range logic
        keyexp = ''
        keyexpvalues = ''
        if not indexname:
            keyexp = "userid = :userid"
            keyexpvalues = {
                            ':userid': {'S': str(key)}
                            }
        else:
            keyexp = "firstname = :firstname"
            keyexpvalues = {
                            ':firstname': {'S': str(key)}
                            }
        return keyexp, keyexpvalues

    def key_expression(self, keys):

        keyvalues = []
        for key in keys:
            keyvalues.append({'userid':
                                {'S':str(key)}
                            })
        return keyvalues

    def create_field_mapping(self, header=None):

        field_mapping = {}
        if header:
            #TODO read header to get mappings for Class
            field_mapping = {'userid': 0,'firstname': 1,'surname': 2}
        else:
            field_mapping = {'userid': 0,'firstname': 1,'surname': 2}
        return field_mapping

    def read_item(self, data, field_mapping):

        userid = data[field_mapping['userid']]
        firstname = data[field_mapping['firstname']]
        surname = data[field_mapping['surname']]
        item = json.loads(json.dumps({
            'userid': {'S': str(userid)}, 'firstname': {'S': str(firstname)}, 'surname': {'S': str(surname)}}))
        return item

    def read_key(self, data):

        item_key = json.loads(json.dumps({
                                "userid": 
                                    data['userid']
                                
                            }))
        return item_key

    def test_data(self):
        items = []
        for t in range(1,31):
            items.append(json.loads(json.dumps({
                                "userid": {
                                    "S": str(t)
                                },
                                "firstname": {
                                    "S": "rob"
                                },
                                "surname": {
                                    "S": "zzz"
                                }
                            })))
        return items

    def test_keys(self):
        item_keys = []
        for t in range(1,31):
            item_keys.append(json.loads(json.dumps({
                                "userid": {
                                    "S": str(t)
                                }
                            })))

        return item_keys
