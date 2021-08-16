from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class FinesReformPlate(Structure):
    product_family_name = PRODUCT_FAMILY_FINES_REFORM_PLATE
    supported_product_codes = ['PVRI1291']

    def parse(self, lines: list) -> list:

        headers = {
            'Detail_record_type': [1, 1],
            'Letter_Code': [2, 8],
            'Sanction_Type': [10, 13],
            Structure.profile_table_mappings['client_id']: [23, 9],
            'Client_Type': [32, 1],
            'Sanction_ID': [33, 20],
            'Name': [53, 30],
            'Name_Line_2': [83, 30],
            'Post_Address_1': [113, 30],
            'Post_Address_2': [143, 30],
            'Post_Suburb': [173, 30],
            'Post_State': [203, 3],
            'PostCode': [206, 4],
            'Salutation': [210, 30],
            'Date_Apply_Or_Delete_Sanction': [240, 8],
            'Registration_Plate_Number': [248, 10],
            'Registration_Plate_Class': [258, 1],
            'Registration_Serial_Number': [259, 8],
            'Registration_Make': [267, 52],
            'Registration_Model': [319, 6],
            'Registration_Status': [325, 20]
        }

        # pop the header
        _ = lines.pop(0)
        # remove the last row
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[1:7]) # double check the indexing

        if number_of_rows != len(lines):
            # report invalid row is number of records does not match
            trailer_row['ClientId'] = " "
            trailer_row['Name'] = " "
            trailer_row['record_no'] = int(len(lines)) + 1
            self.report_invalid_row(trailer_row,
                                    reason='Detail records does not match the total record count in the trailer record',
                                    position_data=[2, 6])
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

                # actual name logic handled in the mail template
                row['Name'] = row['Name'].title()
                row['Name_Line_2'] = row['Name_Line_2'].title()
                row['Salutation'] = row['Salutation'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # handle the address block here
                row['Post_Address_3'] = self.get_address_line3(
                    row['Post_Suburb'],
                    row['Post_State'],
                    row['PostCode']
                )

                # format the address properly
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                # get the current date, which will be the date of issue
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

    # abstract methods required
    def email_template(self) -> str:
        return 'generic/template1.html'

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        pass

    def history_title(self, row: dict) -> str:
        if row['LetterType'] == '110':
            return 'Number plate number {} notice'.format(row['Registration_Plate_Number'])
        elif row['LetterType'] == '120':
            return 'Removal of number plate number {} notice'.format(row['Registration_Plate_Number'])
        return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
