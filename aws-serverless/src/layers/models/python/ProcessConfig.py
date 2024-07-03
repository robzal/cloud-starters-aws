import os
import sys
import json
import boto3
import botocore
import datetime
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

# os.environ['DYNAMODB_CONTROL_TABLE_NAME'] = 'serverless-demo-admin-Process-Control'
PROCESS_CONTROL_TABLE = os.environ['DYNAMODB_CONTROL_TABLE_NAME']

class ProcessConfigDDB(Model):
    class Meta:
        table_name = PROCESS_CONTROL_TABLE
        region = Session().get_config_variable('region')

    process_name = UnicodeAttribute(hash_key=True)
    metric_name = UnicodeAttribute(range_key=True)
    value = UnicodeAttribute()
    date_modified = UnicodeAttribute(default='')
    
class ProcessConfig(object):

    def get_item(self, process_name: str, metric_name: str):

        logger.info('Getting config record {}-{}'.format(process_name,metric_name))
        try:
            process_config = ProcessConfigDDB.get(
                process_name,
                metric_name
            )
            return process_config
        except Exception as e:
            logger.error('failed to get config record', extra={'data': str(e)})

    def add_update_item(self, process_name: str, metric_name: str, value: str):

        logger.info('writing record {}-{}'.format(process_name,metric_name))
        date_modified = str(datetime.datetime.now())
        try:
            process_config = ProcessConfigDDB.get(
                process_name,
                metric_name
            )
            process_config.value = value
            process_config.date_modified = date_modified
            process_config.save()
        except ProcessConfigDDB.DoesNotExist:
            process_config = ProcessConfigDDB(
                process_name=process_name,
                metric_name=metric_name,
                value=value,
                date_modified = date_modified
            )
            process_config.save()
        except Exception as e:
            logger.error('failed to write record', extra={'data': str(e)})
            logger.info(str(e))

    def delete_item(self, process_name: str, metric_name: str):

        logger.info('Deleting Process Config record.')
        try:
            h = ProcessConfigDDB.get(process_name, metric_name)
            h.delete()
        except ProcessConfigDDB.DoesNotExist:
            pass
        except Exception as error:
            logger.info('Error Deleting Process Config')
            logger.info(str(error))

if __name__ == '__main__':
    pass
    # process_config = ProcessConfig()
    # proc_name='DemoQueue'
    # process_config.add_update_item(proc_name, 'max_concurrent_processor_lambdas', '1')
    # process_config.add_update_item(proc_name, 'processor_concurrency_query_minutes', '2')
    # process_config.add_update_item(proc_name, 'processor_stop', '0')
    # process_config.add_update_item(proc_name, 'processor_lambda_timeout_secs', '300')
    # process_config.add_update_item(proc_name, 'processor_lambda_sqs_batch_size', '10')
    # process_config_metric = process_config.get_item(proc_name, 'max_concurrent_processor_lambdas')
    # logger.info(process_config_metric.value)
    # process_config.delete_item(proc_name, 'max_concurrent_processor_lambdas')

