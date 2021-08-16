from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute
)
from botocore.session import Session
import os
import datetime
import uuid
from awslogger import logger
from datetime import datetime
import handlers.CommonFunction as CommonFunction

# DynamoDB file table name
HISTORY_TABLE = os.environ['DDB_HISTORY_TABLE_NAME']

class FilenameIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "filename_status-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection([
            'filename',
            'ClientId',
            'CompositeKey'
            'date',
            'deliveryStatus'
        ])
    
    filename = UnicodeAttribute(default='0', hash_key=True)
    ClientId = UnicodeAttribute()
    CompositeKey = UnicodeAttribute()
    date = UnicodeAttribute()
    deliveryStatus = UnicodeAttribute()
    deliveryMethod = UnicodeAttribute()

class FileKeyIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "file_compositekey-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection([
            'file_compositekey',
            'ClientId',
            'CompositeKey',
            'deliveryStatus'
        ])
    
    file_compositekey = UnicodeAttribute(hash_key=True)
    ClientId = UnicodeAttribute()
    CompositeKey = UnicodeAttribute()
    deliveryStatus = UnicodeAttribute()


class CorrespondenceMetadataIdx(GlobalSecondaryIndex):
    class Meta:
        index_name = "clientId-date-index"
        read_capacity_units = 2
        write_capacity_units = 1
        projection = IncludeProjection([
            'ClientId',
            'date',
            'CompositeKey'
            'DocumentId',
            'correspondence_metadata'
        ])
    ClientId = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute(range_key=True)
    CompositeKey = UnicodeAttribute()
    DocumentId = UnicodeAttribute()
    correspondence_metadata = UnicodeAttribute()


class CustomerHistoryDDB(Model):
    class Meta:
        table_name = HISTORY_TABLE
        region = Session().get_config_variable('region')

    ClientId = UnicodeAttribute(hash_key=True)
    CompositeKey = UnicodeAttribute(range_key=True)
    date = UnicodeAttribute()
    filename = UnicodeAttribute(default='')
    filename_index = FilenameIdx()

    DocumentId = UnicodeAttribute()
    documentTitle = UnicodeAttribute()
    documenturi = UnicodeAttribute(default='')

    deliveryMethod = UnicodeAttribute()
    deliveryStatus = UnicodeAttribute()

    important_correspondence = UnicodeAttribute(default='false')
    new_correspondence = UnicodeAttribute(default='true')
    read_correspondence = UnicodeAttribute(default='false')

    file_compositekey = UnicodeAttribute(default='')
    file_compositekey_index = FileKeyIdx()
    file_sequence_number = UnicodeAttribute(default='')

    correspondence_metadata = UnicodeAttribute(default='')
    correspondence_metadata_index = CorrespondenceMetadataIdx()


class CustomerHistory(object):
    def initiate_history_creation(self, ClientId: str, date: str, DocumentId: str, documentTitle: str,
                                  documenturi: str, deliveryMethod: str, deliveryStatus: str, readStatus:str,
                                  isImportant:str, fileName:str, fileCompositeKey: str, fileSequenceNumber: str,
                                  correspondenceMetadata: str) -> None:

        composite_uuid = uuid.uuid4()
        # TODO: Add line to validate incoming date format

        composite_key = str(date) + '-' + str(composite_uuid)

        new_correspondence = CustomerHistoryDDB(
            ClientId=CommonFunction.unpadded_id(ClientId),
            CompositeKey=composite_key,
            date=date,
            filename=fileName,
            DocumentId=DocumentId,
            documentTitle=documentTitle,
            documenturi=documenturi,
            deliveryMethod=deliveryMethod,
            deliveryStatus=deliveryStatus,
            important_correspondence=isImportant,
            new_correspondence='true',
            read_correspondence=readStatus,
            file_compositekey=fileCompositeKey,
            file_sequence_number=fileSequenceNumber,
            correspondence_metadata=correspondenceMetadata
        )
        try:
            new_correspondence.save()
        except Exception as e:
            logger.error('failed to execute create_new_correspondence_history', extra={'data': str(e)})

    def load_customer_history_record(self, rows: list):

        logger.info(f'writing batch record {"0"}')
        with CustomerHistoryDDB.batch_write() as batch:
            today_date = CommonFunction.today()
            x = 1
            for row in rows:
                if len(row) > 0:
                    try:
                        cells = row.split("|")

                        clientid = CommonFunction.unpadded_id(cells[0])
                        compositekey = cells[1]
                        userhistory = CustomerHistoryDDB(clientid,compositekey)
                        i=2
                        userhistory.CompositeKey = compositekey
                        userhistory.DocumentId = cells[i]; i+=1
                        userhistory.date = cells[i]; i+=1
                        userhistory.filename = cells[i]; i+=1
                        userhistory.deliveryMethod = cells[i]; i+=1
                        userhistory.deliveryStatus = cells[i]; i+=1
                        userhistory.documentTitle = cells[i]; i+=1
                        userhistory.documenturi = cells[i]; i+=1
                        userhistory.important_correspondence = cells[i]; i+=1
                        userhistory.new_correspondence = cells[i];i += 1
                        userhistory.read_correspondence = cells[i]; i+=1
                        userhistory.file_compositekey = '-'
                        userhistory.file_sequence_number = '-'
                        userhistory.correspondence_metadata = cells[i]
                        batch.save(userhistory)
                    except:
                        logger.info(f'error processing row - {row}')
                x +=1
                if x % 1000 == 0:
                    logger.info(f'writing batch record {str(x)}')
                    today_date = CommonFunction.today()

    def delete_customer_history_record(self, clientid: str):
        try:
            userhistory = CustomerHistoryDDB.query(clientid)
            for r in userhistory:
                logger.info('{} history found. Deleting Key {} Now.'.format(clientid,r.CompositeKey))
                h = CustomerHistoryDDB.get(r.ClientId, r.CompositeKey)
                h.delete()
        except CustomerHistoryDDB.DoesNotExist:
            pass
        except Exception as error:
            logger.info('Error Deleting Customer History {}'.format(clientid))
            logger.info(str(error))

        try:
            clientid = CommonFunction.unpadded_id(clientid)           
            userhistory = CustomerHistoryDDB.query(clientid)
            for r in userhistory:
                logger.info('{} history found. Deleting Key {} Now.'.format(clientid,r.CompositeKey))
                h = CustomerHistoryDDB.get(r.ClientId, r.CompositeKey)
                h.delete()
        except CustomerHistoryDDB.DoesNotExist:
            pass
        except Exception as error:
            logger.info('Error Deleting Customer History {}'.format(clientid))
            logger.info(str(error))

    def approve_history_for_file(self, filename:str, deliveryMethod:str = 'ALL'):

        keys = []
        for history_index_item in CustomerHistoryDDB.filename_index.query(filename):
            if history_index_item.deliveryStatus != 'SENT' and (history_index_item.deliveryMethod == deliveryMethod or deliveryMethod =='ALL'):
                keys.append(history_index_item)

        if keys:
            logger.info('We have {} history records to mark as delivered for file - {}'.format(len(keys), filename))
            x = 1
            for key in keys:
                try:
                    history_item = CustomerHistoryDDB.get(key.ClientId, key.CompositeKey)
                    history_item.deliveryStatus = 'SENT'
                    if history_item.correspondence_metadata is None or history_item.correspondence_metadata == '':
                        history_item.correspondence_metadata = '-'
                    history_item.save()
                except:
                    logger.error(f'error updating row {key.ClientId}- {key.CompositeKey}')

                x +=1
                if x % 100 == 0:
                    logger.info(f'updating batch history record {str(x)} as delivered')

    def approve_history_for_key(self, compositekey:str):

        keys = []
        for history_index_item in CustomerHistoryDDB.file_compositekey_index.query(compositekey):
            if history_index_item.deliveryStatus != 'SENT':
                keys.append(history_index_item)

        if keys:
            logger.info('We have {} history records to mark as delivered for key - {}'.format(len(keys), compositekey))
            for key in keys:
                logger.info('Marking history record {} as sent'.format(key.CompositeKey))
                history_item = CustomerHistoryDDB.get(key.ClientId, key.CompositeKey)
                history_item.deliveryStatus = 'SENT'
                if history_item.correspondence_metadata is None or history_item.correspondence_metadata == '':
                    history_item.correspondence_metadata = '-'
                history_item.save()

    def delete_history_for_file(self, filename:str):

        keys = []
        for history_index_item in CustomerHistoryDDB.filename_index.query(filename):
            keys.append(history_index_item)

        logger.info('We have {} history records to delete for file - {}'.format(len(keys), filename))

        with CustomerHistoryDDB.batch_write() as batch:
            x = 1
            for key in keys:
                try:
                    history = CustomerHistoryDDB(key.ClientId, key.CompositeKey)
                    batch.delete(history)
                except:
                    logger.error(f'error deleting row {key.ClientId}- {key.CompositeKey}')
                x +=1
                if x % 1000 == 0:
                    logger.info(f'deleting batch record {str(x)}')

