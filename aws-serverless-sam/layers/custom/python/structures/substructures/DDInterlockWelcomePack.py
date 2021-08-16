from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DDInterlockProgram(Structure):
    product_family_name = PRODUCT_FAMILY_DD_INTERLOCK_WELCOME_PACK
    supported_product_codes = ['PNDL1321']

    def parse(self, lines: list) -> list:

        headers = {
            'DetailRecordType': [1, 1],
            Structure.profile_table_mappings['client_id']: [2, 9],
            'Title': [11, 15],
            'GivenName': [26, 22],
            'Surname': [48, 40],
            'NameLine2': [88, 30],
            'Post_Address_1': [118, 30],
            'Post_Address_2': [148, 30],
            'Post_Suburb': [178, 30],
            'Post_State': [208, 3],
            'PostCode': [211, 4],
            'Salutation': [215, 30],
            'InterLockDurationText': [245, 30],
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[1:7])

        # BR3
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

                # convert name and salutation to capital case
                name = [row['Title'], row['GivenName'], row['Surname']]
                row['Name'] = ' '.join(x.title() for x in name if x)

                salutation = [row['GivenName'], row['Surname']]
                row['Salutation'] = ' '.join(x.title() for x in salutation if x)

                # name for Metadata report
                row['FullName'] = row['Salutation']

                # onsert options
                row['OnsertRequired'] = 1
                row['OnsertMergeAtStart'] = 0

                row['OnsertsToMerge'] = ["KeyGuidelines.pdf"]

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
        return 'Information about being on the Victorian Alcohol Interlock Program'

    def history_title(self, row: dict) -> str:
        return 'Information about being on the Victorian Alcohol Interlock Program'

    def correspondence_metadata(self, row) -> str:
        return '-'
