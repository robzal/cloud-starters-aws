from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute,JSONAttribute
)

import os
import uuid
from awslogger import logger
from botocore.session import Session
import handlers.CommonFunction as CommonFunction

DDB_SUPPORT_MSG_TBL_NAME = os.environ['DDB_SUPPORT_MSG_TBL_NAME']
DDB_SUPPORT_TOPIC_TBL_NAME = os.environ['DDB_SUPPORT_TOPIC_TBL_NAME']


class SupportMessageDDB(Model):
    class Meta:
        table_name = DDB_SUPPORT_MSG_TBL_NAME
        region = Session().get_config_variable('region')
    message_id = UnicodeAttribute(hash_key=True)
    date_created = UnicodeAttribute()
    date_sent = UnicodeAttribute()
    status = UnicodeAttribute()
    topic_name = UnicodeAttribute()
    topic_type = UnicodeAttribute()
    template_name = UnicodeAttribute()
    title = UnicodeAttribute()
    data = UnicodeAttribute()
    attachment_urls = UnicodeAttribute()

class SupportTopicDDB(Model):
    class Meta:
        table_name = DDB_SUPPORT_TOPIC_TBL_NAME
        region = Session().get_config_variable('region')
    topic_name = UnicodeAttribute(hash_key=True)
    recipient_addresses = UnicodeAttribute()
    recipient_data = UnicodeAttribute()

class SupportMessage(object):
    def post_remedy_message(self, template_name: str, subject: str, data: str = '{}', attachment_urls: str = '') -> None:

        message_id = str(uuid.uuid4())
        today_date = CommonFunction.today()
        if len(attachment_urls.strip()) == 0:
            attachment_urls = ','

        message = SupportMessageDDB(
            message_id=message_id,
            date_created=today_date,
            date_sent='0',
            status='INPROGRESS',
            topic_name='-',
            topic_type='REMEDY',
            template_name=template_name,
            title=subject,
            data=data,
            attachment_urls=attachment_urls.strip()
        )
        try:
            message.save()
        except Exception as e:
            logger.error('failed to save Remedy message', extra={'data': str(e)})

    def post_email_message(self, topic_name: str, subject: str, body: str = 'CNP information', attachment_urls: str = '') -> None:

        message_id = str(uuid.uuid4())
        today_date = CommonFunction.today()
        if len(attachment_urls.strip()) == 0:
            attachment_urls = ','

        message = SupportMessageDDB(
            message_id=message_id,
            date_created=today_date,
            date_sent='0',
            status='INPROGRESS',
            topic_name=topic_name,
            topic_type='EMAIL',
            template_name='-',
            title=subject,
            data=body,
            attachment_urls=attachment_urls.strip()
        )
        try:
            message.save()
        except Exception as e:
            logger.error('failed to save Email message', extra={'data': str(e)})

    def send_message(self, message_id: str) -> None:

        today_date = CommonFunction.today()

        message = SupportMessageDDB.get(message_id)
        try:
            message.date_sent = today_date
            message.save()
        except Exception as e:
            logger.error('failed to save Remedy message', extra={'data': str(e)})
