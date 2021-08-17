from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DemeritBreachNotice(Structure):
    product_family_name = PRODUCT_FAMILY_DEMERIT_BREACH_NOTICE
    supported_product_codes = ['PNDL148C']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'IssueDate': [9, 13],
            'Name': [22, 27],
            'Post_Address_1': [49, 26],
            'Post_Address_2': [75, 26],
            'Post_Address_3': [101, 24],
            'OffDate1': [125, 13],
            'TICode1': [138, 4],
            'TINo1': [142, 10],
            'Points1': [152, 2],
            'Filler': [154, 26],
            'Desc1Line1': [180, 40],
            'Desc1Line2': [220, 40],
            'Desc1Line3': [260, 40],
            'Op1SuspTime': [300, 4],
            'SuspStart': [304, 13],
            'Op1SusPnts': [317, 2],
            'Op1Period': [319, 10],
            'Salutation': [329, 49],
            'SuspEnd': [378, 13],
            'P1P2': [391, 2],
            'ProbExtPeriod': [393, 2],
            'E_cond_para': [395, 1],
            'Susp_Status': [396, 1]
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
                row['IssueDate'] = self.get_formatted_date(row['IssueDate'])
                row['OffDate1'] = self.get_formatted_date(row['OffDate1'])
                row['SuspStart'] = self.get_formatted_date(row['SuspStart'])
                row['SuspEnd'] = self.get_formatted_date(row['SuspEnd'])

                # trim zeroes
                row['Op1SusPnts'] = self.trim_zeroes(row['Op1SusPnts'])
                row['Op1Period'] = self.trim_zeroes(row['Op1Period'])
                row['ProbExtPeriod'] = self.trim_zeroes(row['ProbExtPeriod'])
                row['Points1'] = self.trim_zeroes(row['Points1'])

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
        return 'generic/template2.html'

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        return 'Breach of your extended demerit point period'

    def history_title(self, row: dict) -> str:
        return 'Your driver licence is suspended due to a breach in your demerit points. Please review for next steps.'

    def correspondence_metadata(self, row) -> str:
        return '-'
