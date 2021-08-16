
import csv
import os, sys
import math
import json
from time import sleep
from datetime import datetime, timedelta
import boto3
from awscontainerlogger import logger
from handlers.CSVHandler import CsvGenerator
import handlers.CommonFunction as CommonFunction

# S3 Bucket to upload csv files
DDB_USER_TABLE_NAME = os.environ["DDB_USER_TABLE_NAME"]
DDB_REPORT_TABLE_NAME = os.environ["DDB_REPORT_TABLE_NAME"]
S3_BUCKET_REPORTS = os.environ["S3_BUCKET_REPORTS"]
TZ = os.environ["TZ"]

# Folder to output reports
OUTPUT_FOLDER = "reports"

client_ddb = boto3.client("dynamodb")
client_s3 = boto3.client("s3")
client_sfn = boto3.client("stepfunctions")
task_token = os.environ['taskToken']

class DailyReports(object):
    def __init__(self):
        pass

    def check_s3_key_exists(self, s3_bucket, s3_key):

        try:
            results = client_s3.list_objects(Bucket=s3_bucket, Prefix=s3_key)
            return 'Contents' in results
        except:
            return False

    def write_to_csv(self, header, rows, s3_key, create_empty_report:bool = True):
        """
        Creates the various CSV reports for files processed
        :return:
        """

        if create_empty_report == False and len(rows) == 0:
            logger.info ('No records present. Skipping generating report - {}'.format(s3_key))
        else:
            logger.info ('generating report - {}'.format(s3_key))

            csv = CsvGenerator(S3_BUCKET_REPORTS, s3_key)
            csv.create_csv_header(header)

            for row in rows:
                csv.write_row(row)

            csv.save_csv()

            logger.info ('report completed - {}'.format(s3_key))

def lambda_handler(event, context):
    # reports = DailyReports()
    # reports.write_reports()
    logger.info('Processing starting.')

    response = json.dumps({'result': 'success'})
    client_sfn.send_task_success(
        taskToken = task_token,
        output = response
    )

    logger.info('Processing complete.')

    return response

if __name__ == '__main__':
    SF_Record = json.dumps({'request': 'event'})
    lambda_handler(SF_Record,'')
