from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute
)
from botocore.session import Session
from collections import namedtuple
import os
import math
from awslogger import logger
from datetime import datetime
import handlers.CommonFunction as CommonFunction
from handlers.MetadataLUT import MetadataLUTDDB
import handlers.Multi as Multi

# DynamoDB file table name
DDB_STATS_TABLE_NAME = os.environ['DDB_STATS_TABLE_NAME']


class FileDateFinalisedIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "date_finalised-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection(['filename','date_processed','total_mail_sent'])
    
    date_finalised = UnicodeAttribute(default='0', hash_key=True)

class FileDigitalDateFinalisedIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "date_digital_finalised-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection(['filename','date_processed','date_finalised','finalise_status'])
    
    date_digital_finalised = UnicodeAttribute(default='0', hash_key=True)

class FilesProgressDDB(Model):
    class Meta:
        table_name = DDB_STATS_TABLE_NAME
        region = Session().get_config_variable('region')

    filename = UnicodeAttribute(hash_key=True)
    product_code = UnicodeAttribute()
    date_prefix = UnicodeAttribute()
    date_processed = UnicodeAttribute()
    batch_date = UnicodeAttribute()
    batch_no = NumberAttribute()

    rows_failed = NumberAttribute()  # number of rows in this logical file that failed to merge/send correspondence
    rows_processed = NumberAttribute()  # number of rows in this logical file where email/sms/mail was sent
    rows_total = NumberAttribute()  # number of rows in physical DAT, including header/tailer/heading
    rows_total_processable = NumberAttribute()  # number of valid rows in this logical file that should be processed
    rows_invalid = NumberAttribute()  # number of invalid rows in physical DAT (0 for L6 and G6 logical files, which contain only valid rows)

    total_emails_sent = NumberAttribute(default=0)  # including bounced/failed
    total_sms_sent = NumberAttribute(default=0)  # including failed
    total_mail_sent = NumberAttribute(default=0)
    total_page_created = NumberAttribute(default=0)
    total_duplex_page_created = NumberAttribute(default=0)

    date_finalised = UnicodeAttribute(default='0')
    date_finalised_index = FileDateFinalisedIdx()
    finalise_status = UnicodeAttribute(default='0')
    finalise_detail = UnicodeAttribute(default='0')
    date_digital_finalised = UnicodeAttribute(default='0')
    date_digital_finalised_index = FileDigitalDateFinalisedIdx()
    digital_finalised_fallback = UnicodeAttribute(default='0')

    mailhouse_recon_validation = UnicodeAttribute(null=True)


class FilesProgress(object):
    def initiate_process_progress(self, filename: str, auto_approve: str, product_code: str, rows_total: int, rows_total_processable: int, rows_invalid: int,
                                  date_prefix: str, date_processed: str, batch_date: str, batch_no: int) -> None:

        date_finalised = '0'
        finalise_status = '0'
        finalise_detail = '0'
        if auto_approve == 'True':
            date_finalised = CommonFunction.today()
            finalise_status = 'APPROVED'
            finalise_detail = 'Auto Approved'

        new_file = FilesProgressDDB(
            filename=filename,
            product_code=product_code,
            rows_failed=0,
            rows_processed=0,
            rows_total=rows_total,
            rows_total_processable=rows_total_processable,
            rows_invalid=rows_invalid,
            date_prefix=date_prefix,
            date_processed=date_processed,
            batch_date=batch_date,
            batch_no=batch_no,
            total_emails_sent=0,
            total_sms_sent=0,
            total_mail_sent=0,
            total_page_created=0,
            total_duplex_page_created=0,
            date_finalised=date_finalised,
            finalise_status=finalise_status,
            finalise_detail=finalise_detail,
            mailhouse_recon_validation=''
        )
        try:
            new_file.save()
        except Exception as e:
            logger.error('failed to execute create_new_files_record', extra={'data': str(e)})

    def has_process_progress_finished(self, filename: str, is_multi: bool) -> bool:
        """
        Check if the process has finished

        :param process_record:
        :return:
        """
        process_record = self.get_process_record(filename)

        total = int(process_record.rows_total_processable)
        processed = int(process_record.rows_failed) + int(process_record.rows_processed)
        totalL6 = 0
        processedL6 = 0
        totalG6 = 0
        processedG6 = 0
        logger.info('checking process progress', extra={'data': {
            'filename': filename,
            'total': total,
            'processed': processed
        }})

        if is_multi:
            filenameL6, filenameG6 = Multi.filenames(filename)

            process_record = self.get_process_record(filenameL6)

            totalL6 = int(process_record.rows_total_processable)
            processedL6 = int(process_record.rows_failed) + int(process_record.rows_processed)
            logger.info('checking process progress', extra={'data': {
                'filename': filenameL6,
                'total': totalL6,
                'processed': processedL6
            }})

            process_record = self.get_process_record(filenameG6)

            totalG6 = int(process_record.rows_total_processable)
            processedG6 = int(process_record.rows_failed) + int(process_record.rows_processed)
            logger.info('checking process progress', extra={'data': {
                'filename': filenameG6,
                'total': totalG6,
                'processed': processedG6
            }})

        return total <= processed and totalL6 <= processedL6 and totalG6 <= processedG6

    def get_process_record(self, filename: str) -> FilesProgressDDB:
        """
        Retrieve process record for the given file
        :param filename:
        :return:
        """
        try:
            process_record = FilesProgressDDB.get(filename)
        except Exception as e:
            logger.error('failed to execute has_process_progress_finished', extra={'data': str(e)})

        return process_record

    def increment_processed(self, filename):
        """
        Increment rows_processed counter

        :param filename: filename
        """
        try:
            process_record = FilesProgressDDB.get(filename)
            #logger.info('increment_processed with record', extra={'data': process_record})
            if process_record.rows_processed < process_record.rows_total_processable:
                process_record.update(
                    actions=[
                        FilesProgressDDB.rows_processed.add(1)
                    ]
                )
            else:
                logger.error('rows_processed counter exceeded expected. This shouldnt happen.')

        except Exception as e:
            logger.error('error while increment_processed counter', extra={'data': str(e)})

    def increment_failed(self, filename):
        """
        Increment rows_processed counter

        :param filename: filename
        """
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.rows_failed.add(1)
                ]
            )
        except Exception as e:
            logger.error('error while increment_processed counter', extra={'data': str(e)})

    def increament_email_sent(self, filename):
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.total_emails_sent.add(1)
                ]
            )
        except Exception as e:
            logger.error('error while increament_email_sent counter', extra={'data': str(e)})

    def increament_sms_sent(self, filename):
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.total_sms_sent.add(1)
                ]
            )
        except Exception as e:
            logger.error('error while increament_sms_sent counter', extra={'data': str(e)})

    def increament_mail_sent(self, filename):
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.total_mail_sent.add(1)
                ]
            )
        except Exception as e:
            logger.error('error while increament_mail_sent counter', extra={'data': str(e)})

    def increament_page_created(self, filename, page_count):
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.total_page_created.add(page_count),
                    FilesProgressDDB.total_duplex_page_created.add(math.ceil(page_count / 2.))
                ]
            )
        except Exception as e:
            logger.error('error while increament_page_created counter', extra={'data': str(e)})

    def increament_mail_sent_page_created(self, filename, page_count):
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.total_mail_sent.add(1),
                    FilesProgressDDB.total_page_created.add(page_count),
                    FilesProgressDDB.total_duplex_page_created.add(math.ceil(page_count / 2.))
                ]
            )
        except Exception as e:
            logger.error('error while increament_page_created counter', extra={'data': str(e)})

    '''def increment_invalid(self, filename, count):
        """
        Increment rows_processed counter
        Note this function need to run after the row appears in DDB

        :param filename: filename
        """
        try:
            process_record = FilesProgressDDB.get(filename)
            process_record.update(
                actions=[
                    FilesProgressDDB.rows_invalid.add(count)
                ]
            )
        except Exception as e:
            logger.error('error while increment_processed counter for filename {}'.format(filename), extra={'data': str(e)})
'''

Progress = namedtuple('Progress', ['lut', 'filename1', 'file_progress1', 'filenameL6', 'file_progressL6', 'filenameG6', 'file_progressG6'])

class ProgressError(Exception): pass

def load_progress(filename: str, is_multi: bool) -> Progress:
    filename1 = filename

    file_progress1 = FilesProgressDDB.get(filename)
    if file_progress1 is None:
        logger.error(f'Cannot find file progress record for {filename}')
        raise ProgressError

    lut = MetadataLUTDDB.get(CommonFunction.get_prefix_from_filename(filename))
    if lut is None:
        logger.error(f'Cannot find LUT for {filename}')
        raise ProgressError

    filenameL6 = None
    filenameG6 = None
    file_progressL6 = None
    file_progressG6 = None

    if is_multi:
        filenameL6, filenameG6 = Multi.filenames(filename)

        file_progressL6 = FilesProgressDDB.get(filenameL6)
        if file_progressL6 is None:
            logger.error(f'Cannot find file progress record for {filenameL6}')
            raise ProgressError

        file_progressG6 = FilesProgressDDB.get(filenameG6)
        if file_progressG6 is None:
            logger.error(f'Cannot find file progress record for {filenameG6}')
            raise ProgressError

    return Progress(lut, filename1, file_progress1, filenameL6, file_progressL6, filenameG6, file_progressG6)
