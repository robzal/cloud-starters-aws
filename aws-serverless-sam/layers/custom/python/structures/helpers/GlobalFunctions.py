from typing import Optional
from datetime import date
from datetime import datetime
from handlers import MetadataLUT
from handlers.ICRN import ICRN
import re
import pytz
from awslogger import logger


class GlobalFunctions(object):
    @staticmethod
    def is_leap_year(year):
        return year % 4 == 0 and year % 100 != 0 or year % 400 == 0

    @staticmethod
    def state_by_code(postcode: str) -> str:
        """
        Convert postcode to state code

        :param postcode: postcode value
        :return: state code
        """
        if not postcode:
            return ''

        if postcode.startswith('0'):
            if 200 <= int(postcode) <= 299:
                return 'ACT'
            elif 800 <= int(postcode) <= 999:
                return 'NT'

        if (1000 <= int(postcode) <= 2599) or (2620 <= int(postcode) <= 2899) or (2921 <= int(postcode) <= 2999):
            return 'NSW'
        elif (2600 <= int(postcode) <= 2619) or (2900 <= int(postcode) <= 2920):
            return 'ACT'

        if postcode.startswith('5'):
            return 'SA'

        if postcode.startswith('6'):
            return 'WA'

        if postcode.startswith('7'):
            return 'TAS'

        if postcode.startswith('4') or postcode.startswith('9'):
            return 'QLD'

        if postcode.startswith('3') or postcode.startswith('8'):
            return 'VIC'

        return ''

    @staticmethod
    def parse_street_address(street: str) -> Optional[list]:
        pass

    @staticmethod
    def mm_as_digit(month: str) -> int:
        month = month.upper()
        if 'JAN' == month:
            return 1

        if 'FEB' == month:
            return 2

        if 'MAR' == month:
            return 3

        if 'APR' == month:
            return 4

        if 'MAY' == month:
            return 5

        if 'JUN' == month:
            return 6

        if 'JUL' == month:
            return 7

        if 'AUG' == month:
            return 8

        if 'SEP' == month:
            return 9

        if 'OCT' == month:
            return 10

        if 'NOV' == month:
            return 11

        if 'DEC' == month:
            return 12

    @staticmethod
    def get_address_line3(suburb: str, state: str, postcode: str):
        """
        Concatenate state, suburb and postcode to generate address line 3
        """
        address_parts = [suburb, state, postcode]
        address_line_3 = ' '.join(x.strip() for x in address_parts if x.strip())
        if address_line_3:
            return address_line_3
        return ''

    @staticmethod
    def get_formatted_address(address_list: list):
        """
        format address lines, if address3 is empty make address line2 all CAPS else make address line3 all CAPS
        """
        # format address lines
        if any(address_list):
            address_list = [x.title() for x in address_list]
            index = next(len(address_list) - i for i, j in enumerate(reversed(address_list), 1) if j != '')
            address_list[index] = address_list[index].upper()
        return address_list

    @staticmethod
    def get_mailhouse_ref(filename: str, product_code: str):
        """
        get mailhouse reference line i.e. filename + productcode
        """
        if filename and product_code:
            return filename + ' ' + product_code
        return ''

    @staticmethod
    def get_product_code_from_filename(filename: str):
        """
        get product code from file prefix
        """
        # get product code from lookup table
        product_code = MetadataLUT.prefix_to_code(filename.split('_')[0].split('.')[0])

        return product_code

    @staticmethod
    def get_prefix_from_filename(filename: str):
        """
        get product code from file prefix
        """
        return filename.split('_')[0].split('.')[0]

    @staticmethod
    def get_current_system_date():
        """
        get current system date in the format e.g. 07 January 1998
        """
        today = datetime.now(pytz.timezone('Australia/Melbourne'))
        return today.strftime("%d %B %Y")

    @staticmethod
    def get_formatted_date(date_string: str):
        """
        get date formatted as '%d %B %Y'
        """
        fmts = ['%d%m%y', '%d%b%Y', '%d %m %Y', '%d%m%Y', '%Y%m%d', '%d-%m-%y', '%d/%m/%y', '%d/%m/%Y', '%d.%m.%Y',
                '%d\00%m\00%Y', '%d %B %Y', '%dnd %b %Y', '%dnd %B %Y', '%drd %b %Y', '%dst %b %Y', '%dth %b %Y']
        if date_string:
            for fmt in fmts:
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    if date_obj:
                        return date_obj.strftime("%d %B %Y")
                except:
                    continue
        return ''

    @staticmethod
    def get_currency(value: str) -> str:
        """
        get string formatted as currency with decimal places
        :param value:
        :return:
        """
        if value.replace('.', '', 1).isdigit():
            value = value[:-2].lstrip('0') + value[-2:]
            if value != '':
                if '.' not in value:
                    currency = value[:-2] + '.' + value[-2:]
                else:
                    currency = value

                try:
                    currency = '{0:,.2f}'.format(float(currency))
                    return "${}".format(currency)
                except Exception as e:
                    pass
            return ''
        return value

    @staticmethod
    def get_postcode_from_address(address_line: str):
        '''
        extract postcode from address
        :param address_line:
        :return:
        '''
        try:
            return re.findall(r'[0-9]{4}', address_line)[-1]
        except:
            pass
        return ''

    @staticmethod
    def convert_string_to_amount(value: str) -> int:
        is_amount = value.replace('.', '', 1).isdigit()
        if is_amount:
            return int(value)
        return 0

    @staticmethod
    def generate_format_icrn_number(icrn_ref: str, icrn_date: str, icrn_amount: str):
        try:
            if icrn_amount.strip().upper() == 'NIL':
                logger.info ('Substituting in a literal 0 value icrn amount')
                icrn_amount = '000000'
            generated_icrn = ICRN.generate_icrn(icrn_ref, icrn_date, icrn_amount)
            icrn = generated_icrn['icrn']
            if icrn:
                return ' '.join(icrn[i:i + 4] for i in range(0, len(icrn), 4))
        except Exception as e:
            logger.error('failed icrn number generation', extra={'data': str(e)})
            raise Exception('failed icrn number generation - {}'.format(str(e)))

    @staticmethod
    def trim_zeroes(value: str):
        if value:
            value = str(value)
            return '{}{}'.format(value[:-1].lstrip('0'), value[-1:])
        return ''
