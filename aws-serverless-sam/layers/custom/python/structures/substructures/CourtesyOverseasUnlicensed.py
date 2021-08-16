from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class CourtesyOverseasUnlicensed(Structure):
    product_family_name = PRODUCT_FAMILY_COURTESY_OVERSEAS_UNLICENSED
    supported_product_codes = ['PNDL148J']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'IssueDate': [9, 6],
            'Name': [15, 27],
            'Post_Address_1': [42, 26],
            'Post_Address_2': [68, 26],
            'Post_Address_3': [94, 24],
            'OffDate1': [118, 8],
            'TICode1': [126, 4],
            'TINo1': [130, 10],
            'OffDate2': [140, 8],
            'TICode2': [148, 4],
            'TINo2': [152, 10],
            'OffDate3': [162, 8],
            'TICode3': [170, 4],
            'TINo3': [174, 10],
            'OffDate4': [184, 8],
            'TICode4': [192, 4],
            'TINo4': [196, 10],
            'OffDate5': [206, 8],
            'TICode5': [214, 4],
            'TINo5': [218, 10],
            'OffDate6': [228, 8],
            'TICode6': [236, 4],
            'TINo6': [240, 10],
            'OffDate7': [250, 8],
            'TICode7': [258, 4],
            'TINo7': [262, 10],
            'OffDate8': [272, 8],
            'TICode8': [280, 4],
            'TINo8': [284, 10],
            'OffDate9': [294, 8],
            'TICode9': [302, 4],
            'TINo9': [306, 10],
            'OffDate10': [316, 8],
            'TICode10': [324, 4],
            'TINo10': [328, 10],
            'OffDate11': [338, 8],
            'TICode11': [346, 4],
            'TINo11': [350, 10],
            'OffDate12': [360, 8],
            'TICode12': [368, 4],
            'TINo12': [372, 10],
            'Points1': [382, 2],
            'Filler1': [384, 26],
            'Desc1Line1': [410, 40],
            'Desc1Line2': [450, 40],
            'Desc1Line3': [490, 40],
            'Points2': [530, 2],
            'Filler2': [532, 26],
            'Desc2Line1': [558, 40],
            'Desc2Line2': [598, 40],
            'Desc2Line3': [638, 40],
            'Points3': [678, 2],
            'Filler3': [680, 26],
            'Desc3Line1': [706, 40],
            'Desc3Line2': [746, 40],
            'Desc3Line3': [786, 40],
            'Points4': [826, 2],
            'Filler4': [828, 26],
            'Desc4Line1': [854, 40],
            'Desc4Line2': [894, 40],
            'Desc4Line3': [934, 40],
            'Points5': [974, 2],
            'Filler5': [976, 26],
            'Desc5Line1': [1002, 40],
            'Desc5Line2': [1042, 40],
            'Desc5Line3': [1082, 40],
            'Points6': [1122, 2],
            'Filler6': [1124, 26],
            'Desc6Line1': [1150, 40],
            'Desc6Line2': [1190, 40],
            'Desc6Line3': [1230, 40],
            'Points7': [1270, 2],
            'Filler7': [1272, 26],
            'Desc7Line1': [1298, 40],
            'Desc7Line2': [1338, 40],
            'Desc7Line3': [1378, 40],
            'Points8': [1418, 2],
            'Filler8': [1420, 26],
            'Desc8Line1': [1446, 40],
            'Desc8Line2': [1486, 40],
            'Desc8Line3': [1526, 40],
            'Points9': [1566, 2],
            'Filler9': [1568, 26],
            'Desc9Line1': [1594, 40],
            'Desc9Line2': [1634, 40],
            'Desc9Line3': [1674, 40],
            'Points10': [1714, 2],
            'Filler10': [1716, 26],
            'Desc10Line1': [1742, 40],
            'Desc10Line2': [1782, 40],
            'Desc10Line3': [1822, 40],
            'Points11': [1862, 2],
            'Filler11': [1864, 26],
            'Desc11Line1': [1890, 40],
            'Desc11Line2': [1930, 40],
            'Desc11Line3': [1970, 40],
            'Points12': [2010, 2],
            'Filler12': [2012, 26],
            'Desc12Line1': [2038, 40],
            'Desc12Line2': [2078, 40],
            'Desc12Line3': [2118, 40]
        }
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

                # Page CSS
                row['PageCss'] = 'page-letter-victoria-police'

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format dates
                row['IssueDate'] = self.get_formatted_date(row['IssueDate'])

                # Offences list
                row['Offences'] = []
                for index in range(1, 13):
                    # trim zeroes in points and format date
                    row['Points' + str(index)] = self.trim_zeroes(row['Points' + str(index)])
                    row['OffDate' + str(index)] = self.get_formatted_date(row['OffDate' + str(index)])
                    offence = {
                        'OffDate': row['OffDate' + str(index)],
                        'TICode': row['TICode' + str(index)],
                        'TINo': row['TINo' + str(index)],
                        'Points': row['Points' + str(index)],
                        'DescLine1': row['Desc' + str(index) + 'Line1'],
                        'DescLine2': row['Desc' + str(index) + 'Line2'],
                        'DescLine3': row['Desc' + str(index) + 'Line3']}
                    row['Offences'].append(offence)

                # format address lines
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]
                row['Post_Address_3'] = formatted_addresses[2]

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
        return 'Courtesy notice of your incurred demerit points'

    def history_title(self, row) -> str:
        return 'A notice for your incurred demerit points is attached for your review.'

    def correspondence_metadata(self, row) -> str:
        return '-'
