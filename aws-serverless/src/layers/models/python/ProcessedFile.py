import os
import sys
import json
import boto3
import botocore
import datetime
import uuid
from botocore.session import Session
from botocore.client import Config

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute
)

from logger import *
from config import *

logger = Logger().logger
config = Config().config

# os.environ['DYNAMODB_FILES_TABLE_NAME'] = 'serverless-demo-admin-Files'
PROCESSED_FILE_TABLE = os.environ['DYNAMODB_FILES_TABLE_NAME']

class FilenameIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "filename-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection([
            'filename',
            'id',
            'date_modified'
        ])
    
    filename = UnicodeAttribute(hash_key=True)
    id = UnicodeAttribute(range_key=True)
    date_modified = UnicodeAttribute()

class ProcessedFileDDB(Model):
    class Meta:
        table_name = PROCESSED_FILE_TABLE
        region = Session().get_config_variable('region')

    id = UnicodeAttribute(hash_key=True)
    filename = UnicodeAttribute()
    date_modified = UnicodeAttribute(default='')
    # Adding a secondary index as an example
    # it would be used as follows
    # items = ProcessedFileDDB.filename_index.query(filename)
    filename_index = FilenameIdx()
    
class ProcessedFile(object):

    def get_item(self, filename: str):

        logger.info('Getting file record {}'.format(filename))
        try:
            items = ProcessedFileDDB.filename_index.query(
                filename
            )
            for i in items:
                return i
        except Exception as e:
            logger.error('failed to get file record', extra={'data': str(e)})

    def add_update_item(self, filename: str):

        logger.info('writing record {}'.format(filename))
        date_modified = str(datetime.datetime.now())
        try:
            items = ProcessedFileDDB.filename_index.query(
                filename
            )
            found = False
            for i in items:
                found=True
                i.date_modified = date_modified
                i.save()
            if found == False:
                raise ProcessedFileDDB.DoesNotExist()
        except ProcessedFileDDB.DoesNotExist:
            id = str(uuid.uuid4())
            processed_file = ProcessedFileDDB(
                id = id,
                filename=filename,
                date_modified = date_modified
            )
            processed_file.save()
        except Exception as e:
            logger.error('failed to write record', extra={'data': str(e)})
            logger.info(str(e))

    def delete_item(self, filename: str):

        logger.info('Deleting Processed File record {}'.format(filename))
        try:
            # h = ProcessedFileDDB.get(filename)
            # h.delete()
            items = ProcessedFileDDB.filename_index.query(
                filename
            )
            for i in items:
                i.delete()

        except ProcessedFileDDB.DoesNotExist:
            pass
        except Exception as error:
            logger.info('Error Deleting Processed File')
            logger.info(str(error))

if __name__ == '__main__':
    processed_file = ProcessedFile()
    processed_file.add_update_item('myfilename')
    processed_file_item = processed_file.get_item('myfilename')
    logger.info(processed_file_item.filename)
    processed_file.delete_item('myfilename')
