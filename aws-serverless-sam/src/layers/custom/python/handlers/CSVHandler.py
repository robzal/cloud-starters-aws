import csv
from io import StringIO

import boto3
from awslogger import logger

client_s3 = boto3.client("s3")

csv.register_dialect("myDialect", quoting=csv.QUOTE_ALL, skipinitialspace=True)

class CsvGenerator(object):
    def __init__(self, s3_bucket: str, s3_key: str):
        """
        Init the generator with s3 bucket and key

        """
        logger.info("writing CSV to s3://{}/{}".format(s3_bucket, s3_key))

        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.tmp_file = StringIO()
        self.writer = csv.writer(self.tmp_file, dialect="myDialect")

    def create_csv_header(self, header: list):
        """
        Create header for CSV
        """
        self.write_row(header)

    def write_row(self, row: list):
        """
        Write a row to CSV
        """
        self.writer.writerow(row)

    def write_rows(self, rows: list):
        """
        Write rows to CSV
        """
        for row in rows:
            self.writer.writerow(row)

    def save_csv(self):
        '''
        Save file to S3
        :return:
        '''
        logger.info("begin upload CSV to s3://{}/{}".format(self.s3_bucket, self.s3_key))
        client_s3.put_object(Body=self.tmp_file.getvalue(), Bucket=self.s3_bucket, Key=self.s3_key)
        logger.info("CSV uploaded to s3://{}/{}".format(self.s3_bucket, self.s3_key))
