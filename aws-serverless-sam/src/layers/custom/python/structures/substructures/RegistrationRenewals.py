from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RegistrationRenewals(Structure):
    product_family_name = PRODUCT_FAMILY_REGISTRATION_RENEWAL
    supported_product_codes = [
        'rgcrt1',
        'rgcrt2',
        'ovnrnew1',
        'ovnrnew2',
        'ovnrnew3',
        'ovnrnew4',
        'renew1',
        'renew2'
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
            'Spare1': [300, 1],
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
            'TotalFeePayable': [337, 6],
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
            'NHVNumberofAxles': [434, 1],
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
            'Duplicate': [563, 9],
            'TareTitle': [572, 5],
            'Tare': [577, 5],
            'GCMTitle': [582, 4],
            'GCM': [586, 5],
            'GVMTitle': [591, 4],
            'GVM': [595, 5],
            'Spare5': [600, 5],
            'TitleCap': [605, 7],
            'CarryingCapacity': [612, 5],
            'Spare6': [617, 3],
            'TitleSeats': [620, 6],
            'Seats': [626, 3],
            'Spare7': [629, 4],
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
            'HCCAmount': [788, 6],
            'LAMFlag': [794, 1],
            Structure.profile_table_mappings['client_id']: [795, 8],
            'Email_Rqd_Ind': [803, 1],
            Structure.profile_table_mappings['email']: [804, 60],
            Structure.profile_table_mappings['phone']: [864, 19],
            'SMS_Rqd_Ind': [883, 1],
            'Portal_Rqd_Ind': [884, 1],
            'RecurPayInd': [885, 1],
            'ShortTermInd': [886, 1],
            'ShortTermAdmFee': [887, 6],
            'PaperBillFee': [893, 6]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[3:9])

        # BR-AC2
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

                filename = _line['raw_filename']
                data_dict['FilePrefix'] = self.get_prefix_from_filename(filename)

                row = {**data_dict, **_line}

                # Data manipulation prior to validating against business rules

                # handle july month name correction to cater for DXC error
                if row['ExpiryMM'] == 'JLY':
                    row['ExpiryMM'] = 'JUL'
                if row['StartMM'] == 'JLY':
                    row['StartMM'] = 'JUL'

                # format and concatenate dates
                row['StartDate'] = '{}{}{}'.format(row['StartDD'], row['StartMM'], row['StartYY'])
                row['StartDateFormatted'] = self.get_formatted_date(row['StartDate'])
                row['ExpiryDate'] = '{}{}{}'.format(row['ExpiryDD'], row['ExpiryMM'], row['ExpiryYY'])
                row['ExpiryDateFormatted'] = self.get_formatted_date(row['ExpiryDate'])
                row['PaymentDateFormatted'] = self.get_formatted_date(row['PaymentDate'])

                # remove any decimal symbols from the currency to use in calculations
                row['TotalFeePayable'] = row['TotalFeePayable'].replace('.', '', 1)
                row['RegoAmt'] = row['RegoAmt'].replace('.', '', 1)

                # deduce if duplicate rego or not and if duplicate then has it been paid for ot not
                if row['FilePrefix'] in ['rgcrt1', 'rgcrt2']:
                    row['IsDuplicate'] = 1
                    if row['TotalFeePayable'].isdigit() and row['TotalFeePayable'].strip('0') != '':
                        row['IsPaid'] = 0
                    else:
                        row['IsPaid'] = 1
                else:
                    row['IsDuplicate'] = 0
                    row['IsPaid'] = 0

                # add 10k to vehicles that have rego amount above 9999.99
                # to cater for restricted length of 6 chars to represent regoamt/ total fee in DXC .DAT file
                if not row['IsPaid']:
                    if row['NhvConcssnLevel'] not in ['1', '2', '3', '4'] and \
                            row['PartYear'] not in ['1', '2', '3', '4', '5', '6'] and \
                            row['InsuranceCat'] != 26 and \
                            row['FeeCode'] in ['MC2', 'MC3', 'MC4', 'MC5', 'MR2', 'MR3', 'MR4', 'MR5']:
                        if row['TotalFeePayable'].isdigit():
                            row['TotalFeePayable'] = str(int(row['TotalFeePayable']) + 1000000)
                        if (row['RegoAmt'].isdigit() and row['RegoAmt'].strip('0') != '') and \
                                row['FeeCode'] not in ['MR2', 'MR3']:
                            row['RegoAmt'] = str(int(row['RegoAmt']) + 1000000)

                # reject invalid records based on business rules
                if not self.validate_business_rules(row, headers):
                    continue

                # output channel mappings
                row = self.user_output_channels_mapping(row)
                row = self.get_output_channels_mapping(row)

                # only if NOT direct debit and not already paid for (in case it is for duplicates)
                if row['RecurPayInd'] != 'Y' and not row['IsPaid']:
                    # calculate expiry date based on part year value
                    if row['PartYear'] and int(row['PartYear']) in [7, 8, 9]:
                        prev_exp_date = datetime.strptime(row['StartDate'], '%d%b%Y')
                        new_exp_date = prev_exp_date + relativedelta(years=+1)
                    else:
                        prev_exp_date = datetime.strptime(row['StartDate'], '%d%b%Y')
                        new_exp_date = prev_exp_date + relativedelta(months=+3)

                    # generate ICRN number
                    icrn_ref = "1{}".format(row['SerialNumber'].zfill(8))
                    icrn_expiry_date = new_exp_date.strftime('%Y/%m/%d')
                    icrn_amount = row['TotalFeePayable'].lstrip('0')
                    row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_expiry_date, icrn_amount)

                    # auspost barcode calculation
                    barcode_expiry_date = new_exp_date.strftime('%d%m%y')
                    code_string = '374' + row['SerialNumber'] + row['SerialChDigit'] + \
                                  row['TotalFeePayable'].zfill(9) + str(barcode_expiry_date)
                    text = '*374' + ' ' + row['SerialNumber'] + row['SerialChDigit'] + ' ' + str(
                        barcode_expiry_date)
                    code = 'code128'
                    row['AusPostBarcodeBase64'] = self.barcode(code_string, text, code)

                    # payment code calculation
                    total_fee_payable_formatted = self.get_currency(row['TotalFeePayable'])
                    total_fee_payable_formatted = total_fee_payable_formatted[1:]
                    _ = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                    payment_code_expiry_date = _.strftime('%d %b %Y')
                    row['PaymentCode'] = "{}&nbsp;{}&nbsp;&nbsp;{}&nbsp;&nbsp;{}&nbsp;&nbsp;{}".format(
                        row['Registration_No'],
                        row['Reg_checkDigit'],
                        str(payment_code_expiry_date),
                        row['SerialNumber'],
                        str(total_fee_payable_formatted))

                # clean address fields
                address_fields_list = ['Post_Address_1', 'Post_Address_2', 'Post_Suburb', 'Post_State',
                                       'PostCode', 'ResAddress1', 'ResAddress2', 'ResSuburb', 'ResState',
                                       'ResPostcode', 'GarageAdd1', 'GarageAdd2', 'GarageSub', 'GarageState',
                                       'GaragePost']
                for field in address_fields_list:
                    row[field] = row[field].replace('<', ' ').replace('>', ' ')
                if not row['Post_State']:
                    row['Post_State'] = self.state_by_code(row['PostCode'])

                # office use barcode calculation
                code_string = '*REG' + row['Registration_No'] + row['Reg_checkDigit']
                text = ''
                code = 'code128'
                row['OfficeUseBarcodeBase64'] = self.barcode(code_string, text, code)

                # bounce back check TODO
                row['BounceBack'] = 0

                # panel show hide values
                row['ShowSetAndForget'] = 0
                row['ShowAddConcessionLeft'] = 0
                row['ShowAddConcessionRight'] = 0
                row['ShowHealthcareMessage'] = 0
                row['ShowMovingHouseImage'] = 0
                row['ShowConcessionDeductedMessage'] = 0
                row['ShowSwitchShortRego3MthsMessage'] = 0
                row['ShowSwitchShortRego6MthsMessage'] = 0
                row['ShowChooseShortRegoMessage'] = 0
                row['ShowGvm'] = 0

                # right hand side content blocks
                if row['NhvIndicator'] != 'Y' and \
                        row['FeeCode'] in ['AT', 'CB', 'CH', 'CR', 'CS', 'EN', 'ET', 'FI', 'FL', 'FN',
                                           'GE', 'JH', 'JR', 'JW', 'PF', 'PH', 'PR', 'PT', 'VL']:
                    row['ShowMovingHouseImage'] = 1

                if not row['IsDuplicate']:
                    if row['InConcession'] != 'X' and row['NhvIndicator'] != 'Y' and \
                            (row['FeeCode'] in ['EN', 'GE', 'JW', 'VL'] or
                             (row['FeeCode'] in ['CS'] and not row['InsuranceCat'].startswith('43'))):
                        row['ShowAddConcessionLeft'] = 1
                    elif row['InConcession'] != 'X' and row['NhvIndicator'] == 'Y' and \
                            (row['FeeCode'] in ['EN', 'GE', 'JW', 'VL'] or
                             (row['FeeCode'] in ['CS'] and not row['InsuranceCat'].startswith('43'))):
                        row['ShowAddConcessionRight'] = 1

                    if row['InConcession'] != 'X' and \
                            (row['FeeCode'] in ['ER', 'EX', 'GF', 'GG', 'JP', 'JQ', 'VJ', 'VK'] or
                             (row['FeeCode'] in ['CP', 'CQ'] and not row['InsuranceCat'].startswith('43'))):
                        row['ShowAddConcessionRight'] = 1
                else:
                    if row['InConcession'] != 'X' and \
                            (row['FeeCode'] in ['EN', 'ER', 'EX', 'GE', 'GF', 'GG', 'JP', 'JQ', 'JW', 'VJ', 'VK', 'VL'] or
                             (row['FeeCode'] in ['CP', 'CQ', 'CS'] and not row['InsuranceCat'].startswith('43'))):
                        row['ShowAddConcessionLeft'] = 1
                        row['ShowAddConcessionRight'] = 0

                if row['InConcession'] == 'X' and \
                        row['FeeCode'] in ['CH', 'CR', 'CU', 'CW', 'CX', 'CZ', 'JH', 'JU', 'JZ',
                                           'PH', 'PR', 'PS', 'PT', 'PU', 'PV', 'PX', 'PY', 'PZ']:
                    row['ShowConcessionDeductedMessage'] = 1

                if row['NhvIndicator'] != 'Y' and row['ShortTermInd'] == 'Y' and \
                        (row['ShortTermAdmFee'] and row['ShortTermAdmFee'].strip('0') != '') and \
                        row['FeeCode'] in ['AU', 'CF', 'CP', 'CU', 'CW', 'EQ', 'ER', 'FF', 'FJ', 'FW',
                                           'GG', 'JP', 'JT', 'JU', 'PG', 'PS', 'PU', 'PV', 'VJ']:
                    row['ShowSwitchShortRego3MthsMessage'] = 1

                if row['NhvIndicator'] != 'Y' and row['ShortTermInd'] == 'Y' and \
                        (row['ShortTermAdmFee'] and row['ShortTermAdmFee'].strip('0') != '') and \
                        row['FeeCode'] in ['AS', 'CE', 'CQ', 'CX', 'CZ', 'ES', 'EX', 'FC', 'FK', 'FX',
                                           'GF', 'JQ', 'JX', 'PE', 'PX', 'PY', 'VK']:
                    row['ShowSwitchShortRego6MthsMessage'] = 1

                if row['NhvIndicator'] != 'Y' and \
                        row['FeeCode'] in ['AT', 'CB', 'CH', 'CR', 'CS', 'EN', 'ET', 'FI', 'FL', 'FN',
                                           'GE', 'JH', 'JR', 'JW', 'PF', 'PH', 'PR', 'PT', 'VL']:
                    row['ShowChooseShortRegoMessage'] = 1

                if row['RecurPayInd'] != 'Y' and \
                        row['FeeCode'] in ['AS', 'AT', 'AU', 'CB', 'CE', 'CF', 'CH', 'CP', 'CQ', 'CR',
                                           'CS', 'CU', 'CW', 'CX', 'CZ', 'EN', 'EQ', 'ER', 'ES', 'ET',
                                           'EX', 'FC', 'FF', 'FI', 'FJ', 'FK', 'FL', 'FN', 'FW', 'FX',
                                           'GE', 'GF', 'GG', 'JH', 'JP', 'JQ', 'JR', 'JT', 'JU', 'JW',
                                           'JX', 'JZ', 'PE', 'PF', 'PG', 'PH', 'PR', 'PS', 'PT', 'PU',
                                           'PV', 'PX', 'PY', 'PZ', 'VJ', 'VK', 'VL']:
                    row['ShowSetAndForget'] = 1

                if not row['InConcession'] and \
                        row['FeeCode'] in ['CH', 'CU', 'CZ', 'JH', 'JU', 'JZ', 'PH', 'PV', 'PZ'] and \
                        row['RecurPayInd'] != 'Y':
                    row['ShowHealthcareMessage'] = 1
                    row['HCCAmount'] = self.get_currency(row['HCCAmount'])

                row['GVM'] = row['GVM'].lstrip('0')
                row['GCM'] = row['GCM'].lstrip('0')
                row['Tare'] = row['Tare'].lstrip('0')
                row['NHVNumberofAxles'] = row['NHVNumberofAxles'].lstrip('0')

                if row['NhvIndicator'] != 'Y':
                    row['TareInfo'] = row['Tare']
                else:
                    strings = [row['Tare'], row['NHVNumberofAxles'], row['InGoodsCarrying']]
                    row['TareInfo'] = ' '.join(x for x in strings if x)

                if row['FeeCode'] in ['TF', 'TH', 'TV'] and row['GVM']:
                    row['ShowGvm'] = 1

                feereg = [row['FeeCode'], row['RegType']]
                row['FeeRegDetails'] = ' '.join(x for x in feereg if x)

                # vehicle heading
                if row['VehicleDesc'].upper() == 'TRAILER':
                    row['VehicleHeading'] = 'Trailer'
                elif row['VehicleDesc'].upper() == 'MOTOR VEHICLE' or row['VehicleDesc'].upper() == 'CAR':
                    row['VehicleHeading'] = 'Motor vehicle'
                elif row['VehicleDesc'].upper() == 'MOTOR CYCLE' or row['VehicleDesc'].upper() == 'CYCLE':
                    row['VehicleHeading'] = 'Motor cycle'

                row['VehicleMake'] = row['VehicleMake'].title()
                row['VehicleType'] = row['VehicleType'].title()

                row['ServiceFee'] = row['ShortTermAdmFee']

                if row['IsPaid']:
                    if row['TotalFeePayable'].strip('0') == '' or row['TotalFeePayable'] in ['PAID']:
                        row['TotalFeePayable'] = "PAID"
                    if row['RegoAmt'].strip('0') == '' or row['RegoAmt'] in ['PAID']:
                        row['RegoAmt'] = "PAID"
                    if row['InsurancePremium'].strip('0') == '' or row['InsurancePremium'] in ['PAID']:
                        row['InsurancePremium'] = "PAID"
                    if row['StampDuty'].strip('0') == '' or row['StampDuty'] in ['PAID']:
                        row['StampDuty'] = "PAID"
                    if row['ServiceFee'].strip('0') == '' or row['ServiceFee'] in ['PAID'] or \
                            (row['ServiceFee'] and row['ServiceFee'] not in ['PAID', 'NO FEE', 'NIL']):
                        row['ServiceFee'] = "PAID"
                else:
                    # format currency
                    row['TotalFeePayable'] = self.get_currency(row['TotalFeePayable'])
                    row['RegoAmt'] = self.get_currency(row['RegoAmt'])
                    row['InsurancePremium'] = self.get_currency(row['InsurancePremium'])
                    row['StampDuty'] = self.get_currency(row['StampDuty'])
                    row['GST'] = self.get_currency(row['GST'])
                    row['ServiceFee'] = self.get_currency(row['ServiceFee'])
                    row['PaperBillFee'] = self.get_currency(row['PaperBillFee'])

                # convert name to capital case
                row['DerivedName'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                # process Addresses
                row = self.process_addresses(row)

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                # format dates
                _ = datetime.strptime(row['StartDate'], '%d%b%Y')
                row['StartDateEmailSms'] = _.strftime('%d %B %Y')
                _ = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                row['ExpiryDateEmailSms'] = _.strftime('%d %B %Y')
                _ = datetime.strptime(row['StartDate'], '%d%b%Y')
                row['StartDatePost'] = _.strftime('%d %b %Y')
                _ = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                row['ExpiryDatePost'] = _.strftime('%d %b %Y')

                # email subject
                row['EmailSubject'] = self.email_subject(row)

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def business_rules(self, rows: list) -> list:
        pass

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # BR-AC4
            if len(row['raw_row']) != 915:
                self.report_invalid_row(row,
                                        reason='Invalid record size',
                                        position_data=[915, len(row['raw_row'])-915])
                return False

            # BR-AC6
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid registration number - blank field',
                                        position_data=headers['Registration_No'])
                return False

            # BR-AC10
            if not row['StartDateFormatted']:
                self.report_invalid_row(row,
                                        reason='Invalid start date',
                                        position_data=[headers['StartDD'][0], 11])
                return False

            # BR-AC12
            if not row['ExpiryDateFormatted']:
                self.report_invalid_row(row,
                                        reason='Invalid expiry date',
                                        position_data=[headers['ExpiryDD'][0], 11])
                return False

            # BR-AC14
            if row['ExtraFee1'] and int(row['ExtraFee1']):
                self.report_invalid_row(row,
                                        reason='Invalid extra fee',
                                        position_data=headers['ExtraFee1'])
                return False

            if row['ExtraFee2'] and int(row['ExtraFee2']):
                self.report_invalid_row(row,
                                        reason='Invalid extra fee',
                                        position_data=headers['ExtraFee2'])
                return False

            if row['ExtraFee3'] and int(row['ExtraFee3']):
                self.report_invalid_row(row,
                                        reason='Invalid extra fee',
                                        position_data=headers['ExtraFee3'])
                return False
            if row['ExtraFee4'] and int(row['ExtraFee4']):
                self.report_invalid_row(row,
                                        reason='Invalid extra fee',
                                        position_data=headers['ExtraFee4'])
                return False

            if row['ExtraFee5'] and int(row['ExtraFee5']):
                self.report_invalid_row(row,
                                        reason='Invalid extra fee',
                                        position_data=headers['ExtraFee5'])
                return False

            # BR-AC16
            if row['InConcession'] and row['InConcession'] != 'X':
                self.report_invalid_row(row,
                                        reason='Invalid concession',
                                        position_data=headers['InConcession'])
                return False

            # BR-AC18
            if not row['FeeCode']:
                self.report_invalid_row(row,
                                        reason='Invalid fee code',
                                        position_data=headers['FeeCode'])
                return False

            # BR-AC20
            # TODO: Confirm if right because the field length is only 4 char and this condition will never be true
            # if row['NhvConcssnText'] and row['NhvConcssnText'] not in [
            #     'PRIMARY PRODUCER - HEAVY TRAILER',
            #     'PRIMARY PRODUCER - HEAVY VEHICLE',
            #     'PRIMARY PRODUCER - HEAVY VEHICLE',
            #     'PRIMARY PRODUCER - HEAVY VEHICLE',
            #     'PRIMARY PRODUCER - PSV, TSV',
            #     'FIRE FIGHTING AND EMERGENCY RESPONSE VEHICLE',
            #     'PENSIONER / DVA CONCESSION',
            #     'DVA(TPI / EDA) CONCESSION',
            #     'HEALTH CARE CARD CONCESSION',
            #     'CHARITABLE, BENEVOLENT, RELIGIOUS INSTITUTION',
            #     'VEHICLE BUILT TO CARRY INCAPACITATED PERSON',
            #     'VEHICLE MOD FOR DRIVER WHO IS A WHEELCHAIR USER',
            #     'FRENCH ISLAND',
            #     'CONSULAR'
            # ]:
            #     self.report_invalid_row(row,
            #                             reason='Invalid heavy vehicle concession text',
            #                             position_data=headers['NhvConcssnTxt'])
            #     return False

            # BR-AC22
            if not row['VehicleDesc']:
                self.report_invalid_row(row,
                                        reason='Vehicle description is equal to space - invalid',
                                        position_data=headers['VehicleDesc'])
                return False

            # BR-AC24
            if not row['VehicleMake']:
                self.report_invalid_row(row,
                                        reason='Vehicle Make is equal to space - invalid',
                                        position_data=headers['VehicleMake'])
                return False

            # BR-AC26
            if row['CycleLevy'] and row['CycleLevy'] not in ['*', '#']:
                self.report_invalid_row(row,
                                        reason='Invalid Cycle levy',
                                        position_data=headers['CycleLevy'])
                return False

            # BR-AC28
            if row['HCCAmount'] and not row['HCCAmount'].isdigit():
                self.report_invalid_row(row,
                                        reason='Invalid HCCAmount',
                                        position_data=headers['HCCAmount'])
                return False

            # BR-AC30
            if not row[Structure.profile_table_mappings['client_id']] \
                    or len(row[Structure.profile_table_mappings['client_id']].strip()) != 8 \
                    or not row[Structure.profile_table_mappings['client_id']].isdigit():
                self.report_invalid_row(row,
                                        reason='Invalid customer number',
                                        position_data=headers[Structure.profile_table_mappings['client_id']])
                return False

            # BR-AC32
            if row['IsPaid'] and (row['PaymentDate'] and not row['PaymentDateFormatted']):
                self.report_invalid_row(row,
                                        reason='Invalid payment date',
                                        position_data=headers['PaymentDate'])
                return False

            # BR-AC34
            if not row['IsPaid']:
                manual_calculated_fee = self.convert_string_to_amount(row['RegoAmt']) + \
                                        self.convert_string_to_amount(row['InsurancePremium']) + \
                                        self.convert_string_to_amount(row['StampDuty']) + \
                                        self.convert_string_to_amount(row['NhvAdminFee']) + \
                                        self.convert_string_to_amount(row['ShortTermAdmFee']) + \
                                        self.convert_string_to_amount(row['PaperBillFee'])
                if manual_calculated_fee != self.convert_string_to_amount(row['TotalFeePayable']):
                    self.report_invalid_row(row,
                                            reason='Invalid total due',
                                            position_data=headers['TotalFeePayable'])
                    return False

        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

    # helpers
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

        formatted_addresses = self.get_formatted_address([row['ResAddress1'], row['ResAddress2'], row['ResAddress3']])
        row['ResAddress1'] = formatted_addresses[0]
        row['ResAddress2'] = formatted_addresses[1]
        row['ResAddress3'] = formatted_addresses[2]

        formatted_addresses = self.get_formatted_address([row['GarageAdd1'], row['GarageAdd2'], row['GarageAdd3']])
        row['GarageAdd1'] = formatted_addresses[0]
        row['GarageAdd2'] = formatted_addresses[1]
        row['GarageAdd3'] = formatted_addresses[2]

        return row

    # static helpers
    @staticmethod
    def get_output_channels_mapping(row):
        if row['FilePrefix'] in ['ovnrnew1', 'ovnrnew2', 'ovnrnew3', 'ovnrnew4', 'renew1', 'renew2']:
            if row['Email_Rqd_Ind'] == 'Y':
                row['Email_Required'] = 'Y'
                row['Mail_Required'] = 'N'
            else:
                row['Email_Required'] = 'N'
                row['Mail_Required'] = 'Y'
        elif row['FilePrefix'] in ['rgcrt1', 'rgcrt2']:
            if row['Email_Rqd_Ind'] == 'Y':
                row['Email_Required'] = 'Y'
                row['Mail_Required'] = 'Y'
            else:
                row['Email_Required'] = 'N'
                row['Mail_Required'] = 'Y'
        row['SMS_Required'] = 'N'
        return row

    # template mappings
    def email_subject(self, row) -> str:
        if row['FilePrefix'] in ['ovnrnew1', 'ovnrnew2', 'ovnrnew3', 'ovnrnew4', 'renew1', 'renew2']:
            if row['RecurPayInd'] == 'Y':
                return "We're processing your payment for rego {}".format(row['Registration_No'])
            if row['RecurPayInd'] == 'N':
                return "It's time to pay your rego {}".format(row['Registration_No'])
        elif row['FilePrefix'] in ['rgcrt1', 'rgcrt2']:
            return "Your record of your rego {} has been sent.".format(row['Registration_No'])

    def email_template(self) -> str:
        if self.row['FilePrefix'] in ['ovnrnew1', 'ovnrnew2', 'ovnrnew3', 'ovnrnew4', 'renew1', 'renew2']:
            return '{}/email-template.html'.format(self.product_family_name)
        elif self.row['FilePrefix'] in ['rgcrt1', 'rgcrt2']:
            return 'generic/template1.html'

    def sms_template(self) -> str:
        return '{}/sms-template.txt'.format(self.product_family_name)

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def html_template(self) -> str:
        return None
        # return '{}/html-template.html'.format(self.product_family_name)

    def history_title(self, row: dict) -> str:
        if row['FilePrefix'] in ['ovnrnew1', 'ovnrnew2', 'ovnrnew3', 'ovnrnew4', 'renew1', 'renew2']:
            return "Your rego for {} is due for renewal on {}. Please pay.".format(row['Registration_No'],
                                                                                   row['StartDatePost'])
        elif row['FilePrefix'] in ['rgcrt1', 'rgcrt2']:
            return "Your record of your rego {} for {} is attached.".format(row['Registration_No'],
                                                                            row['StartDatePost'])
        else:
            return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
