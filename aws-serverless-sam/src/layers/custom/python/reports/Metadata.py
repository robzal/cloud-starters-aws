import boto3
import csv
from reports.Report import Report
from boto3.dynamodb.conditions import Key, Attr
from awslogger import logger
import io

client_s3 = boto3.client('s3')


class Metadata(Report):

    def __assemble_address(self, row) -> dict:
        address = {
            'address_1': ' ',
            'address_2': ' ',
            'address_3': ' ',
        }
        has_address_1 = 'Post_Address_1' in row and row['Post_Address_1']
        has_address_2 = 'Post_Address_2' in row and row['Post_Address_2']
        has_address_3 = 'Post_Address_3' in row and row['Post_Address_3']
        has_state = 'Post_State' in row and row['Post_State']
        has_suburb = 'Post_Suburb' in row and row['Post_Suburb']
        has_postcode = 'PostCode' in row and row['PostCode']

        # if address line 1 is provided
        if has_address_1:
            address['address_1'] = row['Post_Address_1']
        # if address line 2 is provided
        if has_address_2:
            address['address_2'] = row['Post_Address_2']
        # if address line 3 is provided use it, otherwise use concatenated state, suburb and post
        if has_address_3:
            address['address_3'] = row['Post_Address_3']
        else:
            line3 = ''
            if has_state:
                line3 = row['Post_State']
            if has_suburb:
                if not line3:
                    line3 = row['Post_Suburb']
                else:
                    line3 = "{} {}".format(line3, row['Post_Suburb'])
            if has_postcode:
                if not line3:
                    line3 = row['PostCode']
                else:
                    line3 = "{} {}".format(line3, row['PostCode'])
            if line3:
                address['address_3'] = line3
        return address

    def fetch(self, table_name: str, filename: str) -> list:
        """
        Fetch records that belong to the given filename

        :param table_name: table name to scan
        :param filename: filename prefix to use for scan
        :return: list of records
        """

        rows = []

        query = {
            'FilterExpression': Attr('filename').begins_with(filename),
        }

        table = self.resource_ddb.Table(table_name)

        def _scan_table(query: dict) -> dict:
            return table.scan(**query)

        while True:
            logger.info('scanning {} table for metadata report using {} filename prefix'.format(table_name, filename), extra={'data': query})
            response = _scan_table(query)
            rows.update(response['Items'])

            if 'LastEvaluatedKey' not in response:
                break

            query['ExclusiveStartKey'] = response['LastEvaluatedKey']

        return rows

    def fill(self, rows: list) -> list:
        """
        Generate metadata report using provided records

        :param rows:
        :return:
        """
        report_lines = []

        for row in rows:
            report_line = self.__assemble_address(row)
            report_line['filename'] = row['filename']
            report_line['batch_no'] = '123'
            report_line['client_id'] = '123'
            report_line['customer_name'] = '{} {}'.format(row['Name'], row['NameLine2'])
            report_line['num_of_logical_pages'] = row['number_of_pages']
            report_line['printing_mode'] = 'tba'
            report_line['hopper_1'] = False
            report_line['hopper_2'] = False
            report_line['hopper_3'] = False
            report_line['hopper_4'] = False
            report_line['hopper_5'] = False
            report_line['hopper_6'] = False

            report_lines.append(report_line)

        return report_lines

    def save(self, filename: str, rows: dict, bucket_name: str, prefix: str) -> str:
        """
        Save given rows as csv file in the given s3 destination

        :param filename: filename
        :param rows: report rows
        :param bucket_name: bucket name
        :param prefix: bucket prefix
        :return:
        """

        key = '{}/{}'.format(prefix, '{}_Meta.csv'.format(filename))

        output = io.StringIO()

        writer = csv.DictWriter(output, rows[0].keys())
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        client_s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=output.getvalue()
        )



