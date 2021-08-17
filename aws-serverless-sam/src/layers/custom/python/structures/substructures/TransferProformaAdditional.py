from structures.Structure import Structure
from structures.ProductFamily import *


class TransferProformaAdditional(Structure):
    product_family_name = PRODUCT_FAMILY_TRANSFER_PROFORMA_ADDITIONAL
    supported_product_codes = ['PVRT2050']

    def parse(self, lines: list) -> list:

        headers = {
            'PrintControlCode1': [1, 1],
            'PrintData': [2, 131]
        }

        rows = []
        counter = 15
        first_line_populated = False

        for i, _line in enumerate(lines):
            line = _line['raw_row']
            _line['record_no'] = i
            try:
                data_dict = {
                    header: line[pad[0] - 1: (pad[0] - 1) + pad[1]] for header, pad in headers.items()
                }
                row = {**data_dict, **_line}

                if row['PrintControlCode1'] == '1':
                    first_line_populated = False
                    if counter == 0:
                        if 'END OF PROFORMA PRINTING' in row['PrintData']:
                            break
                        else:
                            row['ContentToPrint'] = []
                            if row['PrintData'].strip():
                                row['ContentToPrint'].append(row['PrintData'])
                                if not first_line_populated:
                                    first_line_populated = True
                            row['OnsertRequired'] = 1
                            row['OnsertMergeAtStart'] = 0
                            row['OnsertsToMerge'] = ["Page1Onsert.pdf"]
                            rows.append(row)
                    else:
                        counter = counter - 1
                else:
                    if len(rows) > 0:
                        if counter == 0:
                            if 'END OF PROFORMA PRINTING' in row['PrintData']:
                                break
                            else:
                                if row['PrintData'].strip():
                                    rows[-1]['ContentToPrint'].append(row['PrintData'])
                                    if not first_line_populated:
                                        first_line_populated = True
                                else:
                                    if first_line_populated:
                                        rows[-1]['ContentToPrint'].append('\n')

            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        processed_rows = self.split_content(rows)
        return processed_rows

    def split_content(self, rows: list) -> list:
        for row in rows:
            row['FullName'] = "{}{}".format(row['ContentToPrint'][6].strip()[:41].strip(), row['ContentToPrint'][7].strip()[:41].strip())
            row['Post_Address_1'] = row['ContentToPrint'][8].strip()[:41]
            row['Post_Address_2'] = row['ContentToPrint'][9].strip()[:41]
            row['Post_Address_3'] = row['ContentToPrint'][10].strip()[:41]
            row['Registration_No'] = row['ContentToPrint'][10].strip()[-11:-5]
        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        pass

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
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
