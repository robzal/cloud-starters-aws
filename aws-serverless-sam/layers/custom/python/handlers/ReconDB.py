from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute,JSONAttribute
)

import os
from botocore.session import Session

DDB_RECON_TBL_NAME = os.environ['DDB_RECON_TBL_NAME']


class ReconDDB(Model):
    class Meta:
        table_name = DDB_RECON_TBL_NAME
        region = Session().get_config_variable('region')
    filename = UnicodeAttribute(hash_key=True)
    batch_no = NumberAttribute()
    product_code = UnicodeAttribute()
    product_description = UnicodeAttribute()
    date_processed = UnicodeAttribute()
    total_records = NumberAttribute()
    valid_records = NumberAttribute()
    invalid_records = NumberAttribute()
    email_sent = NumberAttribute()
    sms_sent = NumberAttribute()
    mail_sent = NumberAttribute()
    simplex_page_count = NumberAttribute()
    duplex_page_count = NumberAttribute()
    envelope_regular_count = NumberAttribute()
    envelope_priority_count = NumberAttribute()
    insert_count = NumberAttribute()
    change_of_address_base_stock_count = NumberAttribute()
    vessels_label_base_stock_count = NumberAttribute()