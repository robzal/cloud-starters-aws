from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class DemeritPointsS41A(Structure):
    product_family_name = PRODUCT_FAMILY_DEMERIT_POINTS_S41A
    supported_product_codes = ['PNDL148K', 'PNDL148L']

    def parse(self, lines: list) -> list:
        def is_type_01(line):
            return line[8:10] == '01'

        def headers(line):
            headers_01 = {
                Structure.profile_table_mappings['client_id']: [1, 8],
                'Rec_Type': [9, 2],
                'Name': [11, 27],
                'Post_Address_1': [38, 26],
                'Post_Address_2': [64, 26],
                'Post_Address_3': [90, 24],
                'Issue_Date': [114, 13],
                'From_Date': [127, 13],
                'To_Date': [140, 13],
                'SuspLength': [153, 2],
                'SuspStartDate': [155, 13],
                'SuspEndDate': [168, 13],
                'P1P2': [181, 2],
                'ProbExtPeriod': [183, 2],
                'E_cond_para': [185, 1],
                'Salutation': [186, 49],
                'Susp_Status': [235, 1],
                'Filler 1': [236, 2017],
                'Form_Type': [2253, 2],
                'Demerit_Points': [2255, 2],
                'Filler': [2257, 30]
            }
            headers_02 = {
                'RecType': [9, 2],
                'Name': [11, 27],
                'Post_Address_1': [38, 26],
                'Post_Address_2': [64, 26],
                'Post_Address_3': [90, 24],
                'IssueDate2': [114, 13],
                'FromDate2': [127, 13],
                'ToDate2': [140, 13],
                'DateInfringe1': [153, 13],
                'TACode1': [166, 4],
                'InfringeNo1': [170, 10],
                'DateInfringe2': [180, 13],
                'TACode2': [193, 4],
                'InfringeNo2': [197, 10],
                'DateInfringe3': [207, 13],
                'TACode3': [220, 4],
                'InfringeNo3': [224, 10],
                'DateInfringe4': [234, 13],
                'TACode4': [247, 4],
                'InfringeNo4': [251, 10],
                'DateInfringe5': [261, 13],
                'TACode5': [274, 4],
                'InfringeNo5': [278, 10],
                'DateInfringe6': [288, 13],
                'TACode6': [301, 4],
                'InfringeNo6': [305, 10],
                'DateInfringe7': [315, 13],
                'TACode7': [328, 4],
                'InfringeNo7': [332, 10],
                'DateInfringe8': [342, 13],
                'TACode8': [355, 4],
                'InfringeNo8': [359, 10],
                'DateInfringe9': [369, 13],
                'TACode9': [382, 4],
                'InfringeNo9': [386, 10],
                'DateInfringe10': [396, 13],
                'TACode10': [409, 4],
                'InfringeNo10': [413, 10],
                'DateInfringe11': [423, 13],
                'TACode11': [436, 4],
                'InfringeNo11': [440, 10],
                'DateInfringe12': [450, 13],
                'TACode12': [463, 4],
                'InfringeNo12': [467, 10],
                'Points1': [477, 2],
                'Filler1': [479, 26],
                'Line1Desc1': [505, 40],
                'Line2Desc1': [545, 40],
                'Line3Desc1': [585, 40],
                'Points2': [625, 2],
                'Filler2': [627, 26],
                'Line1Desc2': [653, 40],
                'Line2Desc2': [693, 40],
                'Line3Desc2': [733, 40],
                'Points3': [773, 2],
                'Filler3': [775, 26],
                'Line1Desc3': [801, 40],
                'Line2Desc3': [841, 40],
                'Line3Desc3': [881, 40],
                'Points4': [921, 2],
                'Filler4': [923, 26],
                'Line1Desc4': [949, 40],
                'Line2Desc4': [989, 40],
                'Line3Desc4': [1029, 40],
                'Points5': [1069, 2],
                'Filler5': [1071, 26],
                'Line1Desc5': [1097, 40],
                'Line2Desc5': [1137, 40],
                'Line3Desc5': [1177, 40],
                'Points6': [1217, 2],
                'Filler6': [1219, 26],
                'Line1Desc6': [1245, 40],
                'Line2Desc6': [1285, 40],
                'Line3Desc6': [1325, 40],
                'Points7': [1365, 2],
                'Filler7': [1367, 26],
                'Line1Desc7': [1393, 40],
                'Line2Desc7': [1433, 40],
                'Line3Desc7': [1473, 40],
                'Points8': [1513, 2],
                'Filler8': [1515, 26],
                'Line1Desc8': [1541, 40],
                'Line2Desc8': [1581, 40],
                'Line3Desc8': [1621, 40],
                'Points9': [1661, 2],
                'Filler9': [1663, 26],
                'Line1Desc9': [1689, 40],
                'Line2Desc9': [1729, 40],
                'Line3Desc9': [1769, 40],
                'Points10': [1809, 2],
                'Filler10': [1811, 26],
                'Line1Desc10': [1837, 40],
                'Line2Desc10': [1877, 40],
                'Line3Desc10': [1917, 40],
                'Points11': [1957, 2],
                'Filler11': [1959, 26],
                'Line1Desc11': [1985, 40],
                'Line2Desc11': [2025, 40],
                'Line3Desc11': [2065, 40],
                'Points12': [2105, 2],
                'Filler12': [2107, 26],
                'Line1Desc12': [2133, 40],
                'Line2Desc12': [2173, 40],
                'Line3Desc12': [2213, 40],
                'FormType2': [2253, 2],
                'DMPoints2': [2255, 2]
            }

            return locals()['headers_{}'.format(line[8:10])]

        rows = []
        type_01_index = None

        for i, _line in enumerate(lines):
            line = _line['raw_row']
            _line['record_no'] = i
            try:
                if is_type_01(line):
                    data_dict = {
                        header: line[pad[0] - 1: (pad[0] - 1) + pad[1]].strip() for header, pad in headers(line).items()
                    }
                    row = {**data_dict, **_line}

                    if not self.validate_business_rules(row, headers(line)):
                        continue

                    # format dates
                    row['Issue_Date'] = self.get_formatted_date(row['Issue_Date'])
                    row['From_Date'] = self.get_formatted_date(row['From_Date'])
                    row['To_Date'] = self.get_formatted_date(row['To_Date'])
                    row['SuspStartDate'] = self.get_formatted_date(row['SuspStartDate'])
                    row['SuspEndDate'] = self.get_formatted_date(row['SuspEndDate'])

                    # trim zeroes
                    row['Demerit_Points'] = self.trim_zeroes(row['Demerit_Points'])
                    row['SuspLength'] = self.trim_zeroes(row['SuspLength'])
                    row['ProbExtPeriod'] = self.trim_zeroes(row['ProbExtPeriod'])

                    # convert name and salutation to capital case
                    row['Name'] = row['Name'].title()
                    row['Salutation'] = row['Salutation'].title()

                    # name for Metadata report
                    row['FullName'] = row['Name']

                    # email subject
                    row['EmailSubject'] = self.email_subject(row)

                    # format address lines
                    formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                    row['Post_Address_1'] = formatted_addresses[0]
                    row['Post_Address_2'] = formatted_addresses[1]
                    row['Post_Address_3'] = formatted_addresses[2]

                    row['PageCss'] = 'page-letter-demerit-point-suspension-notice'

                    rows.append(row)
                    type_01_index = len(rows) - 1
                    rows[type_01_index]['Offences'] = []
                else:
                    offences_dict = {
                        header: line[pad[0] - 1: (pad[0] - 1) + pad[1]].strip() for header, pad in headers(line).items()
                    }

                    # trim zeroes in points and format DateInfringe
                    for index in range(1, 13):
                        offences_dict['Points' + str(index)] = self.trim_zeroes(offences_dict['Points' + str(index)])
                        offences_dict['DateInfringe' + str(index)] = self.get_formatted_date(offences_dict['DateInfringe' + str(index)])

                    rows[type_01_index]['Offences'].append(offences_dict)

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
        return 'Suspension notice of your demerit points'

    def history_title(self, row: dict) -> str:
        return 'Your suspension notice of your demerit points is attached for your review.'

    def correspondence_metadata(self, row) -> str:
        return '-'
