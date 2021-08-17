from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class FinesReformApply(Structure):
    product_family_name = PRODUCT_FAMILY_FINES_REFORM_APPLY
    supported_product_codes = ['PVRI1336']

    def parse(self, lines: list) -> list:

        headers = {
            'DetailRecordType': [1, 1],
            'LetterCode': [2, 8],
            'SanctionType': [10, 13],
            'SanctionAction': [23, 4],
            Structure.profile_table_mappings['client_id']: [27, 9],
            'ClientType': [36, 1],
            'SanctionID': [37, 20],
            'Name': [57, 30],
            'NameLine2': [87, 30],
            'Post_Address_1': [117, 30],
            'Post_Address_2': [147, 30],
            'Post_Suburb': [177, 30],
            'Post_State': [207, 3],
            'PostCode': [210, 4],
            'Salutation': [214, 30],
            'Date_Apply_Or_Delete_Sanction': [244, 8],
            'LicenceCarType': [252, 6],
            'LicenceCarStatus': [258, 12],
            'LicenceCarProficiency': [270, 12],
            'LicenceEndorsementDescription': [282, 20],
            'LicenceBikeType': [302, 6],
            'LicenceBikeStatus': [308, 12],
            'LicenceBikeProficiency': [320, 12],
            'DriverPermitType': [332, 6],
            'DriverPermitStatus ': [338, 12],
            'DPBanIndicator': [350, 1],
            'DateDPBanStart': [351, 8],
            'DateDPBanEnd': [359, 8],
            'ProbationaryLicenceIndicator': [367, 1],
            'ProbationaryLicenceStartDate': [368, 8],
            'ProbationaryLicenceEndDate': [376, 8],
            'TotalDriverConditions': [384, 2],
            'DriverConditionType_1': [386, 4],
            'DriverConditionType_2': [390, 4],
            'DriverConditionType_3': [394, 4],
            'DriverConditionType_4': [398, 4],
            'DriverConditionType_5': [402, 4],
            'DriverConditionType_6': [406, 4],
            'DriverConditionType_7': [410, 4],
            'DriverConditionType_8': [414, 4],
            'DriverConditionType_9': [418, 4],
            'DriverConditionType_10': [422, 4],
            'DriverConditionType_11': [426, 4],
            'DriverConditionType_12': [430, 4],
            'DriverConditionType_13': [434, 4],
            'DriverConditionType_14': [438, 4],
            'DriverConditionType_15': [442, 4],
            'DriverConditionType_16': [446, 4],
            'DriverConditionType_17': [450, 4],
            'DriverConditionType_18': [454, 4],
            'DriverConditionType_19': [458, 4],
            'DriverConditionType_20': [462, 4],
            'DriverConditionType_21': [466, 4],
            'DriverConditionType_22': [470, 4],
            'DriverConditionType_23': [474, 4],
            'DriverConditionType_24': [478, 4],
            'DriverConditionType_25': [482, 4],
            'DriverConditionType_26': [486, 4],
            'DriverConditionType_27': [490, 4],
            'DriverConditionType_28': [494, 4],
            'DriverConditionType_29': [498, 4],
            'DriverConditionType_30': [502, 4],
            'DriverIDReturnedCard': [506, 1],
            'RegCount': [507, 2],
            'PlateNumber_1': [509, 10],
            'PlateClass_1': [519, 1],
            'SerialNumber_1': [520, 8],
            'Make_1': [528, 52],
            'Model_1': [580, 6],
            'ManufYear_1': [586, 4],
            'Status_1': [590, 20],
            'PlateNumber_2': [610, 10],
            'PlateClass_2': [620, 1],
            'SerialNumber_2': [621, 8],
            'Make_2': [629, 52],
            'Model_2': [681, 6],
            'ManufYear_2': [687, 4],
            'Status_2': [691, 20],
            'PlateNumber_3': [711, 10],
            'PlateClass_3': [721, 1],
            'SerialNumber_3': [722, 8],
            'Make_3': [730, 52],
            'Model_3': [782, 6],
            'ManufYear_3': [788, 4],
            'Status_3': [792, 20],
            'PlateNumber_4': [812, 10],
            'PlateClass_4': [822, 1],
            'SerialNumber_4': [823, 8],
            'Make_4': [831, 52],
            'Model_4': [883, 6],
            'ManufYear_4': [889, 4],
            'Status_4': [893, 20],
            'PlateNumber_5': [913, 10],
            'PlateClass_5': [923, 1],
            'SerialNumber_5': [924, 8],
            'Make_5': [932, 52],
            'Model_5': [984, 6],
            'ManufYear_5': [990, 4],
            'Status_5': [994, 20],
            'PlateNumber_6': [1014, 10],
            'PlateClass_6': [1024, 1],
            'SerialNumber_6': [1025, 8],
            'Make_6': [1033, 52],
            'Model_6': [1085, 6],
            'ManufYear_6': [1091, 4],
            'Status_6': [1095, 20],
            'PlateNumber_7': [1115, 10],
            'PlateClass_7': [1125, 1],
            'SerialNumber_7': [1126, 8],
            'Make_7': [1134, 52],
            'Model_7': [1186, 6],
            'ManufYear_7': [1192, 4],
            'Status_7': [1196, 20],
            'PlateNumber_8': [1216, 10],
            'PlateClass_8': [1226, 1],
            'SerialNumber_8': [1227, 8],
            'Make_8': [1235, 52],
            'Model_8': [1287, 6],
            'ManufYear_8': [1293, 4],
            'Status_8': [1297, 20],
            'PlateNumber_9': [1317, 10],
            'PlateClass_9': [1327, 1],
            'SerialNumber_9': [1328, 8],
            'Make_9': [1336, 52],
            'Model_9': [1388, 6],
            'ManufYear_9': [1394, 4],
            'Status_9': [1398, 20],
            'PlateNumber_10': [1418, 10],
            'PlateClass_10': [1428, 1],
            'SerialNumber_10': [1429, 8],
            'Make_10': [1437, 52],
            'Model_10': [1489, 6],
            'ManufYear_10': [1495, 4],
            'Status_10': [1499, 20],
            'PlateNumber_11': [1519, 10],
            'PlateClass_11': [1529, 1],
            'SerialNumber_11': [1530, 8],
            'Make_11': [1538, 52],
            'Model_11': [1590, 6],
            'ManufYear_11': [1596, 4],
            'Status_11': [1600, 20],
            'PlateNumber_12': [1620, 10],
            'PlateClass_12': [1630, 1],
            'SerialNumber_12': [1631, 8],
            'Make_12': [1639, 52],
            'Model_12': [1691, 6],
            'ManufYear_12': [1697, 4],
            'Status_12': [1701, 20],
            'PlateNumber_13': [1721, 10],
            'PlateClass_13': [1731, 1],
            'SerialNumber_13': [1732, 8],
            'Make_13': [1740, 52],
            'Model_13': [1792, 6],
            'ManufYear_13': [1798, 4],
            'Status_13': [1802, 20],
            'PlateNumber_14': [1822, 10],
            'PlateClass_14': [1832, 1],
            'SerialNumber_14': [1833, 8],
            'Make_14': [1841, 52],
            'Model_14': [1893, 6],
            'ManufYear_14': [1899, 4],
            'Status_14': [1903, 20],
            'PlateNumber_15': [1923, 10],
            'PlateClass_15': [1933, 1],
            'SerialNumber_15': [1934, 8],
            'Make_15': [1942, 52],
            'Model_15': [1994, 6],
            'ManufYear_15': [2000, 4],
            'Status_15': [2004, 20],
            'PlateNumber_16': [2024, 10],
            'PlateClass_16': [2034, 1],
            'SerialNumber_16': [2035, 8],
            'Make_16': [2043, 52],
            'Model_16': [2095, 6],
            'ManufYear_16': [2101, 4],
            'Status_16': [2105, 20],
            'PlateNumber_17': [2125, 10],
            'PlateClass_17': [2135, 1],
            'SerialNumber_17': [2136, 8],
            'Make_17': [2144, 52],
            'Model_17': [2196, 6],
            'ManufYear_17': [2202, 4],
            'Status_17': [2206, 20],
            'PlateNumber_18': [2226, 10],
            'PlateClass_18': [2236, 1],
            'SerialNumber_18': [2237, 8],
            'Make_18': [2245, 52],
            'Model_18': [2297, 6],
            'ManufYear_18': [2303, 4],
            'Status_18': [2307, 20],
            'PlateNumber_19': [2327, 10],
            'PlateClass_19': [2337, 1],
            'SerialNumber_19': [2338, 8],
            'Make_19': [2346, 52],
            'Model_19': [2398, 6],
            'ManufYear_19': [2404, 4],
            'Status_19': [2408, 20],
            'PlateNumber_20': [2428, 10],
            'PlateClass_20': [2438, 1],
            'SerialNumber_20': [2439, 8],
            'Make_20': [2447, 52],
            'Model_20': [2499, 6],
            'ManufYear_20': [2505, 4],
            'Status_20': [2509, 20]
        }

        _ = lines.pop(0)
        trailer_row = lines.pop()
        trailer = trailer_row['raw_row']
        number_of_rows = int(trailer[1:7])

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
                                    position_data=[2, 6])
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

                row['LetterType'] = row['LetterCode'][-3:]

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()
                row['DerivedName'] = row['Name']

                if row['NameLine2']:
                    row['NameLine2'] = row['NameLine2'].title()
                    row['DerivedName'] = '{} {}'.format(row['Name'], row['NameLine2'])

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                row['Salutation'] = row['Salutation'].title()

                # date formatting
                row['Date_Apply_Or_Delete_Sanction'] = self.get_formatted_date(row['Date_Apply_Or_Delete_Sanction'])

                # vehicle reg details dictionary
                row['VehicleRegs'] = []
                if int(row['RegCount']) > 0:
                    for j in range(1, int(row['RegCount']) + 1):
                        vehicle_reg = {'PlateNumber': row['PlateNumber_' + str(j)],
                                       'VehicleYear': "{} {}".format(row['ManufYear_' + str(j)], row['Make_' + str(j)])}
                        row['VehicleRegs'].append(vehicle_reg)

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
        pass

    def history_title(self, row: dict) -> str:
        if row['LetterType'] == '010':
            return 'A suspension has been applied to your drivers licence(s) and registration(s)'
        elif row['LetterType'] == '020':
            return 'A suspension has been removed from your drivers licence(s) and registration(s)'
        elif row['LetterType'] == '030':
            return 'A suspension has been removed from your registration(s)'
        elif row['LetterType'] == '040':
            return 'A suspension has been applied to your registration(s)'
        elif row['LetterType'] == '050':
            return 'A suspension has been applied to your drivers licence(s)'
        elif row['LetterType'] == '060':
            return 'A suspension has been removed from your drivers licence(s)'
        return 'You have a message'

    def correspondence_metadata(self, row) -> str:
        return '-'
