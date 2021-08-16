from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta


class VesselRego(Structure):

    product_family_name = PRODUCT_FAMILY_VESSEL_REGO
    supported_product_codes = [
        'boatcrt1',
        'boatcrt2',
        'ovrboat1',
        'ovrboat2',
        'ovrboat3',
        'ovrboat4',
        'ovrboat3be',
        'ovrboat4be',
        'boatreg1',
        'boatreg2'
    ]

    def parse(self, lines: list) -> list:
        headers = {
            'Name': [1, 52],
            'Post_Address_1': [53, 26],
            'Post_Address_2': [79, 26],
            'Post_Suburb': [105, 20],
            'Post_State': [125, 3],
            'PostCode': [128, 4],
            'ResAddress1': [132, 26],
            'ResAddress2': [158, 26],
            'ResSuburb': [184, 20],
            'ResState': [204, 3],
            'ResPostcode': [207, 4],
            'GarageAdd1': [211, 26],
            'GarageAdd2': [237, 26],
            'GarageSub': [263, 20],
            'GarageState': [283, 3],
            'GaragePost': [286, 4],
            'SerialNumber': [290, 7],
            'SerialChDigit': [297, 1],
            'StartDD': [298, 2],
            'Filler 1': [300, 1],
            'StartMM': [301, 3],
            'Filler 2': [304, 1],
            'StartYY': [305, 4],
            'ExpiryDD': [309, 2],
            'Filler 3': [311, 1],
            'ExpiryMM': [312, 3],
            'Filler 4': [315, 1],
            'ExpiryYY': [316, 4],
            'PaymentDate': [320, 10],
            'Registration_No': [330, 6],
            'CheckDigit': [336, 1],
            'RegistrationFee': [337, 6],
            'SumCheck': [343, 7],
            'RegCode': [350, 2],
            'RegoAmt': [352, 6],
            'RateCode': [358, 2],
            'InsuranceArea': [360, 6],
            'InsuranceCode': [366, 3],
            'InsuranceAmount': [369, 6],
            'InsuranceCat': [375, 3],
            'InsurancePremium': [378, 6],
            'StampDuty': [384, 6],
            'ExtraFee1': [390, 6],
            'ExtraFee2': [396, 6],
            'ExtraFee3': [402, 6],
            'ExtraFee4': [408, 6],
            'ExtraFee5': [414, 6],
            'NoPayment': [420, 1],
            'DocumentType': [421, 2],
            'RecordNoWeekly': [423, 10],
            'NhvIndicator': [433, 1],
            'NhvNbAxle': [434, 1],
            'NhvAdminFee': [435, 6],
            'NhvConcssnLevel': [441, 1],
            'NhvConcssnText': [442, 4],
            'NhvCondCode': [446, 15],
            'VehicleDesc': [461, 14],
            'VehicleMake': [475, 6],
            'VehicleType': [481, 6],
            'RTAFont': [487, 1],
            'VinNumber': [488, 18],
            'EngNumber': [506, 20],
            'YearManufacture': [526, 4],
            'InPrvNonBnkPymt': [530, 1],
            'InGoodsCarrying': [531, 3],
            'PostalCdCountry': [534, 3],
            'FeeCode': [537, 4],
            'RegType': [541, 22],
            'Duplicate': [563, 10],
            'BoatLength': [573, 3],
            'EngineType': [576, 8],
            'HullConType': [584, 6],
            'MaxPower': [590, 4],
            'Filler 5': [594, 11],
            'TitleCap': [605, 7],
            'CarryingCapacity': [612, 5],
            'Filler 6': [617, 3],
            'TitleSeats': [620, 6],
            'Seats': [626, 3],
            'Filler 7': [629, 4],
            'TransTxt1': [633, 68],
            'TransTxt2': [701, 62],
            'Office': [763, 10],
            'FourWDInd': [773, 1],
            'InConcession': [774, 1],
            'PMU': [775, 4],
            'PartYear': [779, 1],
            'InsertSup': [780, 1],
            'GST': [781, 6],
            'CycleLevy': [787, 1],
            'Filler 8': [788, 7],
            Structure.profile_table_mappings['client_id']: [795, 8],
            'Email_Rqd_Ind': [803, 1],
            Structure.profile_table_mappings['email']: [804, 60],
            Structure.profile_table_mappings['phone']: [864, 19],
            'SMS_Rqd_Ind': [883, 1],
            'Portal_Rqd_Ind': [884, 1],
            'RecurPayInd': [885, 1],
            'ShortTermInd': [886, 1],
            'ShortTermAdmFee': [887, 6],
            'PaperBillFee': [893, 6],
            'Filler': [899, 16]
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

                filename = _line['raw_filename']
                row['FilePrefix'] = self.get_prefix_from_filename(filename)

                # remove decimals from rego amount if any to work with
                row['RegistrationFee'] = row['RegistrationFee'].replace('.', '', 1)

                # MR-AC11
                if row['ExpiryMM'] == 'JLY':
                    row['ExpiryMM'] = 'JUL'
                if row['StartMM'] == 'JLY':
                    row['StartMM'] = 'JUL'

                # format and concatenate dates
                row['StartDate'] = '{} {} {}'.format(row['StartDD'], row['StartMM'], row['StartYY'])
                row['ExpiryDate'] = '{} {} {}'.format(row['ExpiryDD'], row['ExpiryMM'], row['ExpiryYY'])

                out_month = '0{}'.format(str(self.mm_as_digit(row['ExpiryMM'])))[-2:]
                row['Outmonth1Digit'] = str(out_month).lstrip('0')

                # data mapping
                row['LetterType'] = 'MOK'
                if row['FilePrefix'].startswith('boatcrt'):
                    row['LetterType'] = 'JSM'

                if row['LetterType'] != 'JSM':
                    if row['PartYear'] and int(row['PartYear']) in [7, 8, 9]:
                        prev_exp_date = datetime.strptime(row['StartDate'], '%d %b %Y')
                        new_exp_date = prev_exp_date + relativedelta(years=+1)
                    else:
                        prev_exp_date = datetime.strptime(row['StartDate'], '%d %b %Y')
                        new_exp_date = prev_exp_date + relativedelta(months=+3)

                    # generate ICRN number
                    icrn_ref = "1{}".format(row['SerialNumber'].zfill(8))
                    icrn_expiry_date = new_exp_date.strftime('%Y/%m/%d')
                    icrn_amount = row['RegistrationFee'].lstrip('0')
                    row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_expiry_date, icrn_amount)

                    # auspost code generation
                    _ = datetime.strptime(row['ExpiryDate'], '%d %b %Y')
                    barcode_expiry_date = _.strftime('%d%m%y')
                    code_string = "374{}{}{}{}".format(row['SerialNumber'], row['SerialChDigit'], row['RegistrationFee'].zfill(9), str(barcode_expiry_date))
                    text = "*374 {} {} {}".format(row['SerialNumber'], row['SerialChDigit'], str(barcode_expiry_date))
                    code = 'code128'
                    row['AusPostBarcodeBase64'] = self.barcode(code_string, text, code)

                    # office use barcode calculation
                    code_string = '*REG' + row['Registration_No'] + row['CheckDigit']
                    text = ''
                    code = 'code128'
                    row['OfficeUseBarcodeBase64'] = self.barcode(code_string, text, code)

                # format power and length
                row['MaxPower'] = "{}.{}".format(row['MaxPower'][:-1].zfill(3), row['MaxPower'][-1:])

                # convert registration fee to currency
                row['RegistrationFee'] = self.get_currency(row['RegistrationFee'])

                # convert name to capital case
                # name for Metadata report
                row['FullName'] = row['Name'].title()

                # email subject
                row['EmailSubject'] = self.email_subject(row)

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

    def email_template(self) -> str:
        return 'generic/template3.html'

    def sms_template(self) -> str:
        pass

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        if row['FilePrefix'] in ['ovrboat1', 'ovrrboat2', 'ovrboat3', 'ovrboat4', 'ovrboat3be', 'ovrboat4be', 'boatreg1', 'boatreg2']:
            return "It's time to pay your vessel rego {}".format(row['Registration_No'])
        elif row['FilePrefix'] in ['boatcrt1', 'boatcrt2']:
            return 'A duplicate for your vessel registration renewal {} was sent'.format(row['Registration_No'])
        return 'You have a message'

    def history_title(self, row: dict) -> str:
        if row['FilePrefix'] in ['ovrboat1', 'ovrrboat2', 'ovrboat3', 'ovrboat4', 'ovrboat3be', 'ovrboat4be']:
            return 'Your vessel rego renewal for {} has been sent.'.format(row['Registration_No'])
        elif row['FilePrefix'] in ['boatcrt1', 'boatcrt2']:
            return 'Your vessel rego duplicate for {} has been sent.'.format(row['Registration_No'])
        elif row['FilePrefix'] in ['boatreg1', 'boatreg2']:
            return 'Your vessel rego for {} is due for renewal on {}. Please pay.'.format(row['Registration_No'],
                                                                                          row['ExpiryDate'])
        return 'You have a message'

    def business_rules(self, rows: list) -> list:
        pass

    def validate_business_rules(self, row: dict, headers: dict):
        # invalid record if client no is invalid
        try:
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid registration number - blank field',
                                        position_data=headers['Registration_No'])
                return False
        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

    def correspondence_metadata(self, row) -> str:
        return '-'
