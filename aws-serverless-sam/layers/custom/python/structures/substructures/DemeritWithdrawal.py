from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DemeritWithdrawal(Structure):
    product_family_name = PRODUCT_FAMILY_DEMERIT_NOTICE_WITHDRAWAL
    supported_product_codes = ['PNDL148E', 'PNDL148F', 'PNDL148M']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'DateIssue': [9, 8],
            'Filler': [17, 8],
            'Name': [25, 27],
            'Post_Address_1': [52, 27],
            'Post_Address_2': [79, 27],
            'Post_Address_3': [106, 24],
            'DateNotice': [130, 8],
            'Salutation': [138, 49]
        }
        rows = []
        for i, _line in enumerate(lines):
            line = _line['raw_row']
            _line['record_no'] = i
            try:
                data_dict = {
                    header: line[pad[0] - 1: (pad[0] - 1) + pad[1]].strip() for header, pad in headers.items()
                }
                filename = _line['raw_filename']
                data_dict['FilePrefix'] = self.get_prefix_from_filename(filename)

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
                row['DateIssue'] = self.get_formatted_date(row['DateIssue'])
                row['DateNotice'] = self.get_formatted_date(row['DateNotice'])

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
        if row['FilePrefix'] == 'PNDL148E':
            return 'Cancellation of demerit points notice'
        elif row['FilePrefix'] == 'PNDL148F':
            return 'Cancellation of disqualification notice of your demerit points'
        elif row['FilePrefix'] == 'PNDL148M':
            return 'Cancellation of suspension notice of your demerit points'
        return 'You have a message'

    def history_title(self, row: dict) -> str:
        if row['FilePrefix'] == 'PNDL148E':
            return 'Your prior demerit points notice has been cancelled.'
        elif row['FilePrefix'] == 'PNDL148F':
            return 'Your prior disqualification notice of your demerit points has been cancelled.'
        elif row['FilePrefix'] == 'PNDL148M':
            return 'Your prior suspension notice of your demerit points has been cancelled.'
        return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
