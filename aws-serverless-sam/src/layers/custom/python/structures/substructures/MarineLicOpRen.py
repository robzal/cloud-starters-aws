from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta


class MarineLicOpRen(Structure):
    product_family_name = PRODUCT_FAMILY_MARINE_LICENCE_RENEWAL
    supported_product_codes = ['LicOpRen']

    def parse(self, lines: list) -> list:

        headers = {
            'RecId': [1, 2],
            'PhotoFlag': [3, 1],
            Structure.profile_table_mappings['client_id']: [4, 9],
            'Name': [13, 27],
            'Name_Inc_Title': [40, 27],
            'NameOfficeCopy': [67, 20],
            'PageCount': [87, 6],
            'Post_Address_1': [93, 27],
            'Post_Address_2': [120, 27],
            'Post_Address_3': [147, 25],
            'ResAdd1': [172, 27],
            'ResAdd2': [199, 27],
            'ResAdd3': [226, 25],
            'LResAdd1': [251, 27],
            'LResAdd2': [278, 27],
            'LResAdd3': [305, 25],
            'ExpDate': [330, 10],
            'BirthDate': [340, 10],
            'LicenceFee': [350, 8],
            'EndorsementType': [358, 11],
            'LicDesc1': [369, 25],
            'LicDesc': [394, 17],
            'RestrictEnd': [411, 10],
            'TotalFee': [421, 8],
            'Licence_Category_1': [429, 1],
            'Licence_Category_2': [430, 1],
            'Licence_Category_3': [431, 1],
            'Licence_Category_4': [432, 1],
            'Licence_Category_5': [433, 1],
            'Licence_Category_6': [434, 1],
            'Licence_Category_7': [435, 1],
            'Licence_Category_8': [436, 1],
            'Filler 1': [437, 4],
            'WarnType': [441, 7],
            'LMCode': [448, 2],
            'WarnText': [450, 58],
            'PrevExp': [508, 10]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[2:12])

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
                                    position_data=[3, 10])
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

                # onsert required condition
                if row['PhotoFlag'] == 'Y':
                    row['OnsertRequired'] = 1
                    row['OnsertMergeAtStart'] = 0
                    row['OnsertsToMerge'] = ["PhotoLocations.pdf"]

                # format dates
                row['ExpDate'] = self.get_formatted_date(row['ExpDate'])
                row['PrevExp'] = self.get_formatted_date(row['PrevExp'])
                row['BirthDate'] = self.get_formatted_date(row['BirthDate'])
                row['RestrictEnd'] = self.get_formatted_date(row['RestrictEnd'])

                if row['PhotoFlag'] != 'Y':
                    # generate ICRN number
                    client_no_icrn = row[Structure.profile_table_mappings['client_id']]
                    prev_exp_date_icrn = datetime.strptime(self.get_formatted_date(row['PrevExp']), '%d %B %Y')

                    calculated_date = prev_exp_date_icrn + relativedelta(months=+6)
                    icrn_ref = client_no_icrn.zfill(9)
                    icrn_ref = '3' + icrn_ref[1:]
                    icrn_date = calculated_date.strftime('%Y/%m/%d')

                    icrn_amount = row['LicenceFee'].replace('.', '')

                    row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

                # auspost code generation
                client_no = row[Structure.profile_table_mappings['client_id']]

                prev_exp_date = datetime.strptime(self.get_formatted_date(row['PrevExp']), '%d %B %Y')
                calculated_date = prev_exp_date + relativedelta(months=+6)

                barcode_calculated_payment_date = calculated_date.strftime('%d%m%y')

                licence_fee = row['LicenceFee'].replace('.', '')
                licence_fee = licence_fee.zfill(5)

                code_string = "*3003{}{}{}".format(client_no, barcode_calculated_payment_date, licence_fee)
                text = "*3003 {} {}".format(client_no, barcode_calculated_payment_date)
                code = 'code128'
                row['AusPostBarcodeBase64'] = self.barcode(code_string, text, code)

                # csc barcode generation
                row['CscBarcodeCode'] = "*{}*".format(client_no.zfill(9))
                row['CscBarcodeText'] = "{}".format(client_no.zfill(9))

                # licence conditions string
                licence_conditions_list = [row['Licence_Category_1'], row['Licence_Category_2'],
                                           row['Licence_Category_3'], row['Licence_Category_4'],
                                           row['Licence_Category_5'], row['Licence_Category_6'],
                                           row['Licence_Category_7'], row['Licence_Category_8']]
                row['Licence_conditions'] = ' '.join(
                    x.strip() for x in filter(None, licence_conditions_list) if x.strip())
                if not row['Licence_conditions'] or row['Licence_conditions'] == ' ':
                    row['Licence_conditions'] = 'None'

                # convert name
                if row['Name_Inc_Title']:
                    row['DerivedName'] = row['Name_Inc_Title'].title()
                else:
                    row['DerivedName'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # data mappings
                row['MarineLicenceNo'] = "{}   {}".format(row[Structure.profile_table_mappings['client_id']], row['LMCode'])

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                # format Residential lines
                res_formatted_addresses = self.get_formatted_address([row['ResAdd1'], row['ResAdd2'], row['ResAdd3']])
                row['ResAdd1'] = res_formatted_addresses[0]
                row['ResAdd2'] = res_formatted_addresses[1]
                row['ResAdd3'] = res_formatted_addresses[2]

                # format currency
                row['LicenceFee'] = self.get_currency(row['LicenceFee'])

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
        return 'It’s time to pay your marine licence renewal'

    def history_title(self, row) -> str:
        return 'Your marine licence is due for renewal on {}. Please pay.'.format(row['ExpDate'])

    def correspondence_metadata(self, row) -> str:
        return '-'
