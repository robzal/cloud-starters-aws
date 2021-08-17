from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime


class RefundEligibility(Structure):
    product_family_name = PRODUCT_FAMILY_REFUND_ELIGIBILITY
    supported_product_codes = ['PVRI2016', 'PVRI2031']

    def parse(self, lines: list) -> list:

        headers = {
            'LetterID': [1, 1],
            'Name': [2, 40],
            'Post_Address_1': [42, 40],
            'Post_Address_2': [82, 40],
            'Post_Address_3': [122, 40],
            'Post_Address_4': [162, 40],
            'Registration_No': [202, 10],
            'Make': [212, 6],
            'Type': [218, 6],
            'Date_A': [224, 10],
            'Filler 1': [234, 51],
            'Filler 2': [285, 48]
        }

        header_row = lines.pop(0)
        header = header_row['raw_row']
        number_of_rows = int(header[139:147])

        if number_of_rows != len(lines):
            logger.error('failed parsing, total no of records does not match expected records', extra={'data': {
                'total_records': str(len(lines)),
                'expected_records': str(number_of_rows)
            }})
            header_row['ClientId'] = " "
            header_row['Name'] = " "
            header_row['record_no'] = 0

            self.report_invalid_row(header_row,
                                    reason='Detail records does not match the total record count in the header record',
                                    position_data=[140, 8])
            return []

        rows = []
        for i, _line in enumerate(lines):
            line = _line['raw_row']
            _line['record_no'] = i
            try:
                data_dict = {
                    header: line[pad[0] - 1: (pad[0] - 1) + pad[1]].strip() for header, pad in headers.items()
                }
                row = {**data_dict, **_line}

                if not self.validate_business_rules(row, headers):
                    continue

                # convert name to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format dates
                row['Date_A'] = self.get_formatted_date(row['Date_A'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3'], row['Post_Address_4']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]
                row['Post_Address_4'] = formatted_addresses[3]

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # invalid record if client no is invalid
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid registration number - blank field',
                                        position_data=headers['Registration_No'])
                return False
        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

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

    def history_title(self, row: dict) -> str:
        # not applicable as this correspondence doesnt have client id
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
