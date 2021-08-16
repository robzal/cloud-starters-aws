from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class WriteOff(Structure):

    product_family_name = PRODUCT_FAMILY_WRITE_OFF
    supported_product_codes = ['Writerep', 'Writerephailonly', 'Writesta', 'Writerephailplus']

    def parse(self, lines: list):
        headers = {
            'Serial': [1, 8],
            'Registration_No': [9, 6],
            'Fill1': [15, 2],
            'WriteOffType': [17, 1],
            'DateWriteOff': [18, 8],
            'VinNo': [26, 20],
            Structure.profile_table_mappings['client_id']: [46, 9],
            'Surname': [55, 35],
            'Name': [90, 11],
            'SecondName': [101, 9],
            'Post_Address_1': [112, 30],
            'Post_Address_2': [142, 30],
            'Post_Suburb': [172, 30],
            'PostCode': [202, 4],
            'CancelDate': [206, 8],
            'Post_State': [214, 3],
            'presort': [217, 3],
            'Fill2': [220, 1],
            'JulianDay': [221, 3],
            'Fill3': [224, 1],
            'Count': [225, 6]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[3:9])

        if number_of_rows != len(lines):
            logger.error('failed parsing, total no of records does not match expected records', extra={'data': {
                'total_records': str(len(lines)),
                'expected_records': str(number_of_rows)
            }})
            trailer_row['ClientId'] = " "
            trailer_row['Name'] = " "
            trailer_row['record_no'] = int(len(lines)) + 1

            self.report_invalid_row(trailer_row,
                                    reason='Detail records does not match the total record count in the trailer record',
                                    position_data=[4, 6])
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

                filename = _line['raw_filename']
                product_code = self.get_product_code_from_filename(filename)

                # default onsert options
                row['OnsertRequired'] = 1
                row['OnsertMergeAtStart'] = 0
                row['OnsertsToMerge'] = ["WrittenOffInfo.pdf"]

                # if hail only product, mark writeoff type as H and mark onsert as not required
                # if hail plus other product, mark writeoff type as P
                if product_code.lower() == 'Writerephailonly'.lower():
                    row['WriteOffType'] = "H"
                    row['OnsertRequired'] = 0
                elif product_code.lower() == 'Writerephailplus'.lower():
                    row['WriteOffType'] = "P"

                # generate derived name
                name_parts = [row['Name'], row['SecondName'], row['Surname']]
                derived_name = ' '.join(x.strip().title() for x in name_parts if x.strip())
                row['DerivedName'] = derived_name

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                # format cancel date
                row['CancelDate'] = self.get_formatted_date(row['CancelDate'])

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

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # invalid record if registration no is invalid
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid licence number - blank field',
                                        position_data=headers['Registration_No'])
                return False

            # invalid record if vin no is invalid
            if not row['VinNo']:
                self.report_invalid_row(row,
                                        reason='Invalid vin number - blank field',
                                        position_data=headers['VinNo'])
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

    def history_title(self, row: dict) -> str:
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
