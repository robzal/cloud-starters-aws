from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, BooleanAttribute
)
from botocore.session import Session
import os
import datetime
import uuid
from awslogger import logger
from datetime import datetime
import handlers.CommonFunction as CommonFunction

# DynamoDB file table name
CUSTOMER_TABLE = os.environ['DDB_CUSTOMER_TABLE_NAME']

class CustomerDDB(Model):
    class Meta:
        table_name = CUSTOMER_TABLE
        region = Session().get_config_variable('region')

    ClientId = UnicodeAttribute(hash_key=True)
    CorrespondencePreference = UnicodeAttribute()
    FirstName = UnicodeAttribute()
    LastName = UnicodeAttribute()
    EmailAddress = UnicodeAttribute()
    PhoneNumber = UnicodeAttribute()
    InsertDate = UnicodeAttribute()
    LastUpdated = UnicodeAttribute()
    Active = BooleanAttribute(default=True)
    Locked = BooleanAttribute(default=False)

class Customer(object):
    def load_customer_record(self, rows: list):

        logger.info(f'writing batch record {"0"}')
        with CustomerDDB.batch_write() as batch:
            items = []
            today_date = CommonFunction.today()
            x = 1
            for row in rows:
                if len(row) > 0:
                    try:
                        cells = row.split(",")

                        clientid = CommonFunction.unpadded_id(cells[0])
                        customer = CustomerDDB(ClientId = clientid)
                        i=1
                        customer.CorrespondencePreference = cells[i]; i+=1
                        customer.FirstName = cells[i]; i+=1
                        customer.LastName = cells[i]; i+=1
                        customer.EmailAddress = cells[i];i += 1
                        customer.PhoneNumber = cells[i]; i+=1
                        try:
                            customer.Active = True
                            if cells[i] == 'False':
                                customer.Active = False
                            i+=1
                        except:
                            customer.Active = True
                        try:
                            customer.Locked = False
                            if cells[i] == 'True':
                                customer.Locked = True
                            i+=1
                        except:
                            customer.Locked = False
                        try:
                            customer.InsertDate = cells[i]; i+=1
                        except:
                            customer.InsertDate = today_date
                        try:
                            customer.LastUpdated = cells[i]; i+=1
                        except:
                            customer.LastUpdated = today_date
                        x +=1
                        items.append(customer)
                    except:
                        logger.info(f'error processing row - {row}')
                if x % 1000 == 0:
                    logger.info(f'writing batch record {str(x)}')
                    today_date = CommonFunction.today()

            x = 1
            for item in items:
                # RZ - I've added some retry logic into pynamodb batch write library (base.py)
                if x % 1000 == 0:
                    logger.info(f'saving batch record {str(x)}')
                try:
                    x +=1
                    batch.save(item)
                except Exception as e:
                    logger.error('error in batch customer', extra={'data': str(e)})


    def delete_customer_record(self, rows: list):

        logger.info(f'deleting batch record {"0"}')
        with CustomerDDB.batch_write() as batch:
            today_date = CommonFunction.today()
            x = 1
            for row in rows:
                if len(row) > 0:
                    try:
                        cells = row.split(",")

                        clientid = CommonFunction.unpadded_id(cells[0])
                        customer = CustomerDDB(clientid)
                        batch.delete(customer)
                    except:
                        logger.info(f'error deleting row - {row}')
                x +=1
                if x % 1000 == 0:
                    logger.info(f'deleting batch record {str(x)}')
                    today_date = CommonFunction.today()
