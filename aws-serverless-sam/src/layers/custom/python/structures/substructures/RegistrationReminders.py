from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RegistrationReminders(Structure):
    product_family_name = PRODUCT_FAMILY_REGISTRATION_REMINDER
    supported_product_codes = [
        'rempart',
        'remfull',
        'RemBefFull',
        'RemAftFull',
        'RemBefPart',
        'RemAftPart'
    ]

    def parse(self, lines: list) -> list:
        headers = {
            'Name': [1, 52],
            'Post_Address_1': [53, 26],
            'Post_Address_2': [79, 26],
            'Post_Suburb': [105, 20],
            'PostCode': [125, 4],
            'ResAddress1': [129, 26],
            'ResAddress2': [155, 20],
            'ResPostcode': [175, 4],
            'SerialNumber': [179, 7],
            'ExpiryDate': [186, 9],
            'Registration_No': [195, 6],
            'Reg_checkDigit': [201, 1],
            'TotalFeePayable': [202, 11],
            'SumCheck': [213, 12],
            'RegoAmt': [225, 11],
            'InsuranceCode': [236, 2],
            'InsurancePremium': [238, 11],
            'TACInsuranceCodeandRiskZone': [249, 2],
            'Filler': [251, 1],
            'DocumentType': [252, 2],
            'DailyRecordIndicator': [254, 1],
            'DayNumber': [255, 3],
            'Spare': [258, 1],
            'RecordSequenceNumber': [259, 5],
            'TACInsuranceRiskZone': [264, 6],
            'NhvIndicator': [270, 1],
            'NHVNumberofAxles': [271, 1],
            'NHVAdministrationFeeAmount': [272, 6],
            'NHVConcessionLevelCode': [278, 1],
            'NHVConcessionLevelText': [279, 4],
            'VehicleMake': [283, 6],
            'VehicleType': [289, 6],
            'VehiclePowerMassUnits': [295, 4],
            'FontCode': [299, 1],
            'VehicleDesc': [300, 14],
            'Furtherdatawhichdescrib': [314, 33],
            'Furtherdatawhichdescrib2': [347, 28],
            'PartYear': [375, 1],
            'VinNumber': [376, 20],
            'YearManufacture': [396, 2],
            'NHVConditionCodes': [398, 15],
            'FourWDInd': [413, 1],
            'InConcession': [414, 1],
            'GoodsCarryingIndicator': [415, 3],
            'CountryCodeofthePostalAddress': [418, 3],
            'Pre-sortCodeforthePostalPostcode': [421, 3],
            'FeeCode': [424, 4],
            'RegType': [428, 22],
            'EngNumber': [450, 20],
            'TacExcludingStampDuty': [470, 11],
            'StampDuty': [481, 11],
            'CancellationDate': [492, 9],
            'ShortTermAdmFee': [501, 11],
            'PaperBillFee': [512, 11],
            'AmountField1': [523, 11],
            'AmountField2': [534, 11],
            'AmountField3': [545, 11],
            'AmountField4': [556, 11],
            'AmountField5': [567, 11],
            'AmountField6': [578, 11],
            'AmountField7': [589, 11],
            'AmountField8': [600, 11],
            'AmountField9': [611, 11],
            'AmountField10': [622, 11],
            Structure.profile_table_mappings['client_id']: [633, 8],
            'Email_Rqd_Ind': [641, 1],
            Structure.profile_table_mappings['email']: [642, 60],
            Structure.profile_table_mappings['phone']: [702, 19],
            'SMS_Rqd_Ind': [721, 1],
            'PortalAccountCustomerIndicator': [722, 1],
            'RecurPayInd': [723, 1],
            'ShortTermInd': [724, 1],
            'SerialChDigit': [725, 1],
            'Filler2': [726, 18]
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

                filename = _line['raw_filename']
                data_dict['FilePrefix'] = self.get_prefix_from_filename(filename)

                row = {**data_dict, **_line}

                if not self.validate_business_rules(row, headers):
                    continue

                # MR-AC3
                row['ExpiryDate'] = row['ExpiryDate'].replace('JLY', 'JUL')
                row['CancellationDate'] = row['CancellationDate'].replace('JLY', 'JUL')

                # format dates
                _ = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                row['ExpiryDateVesselEmailSms'] = _.strftime('%d %B %Y')
                _ = datetime.strptime(row['CancellationDate'], '%d%b%Y')
                row['CancellationDateVesselEmailSms'] = _.strftime('%d %B %Y')
                _ = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                row['ExpiryDatePost'] = _.strftime('%d %b %Y')
                _ = datetime.strptime(row['CancellationDate'], '%d%b%Y')
                row['CancellationDatePost'] = _.strftime('%d %b %Y')

                # output channel mappings
                row = self.user_output_channels_mapping(row)
                row = self.get_output_channels_mapping(row)

                # US-AC11 to 13 US-AC56
                # clean address fields
                address_fields_list = ['Post_Address_1', 'Post_Address_2', 'Post_Suburb', 'PostCode']
                for field in address_fields_list:
                    row[field] = row[field].replace('<', ' ').replace('>', ' ')

                # US-AC14 to 26
                row['Post_State'] = self.state_by_code(row['PostCode'])

                # US-AC13
                # generate address line3
                row['Post_Address_3'] = self.get_address_line3(
                    row['Post_Suburb'],
                    row['Post_State'],
                    row['PostCode'])
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                if not row['FeeCode'].startswith('B'):
                    # remove decimals from total fee payable and rego amount if any to work with
                    row['TotalFeePayable'] = row['TotalFeePayable'].replace('.', '', 1)
                    row['RegoAmt'] = row['RegoAmt'].replace('.', '', 1)

                    # generate icrn, auspost barcode & payment code only when not direct debit
                    prev_exp_date = datetime.strptime(row['ExpiryDate'], '%d%b%Y')
                    cancellation_date = datetime.strptime(row['CancellationDate'], '%d%b%Y')
                    if row['PartYear'] == 'Y':
                        new_exp_date = prev_exp_date + relativedelta(months=+3)
                    else:
                        new_exp_date = cancellation_date

                    # US-AC50 MR-AC7 MR-AC8
                    # icrn number
                    icrn_ref = "1{}".format(row['SerialNumber'].zfill(8))
                    icrn_date = new_exp_date.strftime('%Y/%m/%d')
                    icrn_amount = row['TotalFeePayable'].lstrip('0')
                    row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

                    # US-AC51 MR-AC4 MR-AC5
                    # Aus post barcode
                    barcode_expiry_date = new_exp_date.strftime('%d%m%y')
                    code_string = '374' + row['SerialNumber'] + row['SerialChDigit'] + \
                                  row['TotalFeePayable'][-9:].zfill(9) + str(barcode_expiry_date)
                    text = '*374' + ' ' + row['SerialNumber'] + row['SerialChDigit'] + ' ' + str(barcode_expiry_date)
                    code = 'code128'
                    row['AusPostBarcodeBase64'] = self.barcode(code_string, text, code)

                    # US-AC51 MR-AC6
                    # Payment code
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

                    # variables to show/hide content
                    row['ShowSetAndForget'] = 0
                    row['ShowAddConcessionRight'] = 0
                    row['ShowConcessionDeductedMessage'] = 0
                    row['ShowSwitchShortRego3MthsMessage'] = 0
                    row['ShowSwitchShortRego6MthsMessage'] = 0
                    row['ShowChooseShortRegoMessage'] = 0

                    if row['InConcession'] == 'N' and \
                            (row['FeeCode'] in ['EN', 'ER', 'EX', 'GE', 'GF', 'GG',
                                                'JP', 'JQ', 'JW', 'VJ', 'VK', 'VL'] or
                             (row['FeeCode'] in ['CP', 'CQ', 'CS'] and not row['InsuranceCode'].startswith('43'))):
                        row['ShowAddConcessionRight'] = 1

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

                    # US-AC39
                    if row['NhvIndicator'] != 'Y' and \
                            row['FeeCode'] in ['AT', 'CB', 'CH', 'CR', 'CS', 'EN', 'ET', 'FI', 'FL', 'FN',
                                               'GE', 'JH', 'JR', 'JW', 'PF', 'PH', 'PR', 'PT', 'VL']:
                        row['ShowChooseShortRegoMessage'] = 1

                    if row['InConcession'] == 'Y' and \
                            row['FeeCode'] in ['CH', 'CR', 'CU', 'CW', 'CX', 'CZ', 'JH', 'JU', 'JZ', 'PH',
                                               'PR', 'PS', 'PT', 'PU', 'PV', 'PX', 'PY', 'PZ']:
                        row['ShowConcessionDeductedMessage'] = 1

                    # US-AC40
                    # bounce back check TODO
                    row['BounceBack'] = 0

                    feereg = [row['FeeCode'], row['RegType']]
                    row['FeeRegDetails'] = ' '.join(x for x in feereg if x)

                    # US-AC61 US-AC62 US-AC63
                    # vehicle heading
                    if row['VehicleDesc'].upper() == 'TRAILER':
                        row['VehicleHeading'] = 'Trailer'
                    elif row['VehicleDesc'].upper() == 'MOTOR VEHICLE' or row['VehicleDesc'].upper() == 'CAR':
                        row['VehicleHeading'] = 'Motor vehicle'
                    elif row['VehicleDesc'].upper() == 'MOTOR CYCLE' or row['VehicleDesc'].upper() == 'CYCLE':
                        row['VehicleHeading'] = 'Motor cycle'

                    row['VehicleMake'] = row['VehicleMake'].title()
                    row['VehicleType'] = row['VehicleType'].title()

                    # format fees
                    row['TotalFeePayable'] = self.get_currency(row['TotalFeePayable'])
                    row['RegoAmt'] = self.get_currency(row['RegoAmt'])
                    row['TacExcludingStampDuty'] = self.get_currency(row['TacExcludingStampDuty'])
                    row['StampDuty'] = self.get_currency(row['StampDuty'])
                    row['ServiceFee'] = self.get_currency(row['ShortTermAdmFee'])
                    row['PaperBillFee'] = self.get_currency(row['PaperBillFee'])

                    # residential address processing only for vehicles
                    # US-AC11 to 13 US-AC56
                    # clean address fields
                    address_fields_list = ['ResAddress1', 'ResAddress2', 'ResPostcode']
                    for field in address_fields_list:
                        row[field] = row[field].replace('<', ' ').replace('>', ' ')

                    # US-AC14 to 26
                    row['ResState'] = self.state_by_code(row['ResPostcode'])

                    # US-AC13
                    # generate address line3
                    row['ResAddress3'] = self.get_address_line3(
                        '',
                        row['ResState'],
                        row['ResPostcode'])
                    formatted_addresses = self.get_formatted_address([row['ResAddress1'], row['ResAddress2'], row['ResAddress3']])
                    row['ResAddress1'] = formatted_addresses[0]
                    row['ResAddress2'] = formatted_addresses[1]
                    row['ResAddress3'] = formatted_addresses[2]

                # US-AC10
                # convert name to capital case
                row['DerivedName'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # BR-AC4
            if len(row['raw_row']) != 744:
                self.report_invalid_row(row,
                                        reason='Invalid record size',
                                        position_data=[744, len(row['raw_row']) - 744])
                return False

            # BR-AC6
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid registration number - blank field',
                                        position_data=headers['Registration_No'])
                return False

            # BR-AC8
            if row['InConcession'] and row['InConcession'] not in ['Y', 'N']:
                self.report_invalid_row(row,
                                        reason='Invalid concession',
                                        position_data=headers['InConcession'])
                return False

            # BR-AC10
            if not row['FeeCode']:
                self.report_invalid_row(row,
                                        reason='Invalid fee code',
                                        position_data=headers['FeeCode'])
                return False

            # BR-AC12
            if not row['VehicleDesc']:
                self.report_invalid_row(row,
                                        reason='Vehicle description is equal to space - invalid',
                                        position_data=headers['VehicleDesc'])
                return False

            # BR-AC14
            if not row['VehicleMake']:
                self.report_invalid_row(row,
                                        reason='Vehicle make is equal to space - invalid',
                                        position_data=headers['VehicleMake'])
                return False

            # BR-AC16
            if not row[Structure.profile_table_mappings['client_id']] \
                    or len(row[Structure.profile_table_mappings['client_id']].strip()) != 8 \
                    or not row[Structure.profile_table_mappings['client_id']].isdigit():
                self.report_invalid_row(row,
                                        reason='Invalid customer number',
                                        position_data=headers[Structure.profile_table_mappings['client_id']])
                return False

        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

    @staticmethod
    def get_output_channels_mapping(row):
        if row['FilePrefix'] in ['RemAftFull', 'RemAftPart']:
            row['Mail_Required'] = 'N'
            row['Email_Required'] = 'N'
            if row['SMS_Rqd_Ind'] == 'Y':
                row['SMS_Required'] = 'Y'
            else:
                row['SMS_Required'] = 'N'
            row['HistoryTitle'] = "Your rego for {} expired on {}".format(row['Registration_No'],
                                                                          row['ExpiryDatePost'])

        if row['FilePrefix'] in ['RemBefFull', 'RemBefPart']:
            if row['FeeCode'].startswith('B'):
                row['Mail_Required'] = 'N'
                row['Email_Required'] = 'N'
                row['SMS_Required'] = 'N'
            else:
                if row['Email_Rqd_Ind'] == 'Y' and row['RecurPayInd'] == 'N':
                    row['Mail_Required'] = 'N'
                    row['Email_Required'] = 'Y'
                    row['EmailType'] = 'PaymentReminder'
                    row['EmailSubject'] = "Don't forget, your rego for {} will expire on {}".format(
                        row['Registration_No'], row['ExpiryDatePost'])
                    row['HistoryTitle'] = "Don't forget, your rego for {} will expire on {}".format(
                        row['Registration_No'], row['ExpiryDatePost'])
                    row['SMS_Required'] = 'N'
                else:
                    row['Mail_Required'] = 'N'
                    row['Email_Required'] = 'N'
                    row['SMS_Required'] = 'N'

        if row['FilePrefix'] in ['remfull', 'rempart']:
            row['HistoryTitle'] = "Your rego for {} expired on {}. Final overdue notice.".format(
                row['Registration_No'], row['ExpiryDatePost'])
            if row['FeeCode'].startswith('B'):
                row['Email_Required'] = 'N'
                row['Mail_Required'] = 'Y'
                row['SMS_Required'] = 'N'
            else:
                if row['Email_Rqd_Ind'] == 'N':
                    row['Mail_Required'] = 'Y'
                    row['Email_Required'] = 'N'
                elif row['Email_Rqd_Ind'] == 'Y':
                    row['Mail_Required'] = 'N'
                    row['Email_Required'] = 'Y'
                    row['EmailType'] = 'RegoOverdue'
                    row['EmailSubject'] = "Your rego {} is overdue".format(row['Registration_No'])
                    row['SMS_Required'] = 'N'
        return row

    # template mappings
    def email_subject(self, row) -> str:
        if self.row['EmailSubject']:
            return self.row['EmailSubject']
        else:
            return ''

    def email_template(self) -> str:
        #need to check if EmailType exists in row as Merge_Correspondence makes a call to email_template for all products
        if 'EmailType' in self.row.keys():
            if self.row['EmailType'] == 'Generic':
                return 'generic/template1.html'
            else:
                return '{}/email-template.html'.format(self.product_family_name)
        else:
            return None

    def sms_template(self) -> str:
        return '{}/sms-template.txt'.format(self.product_family_name)

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def html_template(self) -> str:
        return None
        # return '{}/html-template.html'.format(self.product_family_name)

    def history_title(self, row: dict) -> str:
        if row['HistoryTitle']:
            return row['HistoryTitle']
        else:
            return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
