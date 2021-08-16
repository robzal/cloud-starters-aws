import re
import datetime
import boto3
from typing import Optional
from awslogger import logger
from boto3.dynamodb.conditions import Key

dynamodb_resource = boto3.resource("dynamodb")

class DynamoDB(object):

    @staticmethod
    def _today():
        """
        Today's date in approved format, do NOT change this
        :return: today's date
        """
        return datetime.datetime.today().strftime('%Y-%m-%d %H:%M')

    @staticmethod
    def _is_datetime_or_empty(value: str) -> bool:
        """
        Determine if value is datetime or equals to 0

        :param value: string to compare
        :return: True if value is datetime or eq to 0
        """
        return re.match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}', value) or value == '0'

    @staticmethod
    def merge_headers(headers: list) -> dict:
        """
        Transform email event headers from list into dict

        :param headers: list of dictionaries
        :return: dict of headers
        """
        r = {}
        for header in headers:
            r[header['name']] = header['value']

        return r

    def _retrieve_ddb_record(self, table_name: str, stream_record) -> Optional[dict]:
        """
        Retrieve DynamoDB record using composite key stored in stream_record
        :param table_name: files table
        :param stream_record:
        :return: record information or None
        """

        table = dynamodb_resource.Table(table_name)

        try:
            response = table.get_item(
                Key={
                    'filename': stream_record['filename'],
                    'client_id': stream_record['client_id']
                }
            )

            return response['Item']
        except Exception as e:
            logger.warn('failed to retrieve item from {} table'.format(table_name), extra={'data': stream_record})
            return None

    def _mark_communication_by_record(self, table_name: str, stream_record: dict, attributes: dict) -> bool:
        """
        Common function to mark record's communications

        :param table_name: table name
        :param stream_record: record information
        :param attributes: fields to update
        :return: True
        """

        update_item_request = {
            'Key': {
                'filename': stream_record['filename'],
                'client_id': stream_record['client_id']
            },
            'UpdateExpression': None,
            'ExpressionAttributeValues': None,
            'ReturnValues': 'UPDATED_NEW'
        }

        update_expression = ''
        expression_attribute_values = {}

        for k, v in attributes.items():
            update_expression += '{}=:{},'.format(k, k)
            expression_attribute_values[':{}'.format(k)] = v

        update_expression = 'set {}'.format(update_expression.strip(','))

        update_item_request['UpdateExpression'] = update_expression
        update_item_request['ExpressionAttributeValues'] = expression_attribute_values

        try:
            table = dynamodb_resource.Table(table_name)
            table.update_item(**update_item_request)
        except Exception as e:
            logger.error('error updating DDB', extra={'data': str(e)})

        return True

    def _mark_communication_by_index(self, table_name: str, key_value: str, attributes: dict, index_name: str, key_name: str) -> None:
        """
        Common function to mark communication using index

        :param table_name: table name to update
        :param key_value: email_message_id or sms_message_id
        :param attributes: fields to update
        :param index_name: DynamoDB index, either 'sms_message_id-index' or 'email_message_id-index'
        :param key_name: DynamoDB field name, either 'email_message_id' or 'sms_message_id'
        :return: None
        """
        table = dynamodb_resource.Table(table_name)

        try:
            query_request = {
                'IndexName': index_name,
                'KeyConditionExpression': Key(key_name).eq(key_value),
            }
            response = table.query(**query_request)
        except Exception as e:
            logger.error('failed query ddb table', extra={'data': str(e)})
            return False

        if not response['Items']:
            logger.info('no items found to mark')
            return False

        item = response['Items'][0]

        update_item_request = {
            'Key': {
                'filename': item['filename'],
                'client_id': item['client_id']
            },
            'UpdateExpression': None,
            'ExpressionAttributeValues': None,
            'ReturnValues': 'UPDATED_NEW'
        }

        update_expression = ''
        expression_attribute_values = {}

        for k, v in attributes.items():
            update_expression += '{}=:{},'.format(k, k)
            expression_attribute_values[':{}'.format(k)] = v

        update_expression = 'set {}'.format(update_expression.strip(','))

        update_item_request['UpdateExpression'] = update_expression
        update_item_request['ExpressionAttributeValues'] = expression_attribute_values

        try:
            table.update_item(**update_item_request)
        except Exception as e:
            logger.error('failed update ddb table', extra={'data': str(e)})
