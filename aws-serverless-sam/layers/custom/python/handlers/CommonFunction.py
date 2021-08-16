import re
import os
import pytz
from datetime import datetime

def today(format: str='%Y-%m-%d %H:%M') -> str:
    """
    Today's date in approved format, do NOT change this
    :return: today's date
    """
    return today_now().strftime(format)

def today_now():
    """
    Today's date time in AU or specified timezone
    
    :return: today's datetime object
    """

    TZ = os.environ.get('TZ','Australia/Melbourne')
    now = datetime.now(pytz.timezone(TZ))
    return now

def str_to_datetime(strdatetime: datetime, format:str='%Y-%m-%d %H:%M %z') -> str:
    """
    Convert string datetime to a datetime object
    :return: datetime object
    """
    return datetime.strptime(strdatetime, format)

def unpadded_id(value: str = None) -> str:
    """
    Removes leading zeroes from IDs
    :return: str id
    """

    return re.sub('^0*', '', value)

def is_datetime_or_empty(value: str) -> bool:
    """
    Determine if value is datetime or equals to 0

    :param value: string to compare
    :return: True if value is datetime or eq to 0
    """
    return re.match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}', value) or value == '0'

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

def get_prefix_from_filename(filename: str) -> str:
    """
    Get the product prefix from filename
    """

    return filename.split('_')[0].split('.')[0]

def create_pdf_filename(dat_filename: str, product_code: str, batch_date: datetime, batch_no: int, sequence_number: int) -> str:
    '''
    Create filename to be used by PDF Files
    '''
    return "{}_{}.pdf".format(base_filename(dat_filename, product_code, batch_date, batch_no), sequence_number)

def create_metadata_filename(dat_filename: str, product_code: str, batch_date: str, batch_no: int) -> str:
    '''
    Create filename to be used by Metadata Report
    '''
    return "{}_Meta.csv".format(base_filename(dat_filename, product_code, batch_date, batch_no))

def create_recon_filename(dat_filename: str, product_code: str, batch_date: str, batch_no: int) -> str:
    '''
    Create filename to be used by Recon Report
    '''
    return "{}_Rec.csv".format(base_filename(dat_filename, product_code, batch_date, batch_no))

def create_invalid_filename(dat_filename: str, product_code: str, batch_date: str, batch_no: int) -> str:
    '''
    Create filename to be used by Error Report
    '''
    return "{}_Err.csv".format(base_filename(dat_filename, product_code, batch_date, batch_no))

def create_zip_filename(dat_filename: str, product_code: str, batch_date: str, batch_no: int) -> str:
    '''
    Create filename to be used a dat file's zip archive
    '''
    return "{}.zip".format(base_filename(dat_filename, product_code, batch_date, batch_no))

def base_filename(dat_filename: str,product_code: str, batch_date: str, batch_no: int) -> str:
    '''
    Create base filename to be used by PDF, Meta Report, Recon report, Error report and Zip File
    '''

    filename = "{}_{}_{}".format(product_code, batch_date,batch_no)
    try:
        if dat_filename[-2:] == 'L6':
            filename = "{}_{}_{}_L6".format(product_code, batch_date,batch_no)
        if dat_filename[-2:] == 'G6':
            filename = "{}_{}_{}_G6".format(product_code, batch_date,batch_no)
    except:
        pass

    return filename

def assemble_address(row) -> dict:
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
