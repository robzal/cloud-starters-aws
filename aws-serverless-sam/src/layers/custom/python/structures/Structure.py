from itertools import groupby
import io
import base64
from barcode import generate
import abc
import os
import boto3
from typing import Optional
from math import ceil
from random import randint
import time
import json
import operator
import Config as ConfigFile
from awslogger import logger
from structures.helpers.GlobalFunctions import GlobalFunctions
from structures.helpers.Mappings import Mappings
from handlers.Customer import CustomerDDB
from handlers.FilesProgress import FilesProgress
from handlers.MetadataLUT import MetadataLUTDDB
import handlers.CommonFunction as CommonFunction

# Australian Post Address table
DDB_ADDRESS_TABLE_NAME = 'adresses'
# DynamoDB Profile Table Name
if 'DDB_CUSTOMER_TABLE_NAME' in os.environ:
    DDB_CUSTOMER_TABLE_NAME = os.environ['DDB_CUSTOMER_TABLE_NAME']

# Invalid Row report CWL
if 'CWL_INVALID_ROW' in os.environ:
    CWL_INVALID_ROW = os.environ['CWL_INVALID_ROW']

cwl_client = boto3.client('logs')

ALL_PROFILES_ROW_THRESHOLD = 5000

class Structure(abc.ABC, GlobalFunctions, Mappings, FilesProgress):

    product_family_name = None
    supported_product_codes = None

    def __init__(self, client_ddb=None, resource_ddb=None):
        logger.info('Validation: Stucture Initialising')
        self.client_ddb = boto3.client('dynamodb')
        self.resource_ddb = boto3.client('dynamodb')
        self._row = {}
        self.product_send_settings = {}
        self.platform_send_settings = {}
        self.user_profiles = {}
        self.nextSequenceToken = None
        self.invalid_rows = 0
        logger.info('Validation: Stucture Initialising Settings')
        self.product_send_settings['setting_number'] = '-1'
        self.product_send_settings['physical_correspondence'] = 'Y'  # Y(es), N(o), P(reference in myAccount)
        self.product_send_settings['electronic_correspondence'] = 'N' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
        self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
        self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
        self.product_send_settings['create_downloadable'] = 'Y'  # Y(es), N(o)
        self.product_send_settings['history_status_unread'] = 'Y'  # Y(es), N(o)
        self.platform_send_settings = {}
        self.platform_send_settings['post_enabled'] = 'N' # Y(es), N(o)
        self.platform_send_settings['email_enabled'] = 'N' # Y(es), N(o)
        self.platform_send_settings['sms_enabled'] = 'N' # Y(es), N(o)

    @abc.abstractmethod
    def parse(self, lines: list) -> list:
        """
        Parse provides dat lines
        :param lines:
        :return: parsed lines
        """
        logger.info('Validation: Structure Parsed')
        pass

    @abc.abstractmethod
    def validate_business_rules(self, line: dict, headers: dict) -> bool:
        """
        Apply business logic to the parsed lines

        :param headers: header definition of the product
        :param line: line to apply business rule to
        :return: bool value if line passed validation or not
        """
        pass

    @abc.abstractmethod
    def email_template(self) -> str:
        """
        Get email template path

        :return: email template path
        """
        pass

    @abc.abstractmethod
    def mail_template(self) -> str:
        """
        Get mail template path

        :return: mail template path
        """
        pass

    @abc.abstractmethod
    def sms_template(self) -> str:
        """
        Get SMS email template

        :return: email template path
        """
        pass

    @abc.abstractmethod
    def html_template(self) -> str:
        """
        Get HTML template path (used on the website)
        :return: html template path
        """
        pass

    @abc.abstractmethod
    def email_subject(self, row: dict) -> str:
        """
        Get email subject text

        :return:  email subject text
        """
        pass

    @abc.abstractmethod
    def history_title(self, row: dict) -> str:
        """
        Get history title text

        :return:  history title text
        """
        return 'Document Title'

    @abc.abstractmethod
    def correspondence_metadata(self, row: dict) -> str:
        """
        Populate correspondence specific data into the history records for consumption by website, etc.

        :return:  history correspondence metadata
        """
        pass

    @staticmethod
    def get_product_family_name(filename: str) -> Optional[str]:
        """
        Determine product family based on the filename

        :param filename:
        :return: product family name
        """

        product_code = GlobalFunctions.get_product_code_from_filename(filename)
        
        for cls in Structure.__subclasses__():
            # if product_code in cls.supported_product_codes:
            if product_code.upper().split() in [x.upper().split() for x in cls.supported_product_codes]:
                return cls.product_family_name

        return None

    @staticmethod
    def is_multi(filename: str) -> Optional[bool]:
        """
        Determine if filetype requires mutli processing
        :param filename:
        :return: bool
        """

        is_multi = False
        if filename[0:6] in ["renew1", "renew2"]:  # OR HOWEVER YOU DETERMINE THIS
            is_multi = True 

        return is_multi

    @staticmethod
    def get_multis(dat_rows: list):
        try:
            parsed_rows1 = []
            parsed_rowsL6 = []
            parsed_rowsG6 = []
            dat_rows.sort(key=operator.itemgetter('FullName', 'Post_Address_1', 'Post_Address_2', 'Post_Address_3'))
            items = [[g for g in group]
                     for key, group in groupby(dat_rows, key=lambda x:(x['FullName'], x['Post_Address_1'],
                                                                       x['Post_Address_2'], x['Post_Address_3']))]
            for item in items:
                if len(item) > 6:
                    parsed_rowsG6.extend(item)
                elif 1 < len(item) <= 6:
                    parsed_rowsL6.extend(item)
                elif len(item) <= 1:
                    parsed_rows1.extend(item)
        except Exception as e:
            logger.error('Failed processing multis sort and split', extra={'data': str(e)})
        return parsed_rows1, parsed_rowsL6, parsed_rowsG6

    @property
    def templates(self) -> dict:
        """
        Get a dictionary of templates names for the particular structure

        :return: dict of templates
        """

        # NOTE - the order of these items is important - we need mail first so PDFs generate before digitial Correspondence
        return {
            ConfigFile.COMMUNICATION_TYPE_MAIL: self.mail_template(),
            ConfigFile.COMMUNICATION_TYPE_EMAIL: self.email_template(),
            ConfigFile.COMMUNICATION_TYPE_HTML: self.html_template(),
            ConfigFile.COMMUNICATION_TYPE_SMS: self.sms_template()
        }

    @property
    def row(self) -> dict:
        return self._row

    @row.setter
    def row(self, row):
        """
        Represents a single record in tge file

        :param row:
        :return:
        """
        self._row = row

    def preparse(self,  lines: list) -> list:

        # add correspondence behaviour in raw_rows, for use in parse, for those structures that use it there 
        channels = self.get_channels_available()
        for line in lines:
            if 'POST' in channels:
                line['mail_required'] = self.product_send_settings['physical_correspondence']
            else:
                line['mail_required'] = 'N'
            if 'EMAIL' in channels:
                line['email_required'] = self.product_send_settings['electronic_correspondence']
            else:
                line['email_required'] = 'N'
            if 'SMS' in channels:
                line['sms_required'] = self.product_send_settings['electronic_correspondence']
            else:
                line['sms_required'] = 'N'
            line['history_required'] = self.product_send_settings['create_history']
            line['history_unread'] = self.product_send_settings['create_downloadable']
            line['fallback_required'] = self.product_send_settings['history_status_unread']
            line['download_required'] = self.product_send_settings['history_status_unread']


        # load user preferences here, for later use in parse, postparse, and maybe merge and send correspondence
        # only if electronic channels available, load profiles / preference, otherwise dont bother
        if ('EMAIL' in channels or 'SMS' in channels) and (self.product_send_settings['electronic_correspondence'] in ['Y','P','E']):
            if len(lines) >= ALL_PROFILES_ROW_THRESHOLD:
                logger.info ('Its a large rowset. Reading in all user profiles for batch process')
                self.user_profiles = self.fetch_all_profiles()
            else:
                logger.info ('Its a small rowset. Lets read in user profiles as needed')

        return lines

    def parse_resubmit(self,  lines: list) -> list:

        # add correspondence behavior and user correspondence preferences, for later use in merge and send correspondence 
        # this would ideally be done in parse() but those are subclassed so lets not repeat this code absolutely everywhere
        channels = self.get_channels_available()
        for row in lines:
            row['Email_Required'] = 'N'
            row['Email_Rqd_Ind'] = 'N'
            row['SMS_Required'] = 'N'
            row['SMS_Rqd_Ind'] = 'N'
            if ('POST' in channels and
                (self.product_send_settings['physical_correspondence'] in ['P'])):
                    # logger.info('Send post for ClientId {}'.format(clientid))
                    row['Mail_Required'] = 'Y'
            else:
                # logger.info('Dont Send Mail for ClientId {}'.format(clientid))
                row['Mail_Required'] = 'N'
        return lines


    def postparse(self,  lines: list) -> list:

        # add correspondence behavior and user correspondence preferences, for later use in merge and send correspondence 
        # this would ideally be done in parse() but those are subclassed so lets not repeat this code absolutely everywhere
        for row in lines:
            self.user_output_channels_mapping(row)
        return lines

    def barcode(self, code_string: str, text: str, code: str) -> str:
        try:
            writer_options = {
                'module_height': 8,
                'center_text': True,
                'module_width': 0.3,
                'font_size': 6,
                'quiet_zone': 0,
                'text_distance': 3.5
            }

            # logger.info('generating barcode', extra={'data': {
            #     'code_string': code_string,
            #     'text': text,
            #     'code': code
            # }})

            fp = io.BytesIO()

            generate(code, code_string, output=fp, text=text, writer_options=writer_options)
            barcode_64 = str(base64.encodebytes(fp.getvalue()), 'utf-8').strip()

            return barcode_64
        except Exception as e:
            logger.warning('failed generate barcode', extra={'data': str(e)})
            return ''

    def load_settings(self, filename, all_channels: bool):

        if os.getenv('ENABLE_SEND_POST') == 'True':
            self.platform_send_settings['post_enabled'] = 'Y' # Y(es), N(o)

        if os.getenv('ENABLE_SEND_EMAIL') == 'True' and all_channels == True:
            self.platform_send_settings['email_enabled'] = 'Y' # Y(es), N(o)

        if os.getenv('ENABLE_SEND_SMS') == 'True' and all_channels == True:
            self.platform_send_settings['sms_enabled'] = 'Y' # Y(es), N(o)

        self.lut = MetadataLUTDDB.get(CommonFunction.get_prefix_from_filename(filename))
        setting = '0'
        if self.lut is None:
            logger.error(f'Cannot find LUT for {filename}')
            raise Exception ('Enable to read correspondence product settings')
        else:
            logger.info('Getting Correspondence Setting Code for {}'.format(filename))
            setting = self.lut.CorrespondenceSetting
            logger.info('Correspondence Setting is {}'.format(setting))
            self.product_send_settings['is_important'] = 'N'
            if self.lut.important_correspondence == '1':
                self.product_send_settings['is_important'] = 'Y'

        if setting == "1":
            # Non deemed - user preferenced channel
            self.product_send_settings['setting_number'] = '1'
            self.product_send_settings['physical_correspondence'] = 'P'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'P' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'Y' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'Y'  # Y(es), N(o)
        elif setting == "2":
            # Deemed Service - Physical + Optional Electronic
            self.product_send_settings['setting_number'] = '2'
            self.product_send_settings['physical_correspondence'] = 'Y'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'P' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'Y'  # Y(es), N(o)
        elif setting == "3":
            # contains physical - Physical + Optional Electronic
            self.product_send_settings['setting_number'] = '3'
            self.product_send_settings['physical_correspondence'] = 'Y'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'P' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'N'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'N'  # Y(es), N(o)
        elif setting == "4":
            # strictly physical - Physical + Never Electronic
            self.product_send_settings['setting_number'] = '4'
            self.product_send_settings['physical_correspondence'] = 'Y'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'N' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'N'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'N'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'N'  # Y(es), N(o)
        elif setting == "5":
            # complimentary eletronic - only electronic if preferenced
            self.product_send_settings['setting_number'] = '5'
            self.product_send_settings['physical_correspondence'] = 'N'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'P' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'N'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'N'  # Y(es), N(o)
        elif setting == "6":
            # mandatory electronic - only electronic if possible
            self.product_send_settings['setting_number'] = '6'
            self.product_send_settings['physical_correspondence'] = 'N'  # Y(es), N(o), P(reference in myAccount)
            self.product_send_settings['electronic_correspondence'] = 'E' # Y(es), N(o), P(reference in myAccount), E(lectronic if active myAccount)
            self.product_send_settings['fallback_physical'] = 'N' # Y(es), N(o)
            self.product_send_settings['create_history'] = 'Y'  # Y(es), N(o)
            self.product_send_settings['create_downloadable'] = 'N'  # Y(es), N(o)
            self.product_send_settings['history_status_unread'] = 'N'  # Y(es), N(o)
        else:
            logger.error('Correspondence setting of {} for {} not understood'.format(setting,filename))
            raise Exception ('Correspondence setting of {} for {} not understood'.format(setting,filename))

    def get_product_send_settings(self):

        return self.product_send_settings

    def get_platform_send_settings(self):

        return self.platform_send_settings

    def get_channels_available(self):

        channels = []
        if self.platform_send_settings['post_enabled'] in ['Y'] and self.product_send_settings['physical_correspondence'] in ['Y','P']:
            # logger.info('Post Channel Available')
            channels.append('POST')
        if self.platform_send_settings['email_enabled']  in ['Y'] and self.product_send_settings['electronic_correspondence'] in ['Y','P','E']:
            # logger.info('Email Channel Available')
            channels.append('EMAIL')
        if self.platform_send_settings['sms_enabled']  in ['Y'] and self.product_send_settings['electronic_correspondence'] in ['Y','P','E']:
            # logger.info('SMS Channel Available')
            channels.append('SMS')
        return channels

    def get_digital_channels_available(self):

        channels = []
        if self.platform_send_settings['email_enabled']  in ['Y'] and self.product_send_settings['electronic_correspondence'] in ['Y','P','E']:
            # logger.info('Email Digital Channel Available')
            channels.append('EMAIL')
        if self.platform_send_settings['sms_enabled']  in ['Y'] and self.product_send_settings['electronic_correspondence'] in ['Y','P','E']:
            # logger.info('SMS Digital Channel Available')
            channels.append('SMS')
        return channels

    def user_output_channels_mapping(self, row: dict) -> dict:
        """
        Evaluate the sending pattern for the given record

        """

        row['History_Required'] = self.product_send_settings['create_history']
        row['History_Unread'] = self.product_send_settings['history_status_unread']
        row['Fallback_Required'] = self.product_send_settings['fallback_physical']
        row['Download_Required'] = self.product_send_settings['create_downloadable']
        row['Physical_Available'] = 'Y'
        row['Is_Important'] = self.product_send_settings['is_important']
        if self.product_send_settings['physical_correspondence'] == 'N':
            row['Physical_Available'] = 'N'

        # if Mail, Email or SMS required fields already there, we'll assume logic comes from parse(), so we wont mess with it
        # if 1 == 1:
        if not (row.get('Mail_Required',None) or row.get('Email_Required',None) or row.get('SMS_Required',None)):
            # logger.info('GET USER PROFILE')
            channels = self.get_channels_available()
            #user settings used in overall settings determination
            clientid = None
            profile = {}
            try:
                clientid = CommonFunction.unpadded_id(row[Structure.profile_table_mappings['client_id']])
                # logger.info('Row ClientID is {}'.format(clientid))
            except:
                pass
            if clientid:
                # logger.info('Looking for User Profile for ClientId {}'.format(clientid))
                if self.user_profiles:
                    if clientid in self.user_profiles:
                        profile = self.user_profiles[clientid]
                else:
                    profile = self.fetch_single_profile(clientid)

                # if profile:
                #     logger.info('Found User Profile for ClientId {}'.format(clientid))
                
            # lets merge user (if found) and platform settings
            if ('EMAIL' in channels and profile.get('Active',False) == True and profile.get('Locked',True) == False and
                (self.product_send_settings['electronic_correspondence'] in ['Y']
                or (self.product_send_settings['electronic_correspondence'] in ['P','E'] and profile.get('CorrespondencePreference','post') == 'electronic'))):
                    # logger.info('Send email for ClientId {}'.format(clientid))
                    row['Email_Required'] = 'Y'
                    row['Email_Rqd_Ind'] = 'Y'
                    row['Email_Address'] = profile['EmailAddress']
            else:
                # logger.info('Dont Send email for ClientId {}'.format(clientid))
                row['Email_Required'] = 'N'
                row['Email_Rqd_Ind'] = 'N'
            if ('SMS' in channels and profile.get('Active',False) == True and profile.get('Locked',True) == False and
                (self.product_send_settings['electronic_correspondence'] in ['Y']
                or (self.product_send_settings['electronic_correspondence'] in ['P','E'] and profile.get('CorrespondencePreference','post') == 'electronic'))):
                    # logger.info('Send sms for ClientId {}'.format(clientid))
                    row['SMS_Required'] = 'Y'
                    row['SMS_Rqd_Ind'] = 'Y'
                    row['Phone_Number'] = profile['PhoneNumber']
            else:
                # logger.info('Dont Send sms for ClientId {}'.format(clientid))
                row['SMS_Required'] = 'N'
                row['SMS_Rqd_Ind'] = 'N'
            if ('POST' in channels and
                (self.product_send_settings['physical_correspondence'] in ['Y']
                or (self.product_send_settings['physical_correspondence'] in ['P'] and profile.get('CorrespondencePreference','post') == 'post'))
                or (self.product_send_settings['physical_correspondence'] in ['P'] and not(row['Email_Required'] == 'Y' or row['SMS_Required'] == 'Y')) ):
                    # logger.info('Send post for ClientId {}'.format(clientid))
                    row['Mail_Required'] = 'Y'
            else:
                # logger.info('Dont Send Mail for ClientId {}'.format(clientid))
                row['Mail_Required'] = 'N'

        return row

    def fetch_all_profiles(self) -> list:
        """
        Fetch all digital preferenced profiles and return as the list

        :return: rows with profile information
        """

        profiles = {}
        logger.info("fetching all profiles")

        for client in CustomerDDB.scan():
            profiles[CommonFunction.unpadded_id(client.ClientId)] = {'ClientId': CommonFunction.unpadded_id(client.ClientId), 'CorrespondencePreference': client.CorrespondencePreference, 'PhoneNumber': client.PhoneNumber, 'EmailAddress': client.EmailAddress, 'Active': client.Active, 'Locked': client.Locked}

        if not profiles:
            # add a dummy record to stop lots of recursive dynamodb calls later on
            profiles['00000000'] = {'ClientId': '00000000', 'CorrespondencePreference': 'post', 'PhoneNumber': '', 'EmailAddress': '', 'Active': 'false'}

        return profiles

    def fetch_single_profile(self, client_id: str) -> dict:
        """
        Fetch single digital preferenced profiles and return as the dict

        :return: rows with profile information
        """

        profile = {}
        # logger.info("fetching user profile for client {}".format(client_id))

        try:
            client = CustomerDDB.get(client_id)
            profile = {'ClientId': CommonFunction.unpadded_id(client.ClientId), 'CorrespondencePreference': client.CorrespondencePreference, 'PhoneNumber': client.PhoneNumber, 'EmailAddress': client.EmailAddress, 'Active': client.Active, 'Locked': client.Locked}
            # logger.info("found user profile for client {}".format(client_id))
        except:
            pass

        return profile

    def fetch_selected_profiles(self, rows: list, customer_id_field_name: str='ClientId') -> list:
        """
        Fetch profile information for each customer given in the list

        :param rows: parsed .dat files data
        :param customer_id_field_name: field name which contains customer number
        :return: rows with customer information
        """

        clients_info = {}

        def __retrieve_clients_info(rows: list) -> list:
            unique_ids = []
            unique_rows = []
            for row in rows:
                if not row[customer_id_field_name] in unique_ids:
                    unique_rows.append(row)
                    unique_ids.append(row[customer_id_field_name])
                else:
                    logger.info ('found new clientid to fetch profile for - {}'.format(row[customer_id_field_name]))

            keys = [
                {
                    Structure.profile_table_mappings['client_id']: {
                        'S': row[customer_id_field_name]
                    }
                } for row in unique_rows]

            batch_get_item_request = {
                DDB_CUSTOMER_TABLE_NAME: {
                    'Keys': keys
                }
            }

            try:
                records = {}
                response = self.client_ddb.batch_get_item(RequestItems=batch_get_item_request)

                for ddb_record in response['Responses'][DDB_CUSTOMER_TABLE_NAME]:
                    record = {}
                    client_id = ddb_record[Structure.profile_table_mappings['client_id']]['S']
                    for k, v in ddb_record.items():
                        record[k] = list(v.values())[0]

                    records[client_id] = record

                return records
            except Exception as e:
                logger.error('error while reading records from ddb', extra={'data': str(e)})
                logger.info('search keys', extra={'data': keys})
                return {}

        batch_get_size = 100
        chunks = ceil(len(rows) / batch_get_size)
        chunk_index = 0

        i = 0
        while i < chunks:
            rows_chunk = rows[chunk_index:chunk_index + batch_get_size]
            chunk_index += batch_get_size
            clients_info.update(__retrieve_clients_info(rows_chunk))
            i += 1

        for row in rows:
            email_address = ''
            phone_number = ''
            email_rgd_ind = 'N'
            sms_rgd_ind = 'N'

            try:
                response = clients_info[row[customer_id_field_name]]

                logger.info('found customer {} profile in the profiles table'.format(row[customer_id_field_name]))
                email_address = response[Structure.profile_table_mappings['email']]
                phone_number = response[Structure.profile_table_mappings['phone']]
                if response[Structure.profile_table_mappings['correspondence_preference']] == 'Digital':
                    logger.info('correspondence preference is {}'.format(response[Structure.profile_table_mappings['correspondence_preference']]))
                    email_rgd_ind = 'Y'
                    sms_rgd_ind = 'Y'
            except KeyError as e:
                pass
                # logger.warn('customer {} is not presented in the profiles table'.format(row[customer_id_field_name]))
            except Exception as e:
                logger.error('error while parsing DDB profiles response', extra={'data': str(e)})

            row[Structure.profile_table_mappings['email']] = email_address
            row[Structure.profile_table_mappings['phone']] = phone_number
            row[Structure.profile_table_mappings['send_email']] = email_rgd_ind
            row[Structure.profile_table_mappings['send_sms']] = sms_rgd_ind

        return rows

    def report_invalid_row(self, row: dict, reason: str, position_data: list = None) -> None:
        '''
        Report invalid row to a seperate CWL for further processing.
        Record number starts at 0.
        '''
        logger.info('Validation: Structure Reporting Invalid Row')
        self.invalid_rows += 1

        row['raw_row_failure_reason'] = reason
        if position_data:
            row['invalid_offset'] = int(position_data[0])
            row['invalid_length'] = int(position_data[1])
        else:
            row['invalid_offset'] = row['invalid_length'] = 0

        payload = {
            'timestamp': int(round(time.time() * 1000)),
            'message': json.dumps(row)
        }
        logger.warning(reason, extra={'data': row})

        try:
            response = cwl_client.create_log_stream(
                logGroupName=CWL_INVALID_ROW,
                logStreamName=row['raw_filename']
            )
        except Exception as e:
            pass

        try:
            if self.nextSequenceToken == None:
                response = cwl_client.describe_log_streams(
                    logGroupName=CWL_INVALID_ROW,
                    logStreamNamePrefix=row['raw_filename']
                )
                print("response", response)
                if 'uploadSequenceToken' in response['logStreams'][0]:
                    self.nextSequenceToken = response['logStreams'][0]['uploadSequenceToken']
                else:
                    self.nextSequenceToken = '0'
            
            response = cwl_client.put_log_events(
                logGroupName=CWL_INVALID_ROW,
                logStreamName=row['raw_filename'],
                logEvents=[
                    payload
                ],
                sequenceToken=self.nextSequenceToken
            )

            self.nextSequenceToken = response['nextSequenceToken']
        except Exception as e:
            logger.error('report_invalid_row failed', extra={'data': str(e)})

    def get_invalid_rows(self):
        '''
        Get the number of invalid rows
        '''
        return self.invalid_rows