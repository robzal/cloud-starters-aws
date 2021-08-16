from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class SuspensionDrugSpeed(Structure):
    product_family_name = PRODUCT_FAMILY_SUSPENSION_DRUG_SPEED
    supported_product_codes = ['PNDL4200']

    def parse(self, lines: list) -> list:

        headers = {
            Structure.profile_table_mappings['client_id']: [1, 8],
            'RecType': [9, 2],
            'InsertDate': [11, 8],
            'Filler1': [19, 8],
            'Name': [27, 27],
            'Post_Address_1': [54, 27],
            'Post_Address_2': [81, 27],
            'Salutation': [108, 49],
            'Post_Address_3': [157, 24],
            'Filler2': [181, 15],
            'OffenceDate': [196, 8],
            'Filler3': [204, 4],
            'TrafficNo': [208, 10],
            'Filler4': [218, 254],
            'DemPoints': [472, 2],
            'Filler': [474, 26],
            'Offence1': [500, 40],
            'Offence2': [540, 40],
            'Offence3': [580, 40],
            'Filler5': [620, 1641],
            'SuspensionSDate': [2261, 8],
            'SuspensionEDate': [2269, 8],
            'Filler6': [2277, 42],
            'NewEDate': [2319, 8],
            'InsertSusDate': [2327, 8],
            'InsertP1P2Date': [2335, 8],
            'CancellationDueDate': [2343, 8],
            'BCPCode': [2351, 1],
            'ProbExtPeriod': [2352, 2]
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

                # BCP Description
                if row['BCPCode'] == 'F':
                    row['BCPDescription'] = "Drug Driver Program"
                elif row['BCPCode'] == 'G':
                    row['BCPDescription'] = "Drink Driver Program"
                elif row['BCPCode'] == 'H':
                    row['BCPDescription'] = "Intensive Drink and Drug Driver Program"
                elif row['BCPCode'] == 'J':
                    row['BCPDescription'] = "Intensive Drink and Drug Driver Program (Stage 2)"

                # Demerit Points
                row['DemPoints'] = self.trim_zeroes(row['DemPoints'])
                row['ProbExtPeriod'] = self.trim_zeroes(row['ProbExtPeriod'])

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()
                row['Salutation'] = row['Salutation'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # merge offence text
                strings = [row['Offence1'], row['Offence2'], row['Offence3']]
                row['OffenceDescription'] = ' '.join(x.strip() for x in strings if x)

                # format dates
                row['InsertDate'] = self.get_formatted_date(row['InsertDate'])
                row['OffenceDate'] = self.get_formatted_date(row['OffenceDate'])
                row['SuspensionSDate'] = self.get_formatted_date(row['SuspensionSDate'])
                row['SuspensionEDate'] = self.get_formatted_date(row['SuspensionEDate'])
                row['NewEDate'] = self.get_formatted_date(row['NewEDate'])
                row['InsertSusDate'] = self.get_formatted_date(row['InsertSusDate'])
                row['InsertP1P2Date'] = self.get_formatted_date(row['InsertP1P2Date'])
                row['CancellationDueDate'] = self.get_formatted_date(row['CancellationDueDate'])

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

            # invalid rectype bcpcode combo
            if row['RecType'] == '94' and not row['BCPCode']:
                self.report_invalid_row(row,
                                        reason='Invalid RecType BCPCode combination',
                                        position_data=headers['RecType'])
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
        return 'Suspended licence'

    def history_title(self, row: dict) -> str:
        return 'Your driver licence is suspended due an offence. Please review for next steps.'

    def correspondence_metadata(self, row) -> str:
        return '-'
