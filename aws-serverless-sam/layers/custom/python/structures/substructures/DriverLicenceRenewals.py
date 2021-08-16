from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta
from handlers import CSCLookup
import re
import json


class DriverLicenceRenewals(Structure):
    product_family_name = PRODUCT_FAMILY_DRIVER_LICENCE_RENEWALS
    supported_product_codes = ['pndl2650']

    def parse(self, lines: list):
        headers = {
            'Rec_ID': [1, 2],
            Structure.profile_table_mappings['client_id']: [3, 9],
            'Name': [12, 27],
            'Name_Inc_Title': [39, 27],
            'Name_Office_Copy': [66, 20],
            'Page_Count': [86, 6],
            'Post_Address_1': [92, 27],
            'Post_Address_2': [119, 27],
            'Post_Address_3': [146, 25],
            'ResAdd1': [171, 27],
            'ResAdd2': [198, 27],
            'ResAdd3': [225, 25],
            'Last_ResAdd1': [250, 27],
            'Last_ResAdd2': [277, 27],
            'Last_ResAdd3': [304, 25],
            'Exp_Date': [329, 10],
            'DOB': [339, 10],
            'Licence_Fee': [349, 8],
            'Licence_Desc_1': [357, 25],
            'Licence_Desc_2': [382, 25],
            'Total_Fee': [407, 8],
            'Licence_Category_1': [415, 1],
            'Licence_Category_2': [416, 1],
            'Licence_Category_3': [417, 1],
            'Licence_Category_4': [418, 1],
            'Licence_Category_5': [419, 1],
            'Licence_Category_6': [420, 1],
            'Licence_Category_7': [421, 1],
            'Licence_Category_8': [422, 1],
            'Photo_Reason': [423, 11],
            'Prob_End_Date': [434, 10],
            'Prob_Exp_Text': [444, 11],
            'LMCode': [455, 3],
            'Warn_Text': [458, 58],
            'Prev_Exp': [516, 10],
            'PhotoFlag': [526, 1],
            'Over75Flag': [527, 1],
            'NDisFlag': [528, 1],
            'Photo_by_date': [529, 10],
            'WS_RenP2_Full': [539, 1],
            'WS_RenTypePRB': [540, 2],
            'WS_RenP1_P2': [542, 1],
            'DT_P2_Start': [543, 10],
            'DT_P2_End': [553, 10],
            'DT_P1_End': [563, 10],
            'Filler': [573, 28]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[2:7])

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
                                    position_data=[3, 5])
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

                # get renewal years
                exp_date = datetime.strptime(self.get_formatted_date(row['Exp_Date']), '%d %B %Y')
                prev_exp_date = datetime.strptime(self.get_formatted_date(row['Prev_Exp']), '%d %B %Y')
                row['RenewalYears'] = relativedelta(exp_date, prev_exp_date).years

                if not self.validate_business_rules(row, headers):
                    continue

                skip_record = 0

                # validate if any of the following dates are of wrong format -
                dates_to_validate = ['Exp_Date', 'Prev_Exp', 'DT_P2_Start',
                                     'DT_P2_End', 'DT_P1_End', 'DOB', 'Prob_End_Date']
                for d in dates_to_validate:
                    date_str = row['{}'.format(d)]
                    if date_str:
                        formatted_date = self.get_formatted_date(date_str)
                        if not formatted_date:
                            self.report_invalid_row(_line,
                                                    reason='Invalid date format',
                                                    position_data=headers['{}'.format(d)])
                            skip_record = 1
                            break
                        else:
                            row['{}'.format(d)] = formatted_date
                if skip_record:
                    continue

                filename = _line['raw_filename']
                row['file_prefix'] = filename.split('_')[0].split('.')[0]

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

                # get current date
                row['SystemDate'] = self.get_current_system_date()

                # generate licence type name
                self.get_licence_type_mappings(row)

                # auspost code generation
                client_no = row[Structure.profile_table_mappings['client_id']]

                calculated_date = prev_exp_date + relativedelta(months=+6)
                barcode_calculated_payment_date = calculated_date.strftime('%d%m%y')

                licence_fee = row['Licence_Fee'].replace('.', '')
                calculated_licence_fee = licence_fee.zfill(9)

                code_string = "536{}{}{}".format(client_no.zfill(10), barcode_calculated_payment_date, calculated_licence_fee)
                text = "*536 {} {}".format(client_no.zfill(10), barcode_calculated_payment_date)
                code = 'code128'
                row['AusPostBarcodeBase64'] = self.barcode(code_string, text, code)

                # csc barcode generation
                row['CscBarcodeCode'] = "*{}*".format(client_no.zfill(9))
                row['CscBarcodeText'] = "{} {}".format(client_no.zfill(9), row['LMCode'])

                # generate ICRN number
                self.generate_icrn_number(row)

                # data mapping
                row['AmountDue'] = self.get_currency(row['Total_Fee'])
                row['DueDate'] = self.get_formatted_date(row['Prev_Exp'])
                if row['Name_Inc_Title']:
                    row['DerivedName'] = row['Name_Inc_Title'].title()
                else:
                    row['DerivedName'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                # email subject
                row['EmailSubject'] = self.email_subject(row)

                # conditionals
                if row['NDisFlag'].lower() == 'f':
                    row['ShouldPrintGoodDrivingMessage'] = 0
                    row['PayOrRenew1'] = "payment"
                    row['PayOrRenew2'] = "payment"
                    if row['PhotoFlag'].lower() == 'y':
                        row['RenewalPaymentMessage'] = "PaidLicencePhotoRequired"
                    else:
                        row['RenewalPaymentMessage'] = "PaidLicenceNoPhotoRequired"
                else:
                    row['ShouldPrintGoodDrivingMessage'] = 1
                    row['PayOrRenew1'] = "renewal"
                    row['PayOrRenew2'] = "you renew"
                    if row['PhotoFlag'].lower() == 'y':
                        row['RenewalPaymentMessage'] = "FreeLicencePhotoRequired"
                    else:
                        row['RenewalPaymentMessage'] = "FreeLicenceNoPhotoRequired"

                if row['PhotoFlag'].lower() == 'y':
                    # lookup closest csc
                    self.lookup_closest_csc(row)

                # onsert requirements
                if row['Over75Flag'] == 'T' or row['PhotoFlag'] == 'Y':
                    row['OnsertRequired'] = 1
                    row['OnsertMergeAtStart'] = 0
                    row['OnsertsToMerge'] = []
                    if row['Over75Flag'] == 'T':
                        row['OnsertsToMerge'].append("Over75Onsert.pdf")
                    if row['PhotoFlag'] == 'Y':
                        row['OnsertsToMerge'].append("PhotoLocations.pdf")

                # licence code mappings
                row['LicenceCodesMapped'] = self.get_licence_code_mappings(row['Licence_Desc_1'])

                # licence conditions string
                self.get_licence_conditions_str(row)

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

            # invalid record if RecId not PO, NO or HI
            if row['Rec_ID'] not in ["PO", "NO", "HI"]:
                self.report_invalid_row(row,
                                        reason='Invalid record ID',
                                        position_data=headers['Rec_ID'])
                return False

            # validate renewal years
            if row['RenewalYears'] not in [3, 4, 10]:
                self.report_invalid_row(row,
                                        reason='Invalid renewal years',
                                        position_data=headers['Exp_Date'])
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
        return 'It’s time to pay your driver licence renewal'

    def history_title(self, row) -> str:
        return 'Your driver licence is due for renewal. Please pay.'

    def lookup_closest_csc(self, row):
        # extract postcode from address line
        if row['ResAdd2']:
            if not row['ResAdd3']:
                postcode = self.get_postcode_from_address(row['ResAdd2'])
            else:
                postcode = self.get_postcode_from_address(row['ResAdd3'])
        elif row['ResAdd3']:
            postcode = self.get_postcode_from_address(row['ResAdd3'])
        else:
            row['NearestCscInfo'] = 0
            return

        if not postcode:
            row['NearestCscInfo'] = 0
            return

        # lookup extracted postcode in CSC LUT
        nearest_csc = CSCLookup.get_closest_csc(postcode)

        # set variable to determine if nearest csc info is available
        if not nearest_csc:
            row['NearestCscInfo'] = 0
        else:
            row['NearestCscInfo'] = 1
            if not nearest_csc['csc_name']:
                row['NearestCscName'] = ' '
            else:
                row['NearestCscName'] = nearest_csc['csc_name']
            if not nearest_csc['csc_address_1']:
                row['NearestCscAddress1'] = ' '
            else:
                row['NearestCscAddress1'] = nearest_csc['csc_address_1']
            if not nearest_csc['csc_address_2']:
                row['NearestCscAddress2'] = ' '
            else:
                row['NearestCscAddress2'] = nearest_csc['csc_address_2']
            if not nearest_csc['csc_address_3']:
                row['NearestCscAddress3'] = ' '
            else:
                row['NearestCscAddress3'] = nearest_csc['csc_address_3']

    def generate_icrn_number(self, row):
        client_no = row[Structure.profile_table_mappings['client_id']]
        prev_exp_date = datetime.strptime(self.get_formatted_date(row['Prev_Exp']), '%d %B %Y')

        calculated_date = prev_exp_date + relativedelta(months=+6)
        icrn_ref = client_no.zfill(9)
        icrn_ref = '2' + icrn_ref[1:]
        icrn_date = calculated_date.strftime('%Y/%m/%d')

        icrn_amount = row['Total_Fee'].replace('.', '')

        row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

    @staticmethod
    def get_licence_code_mappings(desc_string: str):
        # licence codes mapping
        licence_code_mappings = {'CAR': 'Car',
                                 'R': 'Motorcycle (R)',
                                 'LR': 'Light Rigid',
                                 'MR': 'Medium Rigid',
                                 'HR': 'Heavy Rigid',
                                 'HC': 'Heavy Combination',
                                 'MC': 'Multi Combination'}

        def replace(match):
            return licence_code_mappings[match.group(0)]

        desc_list = desc_string.split(' ')
        desc_string = ', '.join(filter(None, desc_list))

        pattern = '|'.join(r'\b%s\b' % re.escape(s) for s in licence_code_mappings)
        return re.sub(pattern, replace, desc_string)

    @staticmethod
    def get_licence_type_mappings(row):
        row['LicenceTypeName'] = " "
        if row['Rec_ID'] == 'PO' and row['WS_RenTypePRB'] == 'P1':
            row['LicenceTypeName'] = "Probationary P1"
        elif row['Rec_ID'] == 'PO' and row['WS_RenTypePRB'] == 'P2':
            row['LicenceTypeName'] = "Probationary P2"
        elif row['Rec_ID'] == 'HI' and row['WS_RenTypePRB'] not in ['P1', 'P2']:
            row['LicenceTypeName'] = "Heavy Vehicle"
        elif row['Rec_ID'] == 'HI' and row['WS_RenTypePRB'] == 'P1':
            row['LicenceTypeName'] = "P1 Heavy Vehicle"
        elif row['Rec_ID'] == 'HI' and row['WS_RenTypePRB'] == 'P2':
            row['LicenceTypeName'] = "P2 Heavy Vehicle"

    @staticmethod
    def get_licence_conditions_str(row):
        licence_conditions_list = [row['Licence_Category_1'], row['Licence_Category_2'],
                                   row['Licence_Category_3'], row['Licence_Category_4'],
                                   row['Licence_Category_5'], row['Licence_Category_6'],
                                   row['Licence_Category_7'], row['Licence_Category_8']]
        row['Licence_conditions'] = ' '.join(
            x.strip() for x in filter(None, licence_conditions_list) if x.strip())
        if not row['Licence_conditions'] or row['Licence_conditions'] == ' ':
            row['Licence_conditions'] = 'None'

    def correspondence_metadata(self, row) -> str:
        data_set = {
            "FreeLicenceEligibilityData":
                {
                    "NDisFlag": row['NDisFlag'],
                    "DueDate": row['DueDate'],
                    "LicenceDescription": row['LicenceCodesMapped'],
                    "LicenceProficiency": row['WS_RenTypePRB']
                }
        }
        return json.dumps(data_set)
