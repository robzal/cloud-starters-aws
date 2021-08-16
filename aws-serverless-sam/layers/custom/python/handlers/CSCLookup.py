from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from botocore.session import Session
from awslogger import logger
import os

DDB_CSC_LOOKUP_NAME = os.environ["DDB_CSC_LOOKUP_NAME"]


# Have you updated IngestCSC.py?
class CSCLookupDDB(Model):
    class Meta:
        table_name = DDB_CSC_LOOKUP_NAME
        region = Session().get_config_variable("region")

    postcode = UnicodeAttribute(hash_key=True)
    csc_name = UnicodeAttribute()
    csc_address_1 = UnicodeAttribute()
    csc_address_2 = UnicodeAttribute(null=True)
    csc_address_3 = UnicodeAttribute(null=True)


def get_closest_csc(postcode: str) -> str:
    """
    Return closest csc from postcode
    :param postcode:
    :return:
    """
    try:
        csc_information = CSCLookupDDB.get(postcode)
        csc_information = {
            "postcode": csc_information.postcode,
            "csc_name": csc_information.csc_name,
            "csc_address_1": csc_information.csc_address_1,
            "csc_address_2": csc_information.csc_address_2,
            "csc_address_3": csc_information.csc_address_3,
        }
    except Exception as e:
        logger.error("error while get_closest_csc", extra={"data": str(e)})
        csc_information = None

    return csc_information

class CSCLookup(object):
    def load_csc_record(self, row: list):

        logger.info(row)
        postcode = row[0]
        try:
            csc_lut = CSCLookupDDB.get(postcode)
            logger.info('{} found'.format(postcode))
        except CSCLookupDDB.DoesNotExist:
            csc_lut = CSCLookupDDB(postcode)
            logger.info('{} not found'.format(postcode))

        i=1
        csc_lut.csc_name = row[i]; i+=1
        csc_lut.csc_address_1 = row[i]; i+=1
        #optional fields
        try:
            csc_lut.csc_address_2 = row[i]; i+=1
        except:
            pass
        try:
            csc_lut.csc_address_3 = row[i]; i+=1
        except:
            pass

        csc_lut.save()

    def delete_csc_record(self, postcode: str):
        try:
            csc_lut = CSCLookupDDB.get(postcode)
            logger.info('Postcode {} found. Deleting Now.'.format(postcode))
            csc_lut.delete()
        except CSCLookupDDB.DoesNotExist:
            logger.info('{} not found.'.format(postcode))
        except Exception as error:
            logger.info('Error Deleting Postcode {}'.format(postcode))
            logger.info(str(error))
