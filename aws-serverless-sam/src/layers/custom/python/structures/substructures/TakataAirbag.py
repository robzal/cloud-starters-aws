from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
import csv
from datetime import datetime


class TakataAirbag(Structure):
    product_family_name = PRODUCT_FAMILY_TAKATA
    supported_product_codes = ['EDSOAP', 'EDS0AP']

    def parse(self, lines: list) -> list:

        headers = [
            'VinNo',
            'EngineNumber',
            'Registration_No',
            'RegoExpiryDate',
            'RegoStatus',
            'WriteoffStatus',
            'WriteoffDate',
            'StolenStatus',
            'DateStolen',
            'Surname',
            'Name',
            'CompanyName',
            'ResAddress1',
            'ResAddress2',
            'ResSuburb',
            'ResState',
            'ResPostCode',
            'Post_Address_1',
            'Post_Address_2',
            'Post_Suburb',
            'Post_State',
            'PostCode',
            'EmailAddress',
            'ContactNo',
            'Make',
            'Title'
        ]

        lines.pop(0)  # remove header row
        rows = []
        for i, _line in enumerate(lines):
            line = _line['raw_row']
            _line['record_no'] = i
            try:
                if line[0:17] != line[24:41]:
                    logger.info('Skipping row, NO VIN match/details found for VIN : {}'.format(line[0:17]))
                    continue

                result = csv.DictReader(line[24:].splitlines(), fieldnames=headers, delimiter='|')
                data_dict = dict(list(result)[0])

                row = {**data_dict, **_line}

                # convert name to capital case
                # name for Metadata report
                if row['CompanyName']:
                    row['FullName'] = row['CompanyName'].title()
                else:
                    name = [row['Name'], row['Surname']]
                    row['FullName'] = ' '.join(x.title() for x in name if x)

                # generate address line3
                row['Post_Address_3'] = self.get_address_line3(
                    row['Post_Suburb'],
                    row['Post_State'],
                    row['PostCode'])
                row['ResAddress3'] = self.get_address_line3(
                    row['ResSuburb'],
                    row['ResState'],
                    row['ResPostCode'])

                # format address lines
                formatted_addresses = self.get_formatted_address(
                    [row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                formatted_addresses = self.get_formatted_address(
                    [row['ResAddress1'], row['ResAddress2'], row['ResAddress3']])
                row['ResAddress1'] = formatted_addresses[0]
                row['ResAddress2'] = formatted_addresses[1]
                row['ResAddress3'] = formatted_addresses[2]

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        pass

    def email_template(self) -> str:
        pass

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        pass

    def history_title(self, row) -> str:
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
