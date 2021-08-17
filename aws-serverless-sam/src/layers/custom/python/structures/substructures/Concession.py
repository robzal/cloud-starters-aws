from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class Concession(Structure):

    product_family_name = PRODUCT_FAMILY_CONCESSION
    supported_product_codes = ['inelgconc']

    def parse(self, lines: list):
        headers = {
            Structure.profile_table_mappings['client_id']: [1, 9],
            'Name': [10, 26],
            'Post_Address_1': [36, 26],
            'Post_Address_2': [62, 26],
            'Post_Suburb': [88, 20],
            'Post_State': [108, 3],
            'PostCode': [111, 4],
            'ExpiryDate': [115, 8],  # reduced length by 2 characters because of presence of NUL char in date
            'Registration_No': [123, 10],  # reduced start position of all subsequent fields by 2 hence.
            'ManagerName': [133, 26],
            'ManagerTitle': [159, 55],
            'FirstNamePrint': [214, 22],
            'PostalNSP': [236, 3]
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

                # convert name to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # generate address line3
                row['Post_Address_3'] = self.get_address_line3(
                    row['Post_Suburb'],
                    row['Post_State'],
                    row['PostCode'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                # format expirydate
                row['ExpiryDate'] = self.get_formatted_date(row['ExpiryDate'])

                # get current date
                row['SystemDate'] = self.get_current_system_date()

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
