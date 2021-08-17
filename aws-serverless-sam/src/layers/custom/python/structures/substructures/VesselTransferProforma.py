from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class VesselTransferProforma(Structure):
    product_family_name = PRODUCT_FAMILY_VESSEL_TRANSFER_PROFORMA
    supported_product_codes = ['PVRT2155']

    def parse(self, lines: list) -> list:
        headers = {
            'Registration_No': [1, 6],
            'Name': [7, 45],
            'Post_Address_1': [52, 38],
            'Post_Address_2': [90, 20],
            'PostCode': [110, 4],
            'Filler2': [114, 1],
            'User_Id': [115, 7],
            'Date': [122, 10],
            'Filler': [132, 8],
            'Transfer_Ref': [140, 10]
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

                # convert the name to capital case
                row['Name'] = row['Name'].title()

                # name for Metadata report
                row['FullName'] = row['Name']

                # format address lines (address line 3 does not exist)
                # create empty post address 3
                row['Post_State'] = self.state_by_code(row['PostCode'])
                strings = [row['Post_Address_2'], row['Post_State'], row['PostCode']]
                row['Post_Address_2'] = ' '.join(x for x in strings if x)
                row['Post_Address_3'] = ''
                formatted_addresses = self.get_formatted_address([row['Post_Address_1'], row['Post_Address_2'], row['Post_Address_3']])
                row['Post_Address_1'] = formatted_addresses[0]
                row['Post_Address_2'] = formatted_addresses[1]

                # get current date
                row['Date'] = self.get_formatted_date(row['Date'])

                rows.append(row)
            except Exception as e:
                self.report_invalid_row(_line, reason='failed parsing line {}'.format(str(e)))

        return rows

    def validate_business_rules(self, row: dict, headers: dict):
        try:
            # invalid record if registration no is invalid
            if not row['Registration_No']:
                self.report_invalid_row(row,
                                        reason='Invalid licence number - blank field',
                                        position_data=headers['Registration_No'])
                return False
        except Exception as e:
            logger.warning('failed processing business rules', extra={'data': str(e)})
            self.report_invalid_row(row, reason='failed processing business rule {}'.format(str(e)))
            return False
        return True

    # abstract methods required
    def email_template(self) -> str:
        pass

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        pass

    def history_title(self, row: dict) -> str:
        # not applicable as this correspondence doesnt have client id
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
