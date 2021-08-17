from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import date, datetime
from datetime import timedelta


class RegistrationRemindersNhvr(Structure):
    product_family_name = PRODUCT_FAMILY_REGISTRATION_REMINDER_NHVR
    supported_product_codes = [
        'nhvrrempart',
        'nhvrremfull',
        'nhvrRemBefFull',
        'nhvrRemAftFull',
        'nhvrRemBefPart',
        'nhvrRemAftPart'
    ]

    def parse(self, lines: list) -> list:
        headers = {
            'Name': [1, 26],
            'NameLine2': [27, 26],
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
            'TACInsuranceCodeandRiskZone': [249, 3],
            'DocumentType': [252, 2],
            'DailyRecordIndicator': [254, 1],
            'DayNumber': [255, 2],
            'Spare': [258, 1],
            'RecordSequenceNumber': [259, 5],
            'TACInsuranceRiskZone': [264, 6],
            'NhvIndicator': [270, 1],
            'NHVNumberofAxles': [271, 1],
            'NHVAdministrationFeeAmount': [272, 6],
            'NHVConcessionLevelCode': [278, 1],
            'NhvConcssnText': [279, 50],
            'NHVROADREGLIND': [329, 1],
            'NhvRoadUseFee': [330, 7],
            'NhvRegulatoryFee': [337, 7],
            'VehicleMake': [344, 6],
            'VehicleType': [350, 6],
            'VehiclePowerMassUnits': [356, 4],
            'FontCode': [360, 1],
            'VehicleDescription': [361, 14],
            'TITLE-TARE': [375, 5],
            'Tare': [380, 5],
            'TITLE-CAP': [385, 7],
            'CARRYING-CAPACITY': [392, 6],
            'TITLE-GVM': [398, 6],
            'GVM': [404, 6],
            'REG-TYPE-DESC-2': [410, 28],
            'PartYear': [438, 1],
            'VinNumber': [439, 20],
            'YearManufacture': [459, 2],
            'NhvCondCode': [461, 15],
            'FourWDInd': [476, 1],
            'InConcession': [477, 1],
            'InGoodsCarrying': [478, 3],
            'CountryCodeofthePostalAddress': [481, 3],
            'Pre-sortCodeforthePostalPostcode': [484, 3],
            'FeeCode': [487, 4],
            'RegType': [491, 22],
            'EngNumber': [513, 20],
            'TACInsuranceFeeAmountexcludingStam': [533, 11],
            'StampDuty': [544, 11],
            'CancellationDate': [555, 9],
            'ShortTermAdmFee': [564, 11],
            'PaperBillFee': [575, 11],
            'AmountField1': [586, 11],
            'AmountField2': [597, 11],
            'AmountField3': [608, 11],
            'AmountField4': [619, 11],
            'AmountField5': [630, 11],
            'AmountField6': [641, 11],
            'AmountField7': [652, 11],
            'AmountField8': [663, 11],
            'AmountField9': [674, 11],
            'AmountField10': [685, 11],
            Structure.profile_table_mappings['client_id']: [696, 8],
            'Email_Rqd_Ind': [704, 1],
            Structure.profile_table_mappings['email']: [705, 60],
            Structure.profile_table_mappings['phone']: [765, 19],
            'SMS_Rqd_Ind': [784, 1],
            'PortalAccountCustomerIndicator': [785, 1],
            'RecurPayInd': [786, 1],
            'ShortTermInd': [787, 1],
            'SerialChDigit': [788, 1],
            'Filler': [789, 16],
            'Fullstop': [805, 1]
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

                rows.append({**data_dict, **_line})

            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        valid_rows = self.business_rules(rows)
        processed_rows = self.perform_data_manipulation(valid_rows)
        return processed_rows

    # file validation business rules
    def business_rules(self, rows: list) -> list:
        filtered_rows = []

        for i, row in enumerate(rows):
            try:
                # BR1
                if not row['Registration_No']:
                    self.report_invalid_row(row, reason='Invalid licence number - blank field')
                    continue

                # BR2
                if len(row['raw_row']) != 807:
                    self.report_invalid_row(row, reason='Invalid record size')
                    continue

                # BR18
                if not row[Structure.profile_table_mappings['client_id']] \
                        or len(row[Structure.profile_table_mappings['client_id']].strip()) != 8\
                        or not row[Structure.profile_table_mappings['client_id']].isdigit():
                    self.report_invalid_row(row, reason='Invalid customer number')
                    continue

                filtered_rows.append(row)

            except Exception as e:
                logger.warning('failed processing business rules', extra={'data': str(e)})
                continue

        return filtered_rows

    # data transformation stuff
    def perform_data_manipulation(self, rows: list) -> list:
        for row in rows:
            try:
                # PBR3 equivalent for reg reminders
                row['ExpiryDate'] = row['ExpiryDate'].replace('JLY', 'JUL')
                row['CancellationDate'] = row['CancellationDate'].replace('JLY', 'JUL')

                # format and concatenate dates
                row['ExpiryDate'] = self.get_formatted_date(row['ExpiryDate'])
                row['CancellationDate'] = self.get_formatted_date(row['CancellationDate'])

                # Email Type
                if not row['FeeCode'].startswith('B') and \
                        row['FilePrefix'] not in ['remfull', 'rempart'] and \
                        row['RecurPayInd'] == 'N':
                    row['EmailType'] = 'PaymentReminder'
                elif not row['FeeCode'].startswith('B') and \
                        row['FilePrefix'] in ['remfull', 'rempart']:
                    row['EmailType'] = 'RegoOverdue'

                # clean address fields
                address_fields_list = ['Post_Address_1', 'Post_Address_2', 'Post_Suburb', 'PostCode', 'ResAddress1', 'ResAddress2', 'ResPostcode']
                for i in address_fields_list:
                    row[i] = row[i].replace('<', ' ').replace('>', ' ')
                row['Post_State'] = self.state_by_code(row['PostCode'])
                row['ResState'] = self.state_by_code(row['ResPostcode'])

                # generate ICRN number
                row['IcrnNumber'] = self.generate_icrn_number(row)

                # PBR2, applicable only for vessel reminder letter
                if row['FeeCode'].startswith('B'):
                    today = date.today()
                    offset = (today.weekday() - 3) % 7
                    last_thursday = today - timedelta(days=offset)
                    row['ThursdayReleaseDate'] = last_thursday.strftime("%d %B %Y")

                # Expiry Date calculation
                row['Calculated_ExpiryDate'] = self.calculate_expiry_date(row)

                # barcode calculation
                row['AusPostBarcodeBase64'] = self.generate_auspost_barcode(row)
                row['OfficeUseBarcodeBase64'] = self.generate_office_use_barcode(row)

                # PBR5
                total_fee_payable_formatted = float(row['TotalFeePayable']) / 100
                row['PaymentCode'] = "{} {}  {}  {}  {}".format(row['Registration_No'],
                                                                row['SerialChDigit'],
                                                                str(row['Calculated_ExpiryDate']),
                                                                row['SerialNumber'],
                                                                str(total_fee_payable_formatted))

                # get data mappings
                row = self.panel_show_hide_messages(row)

                # output channel mappings
                row = self.user_output_channels_mapping(row)
                row = self.get_output_channels_mapping(row)

                # bounce back check TODO
                row['BounceBack'] = 0

                # vehicle heading
                if row['VehicleDescription'].lower() == 'Trailer'.lower():
                    row['VehicleHeading'] = 'Trailer'
                elif row['VehicleDescription'].lower() == 'CAR'.lower():
                    row['VehicleHeading'] = 'Motor vehicle'
                else:
                    row['VehicleHeading'] = 'Motor cycle'

                # format currency
                row['TotalFeePayable'] = self.get_currency(str(int(row['TotalFeePayable']) / 100))
                row['RegoAmt'] = self.get_currency(row['RegoAmt'])
                row['InsurancePremium'] = self.get_currency(row['InsurancePremium'])
                row['StampDuty'] = self.get_currency(row['StampDuty'])
                row['ServiceFee'] = self.get_currency(row['ShortTermAdmFee'])
                row['PaperBillFee'] = self.get_currency(row['PaperBillFee'])

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
    def generate_icrn_number(self, row):
        icrn_ref = row['SerialNumber'].zfill(9)
        exp_date = datetime.strptime(self.get_formatted_date(row['ExpiryDate']), '%d %B %Y')
        icrn_date = exp_date.strftime('%Y/%m/%d')
        icrn_amount = row['TotalFeePayable'].lstrip("0")
        return self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

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
            '',
            row['ResState'],
            row['ResPostcode'])

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

        return row

    # static methods
    @staticmethod
    def panel_show_hide_messages(row):
        row['ShowSetAndForget'] = 0
        row['ShowAddConcessionLeft'] = 0
        row['ShowAddConcessionRight'] = 0
        row['ShowHealthcareMessage'] = 0
        row['ShowEngNumber'] = 0
        row['ShowOnlyTare'] = 0
        row['ShowShortRegoImage'] = 0
        row['ShowConcessionDeductedMessage'] = 0
        row['ShowSwitchShortRegoMessage'] = 0
        row['ShowChooseShortRegoMessage'] = 0

        if row['FeeCode'] in ['CP', 'CQ', 'CS', 'JP', 'JQ', 'JW', 'VJ', 'VK', 'VL']:
            if row['ShortTermInd'] == 'Y':
                row['ShowAddConcessionLeft'] = 1
            else:
                row['ShowAddConcessionRight'] = 1

        if row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR', 'JH', 'PF', 'PT', 'PR', 'PH', 'VL'] and \
                row['Email_Rqd_Ind'] != 'Y':
            row['ShowSetAndForget'] = 1

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

        if row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR', 'JH', 'PF', 'PT', 'PR', 'PH', 'VL']:
            row['ShowShortRegoImage'] = 1

        if row['FeeCode'] in ['CH', 'CZ', 'CU', 'JH', 'JZ', 'JU', 'PH', 'PZ', 'PV']:
            row['ShowConcessionDeductedMessage'] = 1

        if row['NhvIndicator'] not in ['X', 'Y'] and \
                not row['ShortTermAdmFee'] and \
                row['PartYear'] in ['1', '2', '3', '4', '5', '6'] and \
                row['FeeCode'] in ['AU', 'CF', 'CP', 'CU', 'CW', 'EQ', 'ER', 'FF', 'FJ', 'FW', 'GG', 'JP', 'JT',
                                         'JU', 'PG', 'PS', 'PU', 'PV', 'VJ', 'AS', 'CE', 'CQ', 'ES', 'FC', 'FK', 'GF',
                                         'JQ', 'PE', 'VK', 'PX', 'PY', 'JX', 'FX', 'EX', 'CX']:
            row['ShowSwitchShortRegoMessage'] = 1

        if row['NhvIndicator'] not in ['X', 'Y'] and \
                row['FeeCode'] in ['AT', 'CB', 'CS', 'CH', 'CR', 'ET', 'EN', 'FL', 'FN', 'FI', 'GE', 'JW', 'JR',
                                   'JH', 'PF', 'PT', 'PR', 'PH', 'VL']:
            row['ShowChooseShortRegoMessage'] = 1
        return row

    @staticmethod
    def get_output_channels_mapping(row):
        if row['FilePrefix'] in ['RemAftFull', 'RemAftPart']:
            row['Mail_Required'] = 'N'
            row['Email_Required'] = 'N'
            if row['SMS_Rqd_Ind'] == 'Y':
                row['SMS_Required'] = 'Y'
            else:
                row['SMS_Required'] = 'N'

        if row['FilePrefix'] in ['RemBefFull', 'RemBefPart']:
            row['Mail_Required'] = 'N'
            if row['PortalAccountCustomerIndicator'] == 'Y' and \
                    row['Email_Rqd_Ind'] == 'Y' and \
                    row['RecurPayInd'] == 'N' and \
                    not row['FeeCode'].startswith('B'):
                row['Email_Required'] = 'Y'
                row['EmailType'] = 'PaymentReminder'
            else:
                row['Email_Required'] = 'N'
            row['SMS_Required'] = 'N'

        if row['FilePrefix'] in ['remfull', 'rempart']:
            if row['FeeCode'].startswith('B'):
                row['Mail_Required'] = 'Y'
                row['Email_Required'] = 'N'
            else:
                if row['Email_Rqd_Ind'] == 'N':
                    row['Mail_Required'] = 'Y'
                    row['Email_Required'] = 'N'
                elif row['Email_Rqd_Ind'] == 'Y':
                    row['Mail_Required'] = 'N'
                    row['Email_Required'] = 'Y'
                    row['EmailType'] = 'RegoOverdue'
            row['SMS_Required'] = 'N'
        return row

    @staticmethod
    def calculate_expiry_date(row):
        if row['ExpiryDate']:
            calculated_date = datetime.strptime(row['ExpiryDate'], '%d %B %Y')
            return calculated_date.strftime('%d%m%y')
        else:
            return ''

    # template mappings
    def email_subject(self, row) -> str:
        if self.row['FilePrefix'] in ['remfull', 'rempart']:
            return "Your rego {} is overdue".format(self.row['Registration_No'])
        else:
            return "Don't forget, it's time to pay your rego"

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
