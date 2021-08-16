import sys
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, BooleanAttribute
)
import os
import csv
import logging
from botocore.session import Session
from handlers.MetadataLUT import MetadataLUT
from handlers.MetadataLUT import MetadataLUTDDB

print(sys.path)

if __name__ == '__main__':
    # create a fake LUT for testing purpose.
    print(Session().get_config_variable('region'))
    print(Session().get_config_variable('profile'))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    with open('layers/custom/python/handlers/lut.csv', newline='') as csvfile:
        content = csv.reader(csvfile, delimiter=',')
        meta_lut = MetadataLUT()
        for row in content:
            try:
                meta_lut.load_metadata_record(row)
            except Exception as error:
                logger.info('Error Loading Product Data from S3 DataLoad bucket')
                logger.info(row)
                logger.info(str(error))
