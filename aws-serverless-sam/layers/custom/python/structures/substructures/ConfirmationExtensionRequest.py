from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class ConfirmationExtensionRequest(Structure):
    product_family_name = PRODUCT_FAMILY_CONFIRMATION_EXTENSION_REQUEST
    supported_product_codes = ['PNDL1332']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'RecSeqNumber': [9, 2],
            'Name': [11, 27],
            'Post_Address_1': [38, 26],
            'Post_Address_2': [64, 26],
            'Post_Address_3': [90, 24],
            'Salutation': [114, 49],
            'StartDate': [163, 13],
            'EndDate': [176, 13],
            'RecptNumber': [189, 9],
            'SuspLength': [198, 2]
        }
        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[13:24])

        # BR3
        if number_of_rows != len(lines):
            logger.error('failed parsing, total no of records does not match expected records', extra={'data': {
                'total_records': str(len(lines)),
                'expected_records': str(number_of_rows)
            }})
            trailer_row['ClientId'] = " "
            trailer_row['Name'] = " "
            trailer_row['record_no'] = int(len(lines)) + 1

            self.report_invalid_row(trailer_row,
                                    reason='Detail records does not match the total record count in the trailer record',
                                    position_data=[14, 11])
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

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()
                row['Salutation'] = row['Salutation'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format dates
                row['StartDate'] = self.get_formatted_date(row['StartDate'])
                row['EndDate'] = self.get_formatted_date(row['EndDate'])

                # trim zeroes
                row['SuspLength'] = self.trim_zeroes(row['SuspLength'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                # email subject
                row['EmailSubject'] = self.email_subject(row)

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # invalid record if client no is invalid
            if not row[Structure.profile_table_mappings['client_id']]:
                self.report_invalid_row(row,
                                        reason='Invalid licence number - blank field',
                                        position_data=headers[Structure.profile_table_mappings['client_id']])
                return False
        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

    def email_template(self) -> str:
        return 'generic/template1.html'

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        return 'Request received for extended demerit point period'

    def history_title(self, row) -> str:
        return 'Your request to extend your demerit point period has been received.'

    def correspondence_metadata(self, row) -> str:
        return '-'
