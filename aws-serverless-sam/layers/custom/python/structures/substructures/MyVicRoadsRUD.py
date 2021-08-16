from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class MyVicRoadsRUD(Structure):
    product_family_name = PRODUCT_FAMILY_MYVICROADS_RUD
    supported_product_codes = ['PNDL1282']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 9],
            'Filler1': [10, 1],
            'Name': [11, 22],
            'Filler2': [33, 1],
            'Postal RUD Indicator': [34, 1],
            'Filler3': [35, 1],
            'Residential RUD Indicator': [36, 1],
            'Filler4': [37, 1],
            Structure.profile_table_mappings['email']: [38, 60],
            'Filler5': [98, 1],
            Structure.profile_table_mappings['phone']: [99, 19]
        }
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

                # output channel mappings
                row = self.user_output_channels_mapping(row)

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # email subject
                row['EmailSubject'] = self.email_subject(row)

                # output channel settings for email
                row['Mail_Required'] = 'N'
                row['Email_Required'] = 'N'
                row['SMS_Required'] = 'N'

                if row['Email_Rqd_Ind'] == 'Y':
                    row['Email_Required'] = 'Y'

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
        return '{}/email-template.html'.format(self.product_family_name)

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        return "Update your postal address to receive important letter"

    def history_title(self, row: dict) -> str:
        return 'We were unable to mail you an important letter. Please update your postal address.'

    def correspondence_metadata(self, row) -> str:
        return '-'
