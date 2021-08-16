from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class ProbELetter(Structure):
    product_family_name = PRODUCT_FAMILY_PROB_E_LETTER
    supported_product_codes = ['PNDL1260']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'Issue_Date': [9, 13],
            'Name': [22, 27],
            'Post_Address_1': [49, 26],
            'Post_Address_2': [75, 26],
            'Post_Address_3': [101, 24],
            'Salutation': [125, 49],
            'LicenceOrLearnerPermit': [174, 14],
            'SuspEndDate': [188, 13],
            'P1orP2': [201, 2],
            'ProbExtPeriod': [203, 2],
            'InsertP1P2Date': [205, 13],
            'NewEDate': [218, 13],
            'E_ConditionPara': [231, 1]
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

                # email subject
                row['EmailSubject'] = self.email_subject(row)

                # format dates
                row['Issue_Date'] = self.get_formatted_date(row['Issue_Date'])
                row['SuspEndDate'] = self.get_formatted_date(row['SuspEndDate'])
                row['InsertP1P2Date'] = self.get_formatted_date(row['InsertP1P2Date'])
                row['NewEDate'] = self.get_formatted_date(row['NewEDate'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

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
        return 'How your demerit point suspension affects your licence'

    def history_title(self, row: dict) -> str:
        return 'Your driver licence is suspended due to a demerit point offence. Please review for next steps.'

    def correspondence_metadata(self, row) -> str:
        return '-'
