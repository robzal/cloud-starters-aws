from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, 
    UTCDateTimeAttribute,JSONAttribute,BinaryAttribute,BooleanAttribute
)
from botocore.session import Session
from awslogger import logger
import os

DDB_METADATA_LUT_NAME = os.environ['DDB_METADATA_LUT_NAME']

# Have you updated IngestLUT.py?
class MetadataLUTDDB(Model):
    class Meta:
        table_name = DDB_METADATA_LUT_NAME
        region = Session().get_config_variable('region')

    product_prefix = UnicodeAttribute(hash_key=True)
    product_code = UnicodeAttribute()
    product_description = UnicodeAttribute()
    print_mode = UnicodeAttribute()
    hopper_1 = UnicodeAttribute()
    hopper_2 = UnicodeAttribute()
    hopper_3 = UnicodeAttribute()
    hopper_4 = UnicodeAttribute()
    hopper_5 = UnicodeAttribute()
    hopper_6 = UnicodeAttribute()
    hopper_7 = UnicodeAttribute()
    hopper_8 = UnicodeAttribute()
    envelop = UnicodeAttribute()
    stock = UnicodeAttribute()
    CorrespondenceSetting = UnicodeAttribute()
    important_correspondence = UnicodeAttribute()
    header_bytes = UnicodeAttribute()
    footer_bytes = UnicodeAttribute()
    record_length = UnicodeAttribute()
    docType_enabled = UnicodeAttribute()    

def prefix_to_code(product_prefix: str) -> str:
    '''
    Return product_code from product_prefix
    :param product_prefix:
    :return:
    '''
    try:
        lut = MetadataLUTDDB.get(product_prefix)
        product_code = lut.product_code
    except Exception as e:
        logger.error('error while prefix_to_code', extra={'data': str(e)})
        product_code = None

    return product_code

class MetadataLUT(object):
    def load_metadata_record(self, row: list):

        logger.info(row)
        product_prefix = row[0].split('_')[0].split('.')[0].split()[0]
        try:
            lut = MetadataLUTDDB.get(product_prefix)
            logger.info('{} found'.format(product_prefix))
        except MetadataLUTDDB.DoesNotExist:
            lut = MetadataLUTDDB(product_prefix)
            logger.info('{} not found'.format(product_prefix))

        i=0
        lut.product_file = row[i]; i+=1
        lut.product_code = row[i].split()[0]; i+=1
        lut.product_description = row[i]; i+=1
        lut.envelop = row[i];i += 1
        lut.print_mode = row[i]; i+=1
        lut.stock = row[i];i += 1
        lut.hopper_1 = row[i]; i+=1
        lut.hopper_2 = row[i]; i+=1
        lut.hopper_3 = row[i]; i+=1
        lut.hopper_4 = row[i]; i+=1
        lut.hopper_5 = row[i]; i+=1
        lut.hopper_6 = row[i]; i+=1
        lut.hopper_7 = row[i]; i+=1
        lut.hopper_8 = row[i]; i+=1
        lut.CorrespondenceSetting = row[i].split()[0]; i+=1
        lut.important_correspondence = row[i].split()[0]; i+=1
        lut.header_bytes = row[i]; i+=1
        lut.footer_bytes = row[i]; i+=1
        lut.record_length = row[i]; i+=1
        lut.docType_enabled = row[i].split()[0]; i+=1
        lut.save()

    def delete_metadata_record(self, product_prefix: str):
        try:
            meta_lut = MetadataLUTDDB.get(product_prefix)
            logger.info('Product {} found. Deleting Now.'.format(product_prefix))
            meta_lut.delete()
        except MetadataLUTDDB.DoesNotExist:
            logger.info('{} not found.'.format(product_prefix))
        except Exception as error:
            logger.info('Error Deleting Product {}'.format(product_prefix))
            logger.info(str(error))

    def allow_file_process(self, filename: str):

        # these files come from DXC that arent to be processed
        files_to_ignore = ['PNDL148G_DLIP234','pndl2650.trg','pndl2670.trg','LicOpRem.trg','LicOpRen.trg']
        found = [filename if filename.startswith(f) else None for f in files_to_ignore]
        if filename in found:
            return False
        else:
            return True

    def allow_file_rename(self, filename: str):

        # these files come from DXC and need unique suffix added to filename as the filenames are reused every week
        files_to_rename = ['pndl2650.dat','pndl2670.dat','LicOpRem.dat','LicOpRen.dat', 'PNDL8890_Rider_Permit_Extension_Letter.DAT']
        if filename in files_to_rename:
            return True
        else:
            return False