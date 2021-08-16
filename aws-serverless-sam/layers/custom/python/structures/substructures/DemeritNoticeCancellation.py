from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DemeritPointsReminder(Structure):
    product_family_name = PRODUCT_FAMILY_DEMERIT_NOTICE_CANCELLATION
    supported_product_codes = ['PNDL4965']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'DateIssue': [9, 17],
            'Name': [26, 27],
            'Post_Address_1': [53, 27],
            'Post_Address_2': [80, 27],
            'Post_Address_3': [107, 24],
            'Salutation': [131, 49],
            'Reversed_TIN_Number': [180, 10],
            'TIN_Date': [190, 8],
            'Offence_Short_Desc': [198, 25],
            'Offence_Long_Desc': [223, 120],
            'Option_Notice_Date': [343, 8]
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

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()
                row['Salutation'] = row['Salutation'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format dates
                row['DateIssue'] = self.get_formatted_date(row['DateIssue'])
                row['TIN_Date'] = self.get_formatted_date(row['TIN_Date'])
                row['Option_Notice_Date'] = self.get_formatted_date(row['Option_Notice_Date'])

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
        return 'Cancellation of demerit points notice'

    def history_title(self, row: dict) -> str:
        return 'Your are now below the demerit point limit. Please review for next steps.'

    def correspondence_metadata(self, row) -> str:
        return '-'
