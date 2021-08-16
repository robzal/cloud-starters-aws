import csv
import os
import sys
from botocore.session import Session
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from handlers.CSCLookup import CSCLookup
from handlers.CSCLookup import CSCLookupDDB

print(sys.path)

if __name__ == "__main__":
    print(Session().get_config_variable("region"))
    print(Session().get_config_variable("profile"))

    with open("layers/custom/python/handlers/closest_csc.csv", newline="") as csvfile:
        content = csv.reader(csvfile, delimiter=",")
        csc_lut = CSCLookup()
        for row in content:
            try:
                csc_lut.load_csc_record(row)
            except Exception as error:
                logger.info('Error Loading Postcode Data from S3 DataLoad bucket')
                logger.info(row)
                logger.info(str(error))
