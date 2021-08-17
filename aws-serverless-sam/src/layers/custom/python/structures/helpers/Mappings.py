class Mappings(object):

    profile_table_mappings = {
        'client_id': 'ClientId',
        'email': 'EmailAddress',
        'phone': 'PhoneNumber',
        'send_email': 'Email_Rqd_Ind',
        'send_sms': 'SMS_Rqd_Ind',
        'correspondence_preference': 'CorrespondencePreference',
    }

    @staticmethod
    def primary_key_mapping(product_family: str) -> str:
        """
        Retrieve Customer No for particular product family

        :param product_family
        :return: key name that represents customer number for given product family
        """

        return Mappings.profile_table_mappings['client_id']

    @staticmethod
    def email_key_mapping(product_family: str) -> str:
        """
        Retrieve Email for particular product family

        :param product_family:
        :return: key name that represents email for given product family
        """

        return Mappings.profile_table_mappings['email']

    @staticmethod
    def sms_key_mapping(product_family: str) -> str:
        """
        Retrieve Phone number for particular product family

        :param product_family:
        :return: key name that represents phone number for given product family
        """

        return Mappings.profile_table_mappings['phone']
