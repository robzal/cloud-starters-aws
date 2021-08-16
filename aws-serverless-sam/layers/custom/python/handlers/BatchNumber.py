from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute
)
from botocore.session import Session
from awslogger import logger

import os

# DynamoDB batch_no table name
DDB_SEEDS_TABLE_NAME = os.environ['DDB_SEEDS_TABLE_NAME']

SEED_NAME = 'batch_number'

class SeedsDDB(Model):
    class Meta:
        table_name = DDB_SEEDS_TABLE_NAME
        region = Session().get_config_variable('region')
    seed_name = UnicodeAttribute(hash_key=True)
    seed_value = NumberAttribute()

def get_batch_number(seed_name:str = SEED_NAME) -> int:
    '''
    get unique seed_value.
    '''

    try:
        seed = SeedsDDB.get(seed_name)
    except SeedsDDB.DoesNotExist:
        logger.info("seed not exist, initiating")
        seed = SeedsDDB(seed_name, seed_value=0)
        seed.save()
    except Exception as e:
        logger.error("get_batch_number for {} failed".format(seed_name), extra={'data': str(e)})

    seed.refresh()
    seed.update(
        actions=[
            SeedsDDB.seed_value.add(1)
        ]
    )
    return seed.seed_value


    