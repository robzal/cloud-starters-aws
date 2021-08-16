from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute,JSONAttribute
)
from botocore.session import Session
import os
import datetime
import json
from random import randint
from time import sleep
from awslogger import logger
import handlers.CommonFunction as CommonFunction
from structures.Structure import Structure
from typing import Optional

# DynamoDB file table name
DDB_TABLE_NAME = os.environ['DDB_TABLE_NAME']
# DynamoDB TTL field for files
ttl_default = 6 * 24 * 60 * 60  # 144 Hours
TTL_SECONDS = os.environ.get('TTL_SECONDS',ttl_default)
# DynamoDB stream size
BATCH_SIZE = int(os.environ['DDB_STREAM_SIZE'])

class EmailMessageIdIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "email_message_id-index"
        read_capacity_units = 2 # it has to be here, but doe not really affect anything
        write_capacity_units = 1
        projection = IncludeProjection(['compositekey','sequence_number'])
    
    email_message_id = UnicodeAttribute(default='0', hash_key=True)

class SMSMessageIdIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "sms_message_id-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection(['compositekey','sequence_number'])
    
    sms_message_id = UnicodeAttribute(default='0', hash_key=True)

class FilenameIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "filename-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection([
            'filename',
            'compositekey',
            'sequence_number',
            'pdf_generated_at',
            'processed_at',
            'client_id',
            'registration_no',
            'product_code',
            'batch_date',
            'batch_no',
            'full_name',
            'address_1',
            'address_2',
            'address_3',
            'number_of_pages',
            'sms_read_at',
            'email_read_at',
            'email_delivered_at'
        ])
    
    filename = UnicodeAttribute(default='0', hash_key=True)
    compositekey = UnicodeAttribute()
    sequence_number = NumberAttribute()
    pdf_generated_at = UnicodeAttribute()
    processed_at = UnicodeAttribute()
    client_id = UnicodeAttribute()
    registration_no = UnicodeAttribute()
    product_code = UnicodeAttribute()
    batch_date = UnicodeAttribute()
    batch_no = NumberAttribute()
    full_name = UnicodeAttribute()
    address_1 = UnicodeAttribute()
    address_2 = UnicodeAttribute()
    address_3 = UnicodeAttribute()
    number_of_pages = NumberAttribute()
    sms_read_at = UnicodeAttribute()
    email_read_at = UnicodeAttribute()
    email_delivered_at = UnicodeAttribute()

class LinesProgressDDB(Model):
    class Meta:
        table_name = DDB_TABLE_NAME
        region = Session().get_config_variable('region')
    compositekey = UnicodeAttribute(hash_key=True)
    sequence_number = NumberAttribute(range_key=True)

    filename = UnicodeAttribute()
    filename_index = FilenameIdx()
    client_id = UnicodeAttribute()
    registration_no = UnicodeAttribute()
    date_prefix = UnicodeAttribute()

    submitted_at = UnicodeAttribute()
    processed_at = UnicodeAttribute(default='0')
    failed_at = UnicodeAttribute(default='0')

    item = JSONAttribute()
    pdf_generated_at = UnicodeAttribute(default='0') #when the mail is generated
    
    product_family = UnicodeAttribute()
    product_code = UnicodeAttribute()
    batch_date = UnicodeAttribute()
    batch_no = NumberAttribute()

    email_communicated_at = UnicodeAttribute(default='0')
    email_message_id = UnicodeAttribute(default='0')
    email_sent_at = UnicodeAttribute(default='0')
    email_read_at = UnicodeAttribute(default='0')
    email_delivered_at = UnicodeAttribute(default='0')
    email_message_id_index = EmailMessageIdIdx()

    sms_communicated_at = UnicodeAttribute(default='0')
    sms_message_id = UnicodeAttribute(default='0')
    sms_read_at = UnicodeAttribute(default='0')
    sms_message_id_index = SMSMessageIdIdx()
    
    ttl  = NumberAttribute()

    full_name = UnicodeAttribute()
    address_1 = UnicodeAttribute(default='0')
    address_2 = UnicodeAttribute(default='0')
    address_3 = UnicodeAttribute(default='0')
    number_of_pages = NumberAttribute()
    number_of_emails = NumberAttribute()
    number_of_sms = NumberAttribute()
    number_of_htmls = NumberAttribute()
    
class LinesProgress(object):

    def rows_to_ddb(self, range_seq: int, rows: list, filename: str, product_code: str, date_prefix: str, batch_date: str, batch_no: int) -> None:
        """
        Insert following rows into DynamoDB

        :param range_seq: batch sequence number
        :param rows: rows to insert
        :param filename: uploaded filename
        :return: None
        """
        unix_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        ttl = int(unix_timestamp + TTL_SECONDS)
        product_family = Structure.get_product_family_name(filename)

        with LinesProgressDDB.batch_write() as batch:
            items = []
            for i, row in enumerate(rows):
                address = CommonFunction.assemble_address(row)
                row_sequence_number = range_seq * BATCH_SIZE + (i + 1)
                item = LinesProgressDDB(
                    item = row,
                    product_family = product_family,
                    product_code = product_code,
                    batch_date = batch_date,
                    batch_no = batch_no,
                    submitted_at = CommonFunction.today(),
                    date_prefix = date_prefix,
                    compositekey = str(row_sequence_number) + '-' + filename,
                    filename = filename,
                    # client_id = row[Structure.primary_key_mapping(product_family)],
                    sequence_number = row_sequence_number,
                    ttl = ttl,
                    number_of_pages = -1, #defaulting to an erroneous value
                    number_of_emails = -1, #defaulting to an erroneous value
                    number_of_sms = -1, #defaulting to an erroneous value
                    number_of_htmls = -1, #defaulting to an erroneous value
                    address_1 = address['address_1'],
                    address_2 = address['address_2'],
                    address_3 = address['address_3'],
                    registration_no = ddb_safe_get_value(row, 'Registration_No'),
                    full_name = ddb_safe_get_value(row, 'FullName')
                )
                # TODO : Fetch the rego if client_id is missing
                if Structure.primary_key_mapping(product_family) in row:
                    item.client_id = row[Structure.primary_key_mapping(product_family)]
                    # logger.info('client id for this record is {}'.format(item.client_id))
                else:
                    item.client_id = ' '
                    # logger.info('No clientId for this record')
                items.append(item)

            for item in items:
                # RZ - I've added some retry logic into pynamodb batch write library (base.py)
                try:
                    batch.save(item)
                except Exception as e:
                    logger.error('error in rows_to_ddb', extra={'data': str(e)})
                    raise e

    def retrieve_lines(self, stream_record, retry: bool = True) -> LinesProgressDDB:
        """
        Retrieve DynamoDB record using composite key stored in stream_record
        :param table_name: files table
        :param stream_record:
        :return: record information or None
        """
        try:
            compositekey = str(stream_record['sequence_number']) + '-' + str(stream_record['filename'])
            sequence_number = (stream_record['sequence_number'])
 
            # some retry logic as the lines table also gets very busy
            j = 1
            if retry == False:
                j = 10
                
            while j <= 10:
                try:
                    record = LinesProgressDDB.get(str(compositekey), int(stream_record['sequence_number']))
                    j = 11
                except Exception as e:
                    print('error while reading line record, attempt {} for key {} and sequence {}'.format(j, compositekey, sequence_number))
                    sleep (randint(3,10))
                    j += 1
                    if j > 10:
                        # throw the exception as the processing will be missing records
                        logger.error('error while reading line record, attempt {} for key {} and sequence {}'.format(j, compositekey, sequence_number))
                        raise e

            return record

        except Exception as e:
            print(stream_record)
            logger.error('failed to retrieve item from LinesProgressDDB', extra={ "err": str(e)})
            return None

def ddb_safe_get_value(d: dict, key: str):
    value = d.get(key)
    if value is None or value == '':
        return ' '
    return value
