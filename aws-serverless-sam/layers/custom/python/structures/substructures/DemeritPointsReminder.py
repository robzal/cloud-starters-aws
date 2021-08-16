from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DemeritPointsReminder(Structure):
    product_family_name = PRODUCT_FAMILY_DEMERIT_POINTS_REMINDER
    supported_product_codes = ['PNDL1530']

    def parse(self, lines: list) -> list:

        headers = {
            'PrintDate': [1, 13],
            Structure.profile_table_mappings['client_id']:[14, 9],
            'Name': [23, 27],
            'Post_Address_1': [50, 27],
            'Post_Address_2': [77, 27],
            'Post_Address_3': [104, 24],
            'OptIssueDate': [128, 13],
            'SusPeriodDur': [141, 4],
            'SuspenCode': [145, 1],
            'ReplyByDate': [146, 13],
            'SuspenSDate': [159, 13],
            'SuspenEDate': [172, 13],
            'LicRetDate': [185, 13],
            'PIN': [198, 4],
            'Salutation': [202, 49],
            'SuspLength': [251, 2]
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
                row['OptIssueDate'] = self.get_formatted_date(row['OptIssueDate'])
                row['ReplyByDate'] = self.get_formatted_date(row['ReplyByDate'])
                row['SuspenSDate'] = self.get_formatted_date(row['SuspenSDate'])
                row['SuspenEDate'] = self.get_formatted_date(row['SuspenEDate'])

                # trim zeroes
                row['SuspLength'] = self.trim_zeroes(row['SuspLength'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

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
        return 'generic/template1.html'

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        return 'Reminder to extend your demerit point period'

    def history_title(self, row: dict) -> str:
        return "Don't forget, your election to extend your demerit period is required by {}".format(row['ReplyByDate'])

    def correspondence_metadata(self, row) -> str:
        return '-'
