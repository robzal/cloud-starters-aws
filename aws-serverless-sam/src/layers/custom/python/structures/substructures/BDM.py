from structures.Structure import Structure
from structures.ProductFamily import *
from awslogger import logger


class BDM(Structure):

    product_family_name = PRODUCT_FAMILY_BDM
    supported_product_codes = ['BDM']

    def parse(self, lines: list):
        headers = {
            Structure.profile_table_mappings['client_id']: [1, 9],
            'LetterDate': [10, 10],
            'Title': [20, 22],
            'Name': [42, 22],
            'SecondName': [64, 22],
            'Surname': [86, 40],
            'Post_Address_1': [126, 30],
            'Post_Address_2': [156, 41],
            'Post_Suburb': [197, 46],
            'Post_State': [243, 30],
            'PostCode': [273, 4],
            'ActionReq': [277, 10],
            'Filler_1': [1387, 13]
        }
        vehicles = {
            'VehDetails_1': [287, 22],
            'VehDetails_2': [309, 22],
            'VehDetails_3': [331, 22],
            'VehDetails_4': [353, 22],
            'VehDetails_5': [375, 22],
            'VehDetails_6': [397, 22],
            'VehDetails_7': [419, 22],
            'VehDetails_8': [441, 22],
            'VehDetails_9': [463, 22],
            'VehDetails_10': [485, 22],
            'VehDetails_11': [507, 22],
            'VehDetails_12': [529, 22],
            'VehDetails_13': [551, 22],
            'VehDetails_14': [573, 22],
            'VehDetails_15': [595, 22],
            'VehDetails_16': [617, 22],
            'VehDetails_17': [639, 22],
            'VehDetails_18': [661, 22],
            'VehDetails_19': [683, 22],
            'VehDetails_20': [705, 22],
            'VehDetails_21': [727, 22],
            'VehDetails_22': [749, 22],
            'VehDetails_23': [771, 22],
            'VehDetails_24': [793, 22],
            'VehDetails_25': [815, 22],
            'VehDetails_26': [837, 22],
            'VehDetails_27': [859, 22],
            'VehDetails_28': [881, 22],
            'VehDetails_29': [903, 22],
            'VehDetails_30': [925, 22],
            'VehDetails_31': [947, 22],
            'VehDetails_32': [969, 22],
            'VehDetails_33': [991, 22],
            'VehDetails_34': [1013, 22],
            'VehDetails_35': [1035, 22],
            'VehDetails_36': [1057, 22],
            'VehDetails_37': [1079, 22],
            'VehDetails_38': [1101, 22],
            'VehDetails_39': [1123, 22],
            'VehDetails_40': [1145, 22],
            'VehDetails_41': [1167, 22],
            'VehDetails_42': [1189, 22],
            'VehDetails_43': [1211, 22],
            'VehDetails_44': [1233, 22],
            'VehDetails_45': [1255, 22],
            'VehDetails_46': [1277, 22],
            'VehDetails_47': [1299, 22],
            'VehDetails_48': [1321, 22],
            'VehDetails_49': [1343, 22],
            'VehDetails_50': [1365, 22]
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

                # build vehicles list
                vehicle_list = []
                for j, offset in vehicles.items():
                    vehicle_details = line[offset[0] - 1: (offset[0] - 1) + offset[1]].strip()
                    vehicle_reg_no = vehicle_details.split(' ', 1)[0]
                    vehicle_list.append(vehicle_reg_no)
                vehicle_string = '; '.join(filter(None, vehicle_list))
                row['Vehicles'] = vehicle_string

                # convert Title to title case
                row['Title'] = row['Title'].title()

                # generate derived name
                name_parts = [row['Name'], row['SecondName'], row['Surname']]
                derived_name = ' '.join(x.strip().title() for x in name_parts if x.strip())
                row['DerivedName'] = derived_name

                # name for Metadata report
                row['FullName'] = row['DerivedName']

                # format dates
                row['LetterDate'] = self.get_formatted_date(row['LetterDate'])

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

                post_address_line1 = [row['Post_Address_1'], row['Post_Address_2']]
                row['Post_Address_Line1'] = ' '.join(x for x in post_address_line1 if x)

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
        pass

    def mail_template(self) -> str:
        return '{}/mail-template.html'.format(self.product_family_name)

    def sms_template(self) -> str:
        pass

    def html_template(self) -> str:
        pass

    def email_subject(self, row) -> str:
        pass

    def history_title(self, row) -> str:
        pass

    def correspondence_metadata(self, row) -> str:
        return '-'
