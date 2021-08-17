from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DDInterlockProgram(Structure):
    product_family_name = PRODUCT_FAMILY_DD_INTERLOCK_IIC
    supported_product_codes = ['PNDL1655']

    def parse(self, lines: list) -> list:

        headers = {
            'LetterType': [1, 1],
            Structure.profile_table_mappings['client_id']: [2, 9],
            'Title': [11, 15],
            'GivenName': [26, 22],
            'Surname': [48, 40],
            'NameLine': [88, 30],
            'Post_Address_1': [118, 30],
            'Post_Address_2': [148, 30],
            'Post_Suburb': [178, 30],
            'Post_State': [208, 3],
            'PostCode': [211, 4],
            'Salutation': [215, 30],
            Structure.profile_table_mappings['email']: [245, 60],
            Structure.profile_table_mappings['phone']: [305, 20],
            'ActivePortalCustomerInd': [325, 1],
            'BanEndDate': [326, 8],
            'Minimum_Duration': [334, 4]  # TODO: get actual data structure for welcome pack
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[3:9])

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

                salutation = [row['Title'], row['Surname']]
                row['Salutation'] = ' '.join(x.title() for x in salutation if x)

                # name for Metadata report
                fullname = [row['GivenName'], row['Surname']]
                row['FullName'] = ' '.join(x.title() for x in fullname if x)

                # format dates
                row['BanEndDate'] = self.get_formatted_date(row['BanEndDate'])

                # csc barcode generation
                client_no = row[Structure.profile_table_mappings['client_id']]
                row['ClientBarcode'] = "*{}*".format(client_no.zfill(9))

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
        return 'You are required to install an alcohol interlock device.'

    def history_title(self, row: dict) -> str:
        return 'You have to install an alcohol interlock device. Please review'

    def correspondence_metadata(self, row) -> str:
        return '-'
