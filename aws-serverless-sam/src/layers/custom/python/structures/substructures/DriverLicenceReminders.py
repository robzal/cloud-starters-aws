from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta


class DriverLicenceReminders(Structure):

    product_family_name = PRODUCT_FAMILY_DRIVER_LICENCE_REMINDERS
    supported_product_codes = ['pndl2670', 'pndl4150']

    def parse(self, lines: list):
        headers = {
            'Rec_ID': [1, 2],
            'PostCode': [3, 4],
            Structure.profile_table_mappings['client_id']: [7, 9],
            'Name': [16, 27],
            'Post_Address_1': [43, 25],
            'Post_Address_2': [68, 25],
            'Post_Address_3': [93, 25],
            'LicType1': [118, 5],
            'ExpDate1': [123, 10],
            'LicType2': [133, 5],
            'ExpDate2': [138, 10],
            'IssueDate': [148, 10],
            'PhotoFlag': [158, 1],
            'AmountDue': [159, 8],
            'Filler': [167, 4],
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

                if not self.validate_business_rules(row, headers):
                    continue

                row['OnsertRequired'] = 1
                row['OnsertMergeAtStart'] = 0
                row['OnsertsToMerge'] = ["Page2Onsert.pdf"]

                # onsert required condition
                if row['PhotoFlag'] == 'Y':
                    row['OnsertsToMerge'] = ["Page2Onsert.pdf", "PhotoLocations.pdf"]
                else:
                    # generate ICRN number
                    client_no = row[Structure.profile_table_mappings['client_id']]
                    prev_exp_date = datetime.strptime(self.get_formatted_date(row['ExpDate1']), '%d %B %Y')

                    calculated_date = prev_exp_date + relativedelta(months=+6)
                    icrn_ref = client_no.zfill(9)
                    icrn_ref = '2' + icrn_ref[1:]
                    icrn_date = calculated_date.strftime('%Y/%m/%d')

                    icrn_amount = row['AmountDue'].replace('.', '')

                    row['IcrnNumber'] = self.generate_format_icrn_number(icrn_ref, icrn_date, icrn_amount)

                # licence types
                strings = [row['LicType1'], row['LicType2']]
                row['LicenceTypes'] = ', '.join(x.strip() for x in strings if x)

                # convert name and salutation to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format dates
                row['ExpDate1'] = self.get_formatted_date(row['ExpDate1'])
                row['ExpDate2'] = self.get_formatted_date(row['ExpDate2'])

                # format currency
                row['AmountDue'] = self.get_currency(row['AmountDue'])

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

            # invalid record if record type is invalid
            if row['Rec_ID'] != 'RO':
                self.report_invalid_row(row,
                                        reason='Invalid record ID',
                                        position_data=headers['Rec_ID'])
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
        return 'Your driver licence renewal is overdue'

    def history_title(self, row) -> str:
        return 'Your driver licence expired on {}. Final overdue notice.'.format(row['ExpDate1'])

    def correspondence_metadata(self, row) -> str:
        return '-'
