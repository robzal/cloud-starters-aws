from structures.Structure import Structure
from structures.ProductFamily import *


class COAAdviceLabel(Structure):
    product_family_name = PRODUCT_FAMILY_COA_ADVICE_LABEL
    supported_product_codes = ['PNDL1320']

    def parse(self, lines: list) -> list:

        headers = {
            'PrintControlCode1': [1, 1],
            'PrintControlCode2': [2, 1],
            'PrintData': [3, 70],
            'PrintDataAddr': [1, 70]
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

                if row['PrintControlCode1'] == '1':
                    count = 0
                    row['ContentToPrint'] = []
                    if row['PrintData']:
                        row['ContentToPrint'].append(row['PrintData'])
                    else:
                        row['ContentToPrint'].append(' ')
                    rows.append(row)
                else:
                    count = count + 1
                    if count in [12, 13, 14]:
                        if row['PrintDataAddr'][1:]:
                            rows[-1]['ContentToPrint'].append(row['PrintDataAddr'][1:])
                        else:
                            rows[-1]['ContentToPrint'].append(' ')
                    else:
                        if row['PrintData']:
                            rows[-1]['ContentToPrint'].append(row['PrintData'])
                        else:
                            rows[-1]['ContentToPrint'].append(' ')

                # name for Metadata report
                row['FullName'] = ''

                # email subject
                row['EmailSubject'] = self.email_subject(row)

            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))
        processed_rows = self.split_content(rows[5:])
        return processed_rows

    def split_content(self, rows: list) -> list:
        for row in rows:
            row['NewAddress_Line1'] = row['ContentToPrint'][12][8:43]
            row['NewAddress_Line2'] = row['ContentToPrint'][13][8:43]
            row['NewAddress_Line3'] = row['ContentToPrint'][14][8:43]
            row['PostalAddress_Line1'] = row['ContentToPrint'][12][43:]
            row['PostalAddress_Line2'] = row['ContentToPrint'][13][43:]
            row['PostalAddress_Line3'] = row['ContentToPrint'][14][43:]

            row['ProcessingDate'] = row['ContentToPrint'][3]
            row['FullName'] = row['ContentToPrint'][4]
            row['Post_Address_1'] = row['ContentToPrint'][5]
            row['Post_Address_2'] = row['ContentToPrint'][6]
            row['Post_Address_3'] = row['ContentToPrint'][7]
            row['PostalHeading'] = row['ContentToPrint'][11]
            row['LicenceDetails'] = row['ContentToPrint'][19:23]
            row['VehicleDetails'] = row['ContentToPrint'][25:37]

            # extract licence number of CAR licence as ClientId, if not take the first licence number in the list
            row[Structure.profile_table_mappings['client_id']] = ''
            if len(row['LicenceDetails']) > 0:
                for licence in row['LicenceDetails']:
                    if 'CAR' in str(licence[9:29]):
                        row[Structure.profile_table_mappings['client_id']] = str(licence[0:9]).lstrip().rstrip()
                        break
                if not row[Structure.profile_table_mappings['client_id']]:
                    row[Structure.profile_table_mappings['client_id']] = str(row['LicenceDetails'][0])[0:9]
            else:
                if not row[Structure.profile_table_mappings['client_id']]:
                    row[Structure.profile_table_mappings['client_id']] = ' '
        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        pass

    def email_template(self) -> str:
        return 'generic/template3.html'

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        return 'We have posted your change of address label'

    def history_title(self, row) -> str:
        return 'Your change of address label has been sent.'

    def correspondence_metadata(self, row) -> str:
        return '-'
