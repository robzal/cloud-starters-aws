from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime


class RegistrationRenewalsNhvr(Structure):

    product_family_name = PRODUCT_FAMILY_REGISTRATION_RENEWAL_NHVR
    supported_product_codes = [
        'nhvrrgcrt1',
        'nhvrrgcrt2',
        'nhvrovnrnew1',
        'nhvrovnrnew2',
        'nhvrovnrnew3',
        'nhvrovnrnew4',
        'nhvrrenew1',
        'nhvrrenew2'
    ]

    def parse(self, lines: list) -> list:
        headers = {
            'Name': [1, 26],
            'NameLine2': [27, 26],
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
            'Spare': [300, 1],
            'StartMM': [301, 3],
            'Spare2': [304, 1],
            'StartYY': [305, 4],
            'ExpiryDD': [309, 2],
            'Spare3': [311, 1],
            'ExpiryMM': [312, 3],
            'Spare4': [315, 1],
            'ExpiryYY': [316, 4],
            'PaymentDate': [320, 10],
            'Registration_No': [330, 6],
            'Reg_checkDigit': [336, 1],
            'TotalFeePayable': [337, 7],
            'SumCheck': [344, 7],
            'RegCode': [351, 2],
            'RegoAmt': [353, 6],
            'RateCode': [359, 2],
            'InsuranceArea': [361, 6],
            'InsuranceCode': [367, 3],
            'InsuranceAmount': [370, 6],
            'InsuranceCat': [376, 3],
            'InsurancePremium': [379, 6],
            'StampDuty': [385, 6],
            'ExtraFee1': [391, 6],
            'ExtraFee2': [397, 6],
            'ExtraFee3': [403, 6],
            'ExtraFee4': [409, 6],
            'ExtraFee5': [415, 6],
            'NoPayment': [421, 1],
            'DocumentType': [422, 2],
            'RecordNoWeekly': [424, 10],
            'NhvIndicator': [434, 1],
            'NHVNumberofAxles': [435, 1],
            'NhvAdminFee': [436, 6],
            'NhvRoadUseFee': [442, 7],
            'NhvRegulatoryFee': [449, 7],
            'NhvConcssnLevel': [456, 1],
            'NhvConcssnText': [457, 50],
            'NhvCondCode': [507, 15],
            'NHVROADREGLIND': [522, 1],
            'VehicleDesc': [523, 14],
            'VehicleMake': [537, 6],
            'VehicleType': [543, 6],
            'RTAFont': [549, 1],
            'VinNumber': [550, 18],
            'EngNumber': [568, 20],
            'YearManufacture': [588, 4],
            'InPrvNonBnkPymt': [592, 1],
            'InGoodsCarrying': [593, 3],
            'PostalCdCountry': [596, 3],
            'FeeCode': [599, 4],
            'RegType': [603, 22],
            'Duplicate': [625, 9],
            'TareTitle': [634, 5],
            'Tare': [639, 5],
            'GCMTitle': [644, 4],
            'GCM': [648, 6],
            'GVMTitle': [654, 4],
            'GVM': [658, 6],
            'Spare5': [664, 4],
            'TitleCap': [668, 7],
            'CarryingCapacity': [675, 6],
            'Spare1': [681, 3],
            'TitleSeats': [684, 6],
            'Seats': [690, 3],
            'Spare6': [693, 4],
            'TransTxt1': [697, 68],
            'TransTxt2': [765, 62],
            'Office': [827, 10],
            'FourWDInd': [837, 1],
            'InConcession': [838, 1],
            'PMU': [839, 4],
            'PartYear': [843, 1],
            'InsertSup': [844, 1],
            'GST': [845, 6],
            'CycleLevy': [851, 1],
            'HCCAmount': [852, 6],
            'LAMFlag': [858, 1],
            Structure.profile_table_mappings['client_id']: [859, 8],
            'Email_Rqd_Ind': [867, 1],
            Structure.profile_table_mappings['email']: [868, 60],
            Structure.profile_table_mappings['phone']: [928, 19],
            'SMS_Rqd_Ind': [947, 1],
            'Portal_Rqd_Ind': [948, 1],
            'RecurPayInd': [949, 1],
            'ShortTermInd': [950, 1],
            'ShortTermAdmFee': [951, 6],
            'PaperBillFee': [957, 6],
            'Filler': [963, 14]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[3:10])

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
                                    reason='Detail records does not match the total record count in the trailer record')
            return []

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

                # PBR3
                if data_dict['ExpiryMM'] == 'JLY':
                    data_dict['ExpiryMM'] = 'JUL'
                if data_dict['StartMM'] == 'JLY':
                    data_dict['StartMM'] = 'JUL'

                # format and concatenate dates
                data_dict['StartDate'] = self.get_formatted_date('{}{}{}'.format(data_dict['StartDD'], data_dict['StartMM'], data_dict['StartYY']))
                data_dict['ExpiryDate'] = self.get_formatted_date('{}{}{}'.format(data_dict['ExpiryDD'], data_dict['ExpiryMM'], data_dict['ExpiryYY']))
                data_dict['PaymentDate'] = self.get_formatted_date(data_dict['PaymentDate'])

                rows.append( {**data_dict, **_line} )
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        valid_rows = self.business_rules(rows)
        processed_rows = self.perform_data_manipulation(valid_rows)
        return processed_rows

    def business_rules(self, rows: list) -> list:
        filtered_rows = []

        for i, row in enumerate(rows):
            try:
                # BR1
                if not row['Registration_No']:
                    self.report_invalid_row(row, reason='Invalid licence number - blank field')
                    continue

                # BR2
                if len(row['raw_row']) != 978:
                    self.report_invalid_row(row, reason='Invalid record size')
                    continue

                # BR4
                if int(row['ExpiryYY']) > (int(datetime.now().year) + 1):
                    self.report_invalid_row(row, reason='Invalid expiry date')
                    continue

                # BR5 [TODO: Clarify rule]
                # if row['FilePrefix'] in ['ovnrnew1', 'ovnrnew2', 'ovnrnew3', 'ovnrnew4', 'renew1', 'renew2']:
                #     manual_calculated_fee = self.convert_string_to_amount(row['RegoAmt']) + \
                #                             self.convert_string_to_amount(row['InsurancePremium']) + \
                #                             self.convert_string_to_amount(row['StampDuty']) + \
                #                             self.convert_string_to_amount(row['NhvAdminFee']) + \
                #                             self.convert_string_to_amount(row['ShortTermAdmFee'])
                #     if manual_calculated_fee != self.convert_string_to_amount(row['TotalFeePayable']):
                #         self.report_invalid_row(row, reason='Invalid total due')
                #         continue

                # BR6
                if int(row['StartYY']) < 2000:
                    self.report_invalid_row(row, reason='Invalid start date')
                    continue

                # BR7
                if not row['StartDate']:
                    self.report_invalid_row(row, reason='Invalid start date')
                    continue

                # BR8
                if int(row['ExpiryYY']) < 2000:
                    self.report_invalid_row(row, reason='Invalid expiry date')
                    continue

                # BR9
                if not row['ExpiryDate']:
                    self.report_invalid_row(row, reason='Invalid expiry date')
                    continue

                # BR10
                if (row['ExtraFee1'] and int(row['ExtraFee1']) != 0) or \
                        (row['ExtraFee2'] and int(row['ExtraFee2']) != 0) or \
                        (row['ExtraFee3'] and int(row['ExtraFee3']) != 0) or \
                        (row['ExtraFee4'] and int(row['ExtraFee4']) != 0) or \
                        (row['ExtraFee5'] and int(row['ExtraFee5']) != 0):
                    self.report_invalid_row(row, reason='Invalid extra fee')
                    continue

                # BR11
                if row['InConcession'] and row['InConcession'] != 'X':
                    self.report_invalid_row(row, reason='Invalid concession')
                    continue

                # BR12
                if not row['FeeCode']:
                    self.report_invalid_row(row, reason='Invalid fee code')
                    continue

                # BR13
                if row['NhvConcssnText'] and row['NhvConcssnText'] not in ['HT2', 'HT3', 'P/P']:
                    self.report_invalid_row(row, reason='Invalid heavy vehicle concession text')
                    continue

                # BR14
                if not row['VehicleDesc']:
                    self.report_invalid_row(row, reason='Vehicle description is equal to space - invalid')
                    continue

                # BR15
                if not row['VehicleMake']:
                    self.report_invalid_row(row, reason='Vehicle Make is equal to space - invalid')
                    continue

                # BR16
                if row['FourWDInd'] == 'Y' and row['CycleLevy'] in ['*', '#']:
                    self.report_invalid_row(row, reason='Invalid Cycle levy')
                    continue

                # BR17
                if row['HCCAmount'] and not row['HCCAmount'].isdigit():
                    self.report_invalid_row(row, reason='Invalid HCCAmount')
                    continue

                # BR18
                if not row[Structure.profile_table_mappings['client_id']] \
                        or len(row[Structure.profile_table_mappings['client_id']].strip()) != 8\
                        or not row[Structure.profile_table_mappings['client_id']].isdigit():
                    self.report_invalid_row(row, reason='Invalid customer number')
                    continue

                # BR19
                if not row['PaymentDate']:
                    self.report_invalid_row(row, reason='Invalid payment date')
                    continue

                # BR20
                if row['PartYear'] and int(row['PartYear']) > 10:
                    self.report_invalid_row(row, reason='Invalid part year')
                    continue

                filtered_rows.append(row)

            except Exception as e:
                logger.warning('failed processing business rules', extra={'data': str(e)})
                self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
                continue

        return filtered_rows

    def perform_data_manipulation(self, rows: list) -> list:
        for row in rows:
            try:
                # clean address fields
                address_fields_list = ['Post_Address_1', 'Post_Address_2', 'Post_Suburb', 'Post_State', 'PostCode',
                                       'ResAddress1', 'ResAddress2', 'ResSuburb', 'ResState', 'ResPostcode',
                                       'GarageAdd1', 'GarageAdd2', 'GarageSub', 'GarageState', 'GaragePost']
                for i in address_fields_list:
                    row[i] = row[i].replace('<', ' ').replace('>', ' ')
                if not row['Post_State']:
                    row['Post_State'] = self.state_by_code(row['PostCode'])

                # generate ICRN number
                row['IcrnNumber'] = self.generate_icrn_number(row)

                # product business rules
                # PBR1
                if row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                        row['NhvConcssnLevel'] not in ['1', '2', '3', '4'] and \
                        row['PartYear'] not in ['1', '2', '3', '4', '5', '6'] and \
                        row['InsuranceCat'] != 26 and \
                        row['FeeCode'] in ['MC4', 'MC5', 'FMC4', 'FMC5', 'MR2', 'MR3', 'MR4', 'MR5', 'LR2', 'LR3',
                                           'LR4', 'LR5', 'MC2', 'MC3']:
                    if row['TotalFeePayable'].isdigit():
                        row['TotalFeePayable'] = str(int(row['TotalFeePayable']) + 10000)
                    if row['RegoAmt'].isdigit():
                        row['RegoAmt'] = str(int(row['RegoAmt']) + 10000)

                # Expiry Date calculation
                row['Calculated_ExpiryDate'] = self.calculate_expiry_date(row)

                # barcode calculation
                row['AusPostBarcodeBase64'] = self.generate_auspost_barcode(row)
                row['OfficeUseBarcodeBase64'] = self.generate_office_use_barcode(row)

                # PBR5
                if row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2']:
                    total_fee_payable_formatted = float(row['TotalFeePayable']) / 100
                    row['PaymentCode'] = "{} {}  {}  {}  {}".format(row['Registration_No'],
                                                                          row['SerialChDigit'],
                                                                          str(row['Calculated_ExpiryDate']),
                                                                          row['SerialNumber'],
                                                                          str(total_fee_payable_formatted))

                # output channel mappings
                row = self.user_output_channels_mapping(row)
                row = self.get_output_channels_mapping(row)

                # bounce back check TODO
                row['BounceBack'] = 0

                # panel show hide values
                row = self.panel_show_hide_messages(row)

                # vehicle heading
                if row['VehicleDesc'] == 'Trailer':
                    row['VehicleHeading'] = 'Trailer'
                elif row['VehicleDesc'] == 'CAR':
                    row['VehicleHeading'] = 'Motor vehicle'
                else:
                    row['VehicleHeading'] = 'Motor cycle'

                # format currency
                if row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2']:
                    row['TotalFeePayable'] = self.get_currency(row['TotalFeePayable'])
                    row['RegoAmt'] = self.get_currency(row['RegoAmt'])
                    row['InsurancePremium'] = self.get_currency(row['InsurancePremium'])
                    row['StampDuty'] = self.get_currency(row['StampDuty'])
                    row['GST'] = self.get_currency(row['GST'])
                    row['NhvRoadUseFee'] = self.get_currency(row['NhvRoadUseFee'])
                    row['NhvRegulatoryFee'] = self.get_currency(row['NhvRegulatoryFee'])
                    row['ServiceFee'] = self.get_currency(row['ShortTermAdmFee'])
                    row['PaperBillFee'] = self.get_currency(row['PaperBillFee'])

                if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2']:
                    if row['ShortTermAdmFee'] == '000000' or row['ShortTermAdmFee'] == 'NO FEE':
                        row['ServiceFee'] = "PAID"

                # convert name to capital case
                if row['Name']:
                    row['DerivedName'] = row['Name'].title()
                else:
                    row['DerivedName'] = row['NameLine2'].title()

                # process Addresses
                row = self.process_addresses(row)

                # get current date
                row['SystemDate'] = self.get_current_system_date()

            except Exception as e:
                self.report_invalid_row(row, reason='failed parsing line {}'.format(str(e)))
        return rows

    # helpers
    def panel_show_hide_messages(self, row):
        row['LetterType'] = 'Others'
        row['CycleLevySpecialChar'] = 0
        row['ShowSetAndForget'] = 0
        row['ShowAddConcession'] = 0
        row['ShowHealthcareMessage'] = 0
        row['ShowEngNumber'] = 0
        row['ShowOnlyTare'] = 0
        row['ShowShortRegoImage'] = 0
        row['ShowConcessionDeductedMessage'] = 0
        row['ShowSwitchShortRegoMessage'] = 0
        row['ShowChooseShortRegoMessage'] = 0
        
        if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2']:
            row['LetterType'] = 'JSM'

        if row['CycleLevy'] in ['*', '#']:
            row['CycleLevySpecialChar'] = 1

        if row['ShortTermInd'] == 'Y' and \
                row['FeeCode'] in ['CP', 'CQ', 'CS', 'JP', 'JQ', 'JW', 'VJ', 'VK', 'VL']:
            row['ShowAddConcession'] = 1

        if row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR',
                                         'JH', 'PF', 'PT', 'PR', 'PH', 'VL'] and \
                row['Email_Rqd_Ind'] != 'Y':
            row['ShowSetAndForget'] = 1

        if not row['InConcession'] and \
                row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                row['FeeCode'] in ['CH', 'CZ', 'JZ', 'PH', 'PZ', 'JH'] and \
                row['RecurPayInd'] == 'N':
            row['ShowHealthcareMessage'] = 1
            row['HCCAmount'] = self.get_currency(row['HCCAmount'])

        if row['NhvIndicator'] not in ['X', 'Y'] \
                and row['EngNumber']:
            row['ShowEngNumber'] = 1

        if row['NhvIndicator'] in ['X', 'Y']:
            row['TareInfo'] = row['Tare']
        else:
            row['TareInfo'] = "{}, {}, {}".format(row['Tare'], row['NHVNumberofAxles'], row['InGoodsCarrying'])

        if row['FeeCode'] in ['TF', 'TH', 'TL', 'TV'] and \
                row['GVM']:
            row['ShowGvm'] = 1

        if row['FilePrefix'] not in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR',
                                         'JH', 'PF', 'PT', 'PR', 'PH', 'VL']:
            row['ShowShortRegoImage'] = 1

        if row['FeeCode'] in ['CH', 'CZ', 'CU', 'JH', 'JZ', 'JU', 'PH', 'PZ', 'PV']:
            row['ShowConcessionDeductedMessage'] = 1

        if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                not row['ShortTermAdmFee'] and \
                row['PartYear'] in ['1', '2', '3', '4', '5', '6'] and \
                row['FeeCode'] in ['AU', 'CF', 'CP', 'CU', 'CW', 'EQ', 'ER', 'FF', 'FJ', 'FW', 'GG', 'JP', 'JT',
                                         'JU', 'PG', 'PS', 'PU', 'PV', 'VJ', 'AS', 'CE', 'CQ', 'ES', 'FC', 'FK', 'GF',
                                         'JQ', 'PE', 'VK', 'PX', 'PY', 'JX', 'FX', 'EX', 'CX']:
            row['ShowSwitchShortRegoMessage'] = 1

        if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2'] and \
                row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR',
                                         'JH', 'PF', 'PT', 'PR', 'PH', 'VL']:
            row['ShowChooseShortRegoMessage'] = 1
        return row

    def generate_icrn_number(self, row):
        icrn_ref = row['SerialNumber'].zfill(9)
        exp_date = datetime.strptime(self.get_formatted_date(row['ExpiryDate']), '%d %B %Y')
        icrn_date = exp_date.strftime('%Y/%m/%d')
        icrn_amount = row['TotalFeePayable'].lstrip("0")
        return self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

    def calculate_expiry_date(self, row):
        if row['PartYear'] and int(row['PartYear']) in [7, 8, 9]:
            calculated_start_yy = int(row['StartYY']) + 1
            calculated_start_mm = self.mm_as_digit(row['StartMM'])
        else:
            calculated_start_yy = int(row['StartYY'])
            calculated_start_mm = self.mm_as_digit(row['StartMM']) + 3

            if calculated_start_mm > 12:
                calculated_start_mm = calculated_start_mm - 12
                calculated_start_yy = calculated_start_yy - 1

        next_pay_date = int(row['ExpiryDD'])

        if calculated_start_mm in [4, 6, 9, 11] and next_pay_date > 30:
            next_pay_date = 30

        if calculated_start_mm == 2:
            if self.is_leap_year(calculated_start_yy):
                next_pay_date = 29
            else:
                next_pay_date = 28

        calculated_start_yy = str(calculated_start_yy)
        return str(next_pay_date) + '{:02d}'.format(calculated_start_mm) + calculated_start_yy[2:5]

    def generate_auspost_barcode(self, row):
        code_string = '374' + row['SerialNumber'] + row['SerialChDigit'] + '00' + row[
            'TotalFeePayable'] + str(
            row['Calculated_ExpiryDate'])
        text = '*374' + ' ' + row['SerialNumber'] + row['SerialChDigit'] + ' ' + str(
            row['Calculated_ExpiryDate'])
        code = 'code128'
        return self.barcode(code_string, text, code)

    def generate_office_use_barcode(self, row):
        code_string = 'REG' + row['Registration_No'] + row['Reg_checkDigit']
        text = ''
        code = 'code39'
        return self.barcode(code_string, text, code)

    def process_addresses(self, row):
        # generate address line3
        row['Post_Address_3'] = self.get_address_line3(
            row['Post_Suburb'],
            row['Post_State'],
            row['PostCode'])
        row['ResAddress3'] = self.get_address_line3(
            row['ResSuburb'],
            row['ResState'],
            row['ResPostcode'])
        row['GarageAdd3'] = self.get_address_line3(
            row['GarageSub'],
            row['GarageState'],
            row['GaragePost'])

        # format address lines
        formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
        row['Post_Address_1'] = formatted_addresses[0]
        row['Post_Address_2'] = formatted_addresses[1]
        row['Post_Address_3'] = formatted_addresses[2]

        formatted_addresses = self.get_formatted_address(
            row['ResAddress1'],
            row['ResAddress2'],
            row['ResAddress3'])
        row['ResAddress1'] = formatted_addresses[0]
        row['ResAddress2'] = formatted_addresses[1]
        row['ResAddress3'] = formatted_addresses[2]

        formatted_addresses = self.get_formatted_address(
            row['GarageAdd1'],
            row['GarageAdd2'],
            row['GarageAdd3'])
        row['GarageAdd1'] = formatted_addresses[0]
        row['GarageAdd2'] = formatted_addresses[1]
        row['GarageAdd3'] = formatted_addresses[2]

        return row

    # static helpers
    @staticmethod
    def get_output_channels_mapping(row):
        if row['FilePrefix'] in ['nhvrrenew1', 'nhvrrenew2', 'nhvrovnrnew1', 'nhvrovnrnew2', 'nhvrovnrnew3', 'nhvrovnrnew4']:
            if row['Email_Rqd_Ind'] == 'N':
                row['Mail_Required'] = 'Y'
                row['Email_Required'] = 'N'
            else:
                row['Mail_Required'] = 'N'
                row['Email_Required'] = 'Y'
            row['SMS_Required'] = 'N'

        if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2']:
            row['Mail_Required'] = 'Y'
            if row['Email_Rqd_Ind'] == 'Y':
                row['Email_Required'] = 'Y'
            else:
                row['Email_Required'] = 'N'
            row['SMS_Required'] = 'N'
        return row

    # template mappings
    def email_subject(self, row) -> str:
        if row['FilePrefix'] in ['nhvrrenew1', 'nhvrrenew2', 'nhvrovnrnew1', 'nhvrovnrnew2', 'nhvrovnrnew3', 'nhvrovnrnew4']:
            if row['RecurPayInd'] == 'Y':
                return "We're processing your payment for rego {}".format(self.row['Registration_No'])
            if row['RecurPayInd'] == 'N':
                return "It's time to pay your rego {}".format(self.row['Registration_No'])
        if row['FilePrefix'] in ['nhvrrgcrt1', 'nhvrrgcrt2']:
            return "It's time to pay your rego {}".format(self.row['Registration_No'])

    def email_template(self) -> str:
        return '{}/email-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        return '{}/sms-template.txt'.format(self.product_family_name)

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def html_template(self) -> str:
        return None
        # return '{}/html-template.html'.format(self.product_family_name)

    def history_title(self, row: dict) -> str:
        # TODO
        return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
