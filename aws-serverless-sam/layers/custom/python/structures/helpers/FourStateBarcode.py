from typing import Optional

class FourStateBarcode(object):
    def search_dpid_record(self, code: str, address_full: str, group_full: str, locality_full: str) -> Optional[str]:
        """
        Fetch DPID address record using provided full address

        :param code: postcode
        :param address_full: point full address
        :param group_full: street full address
        :param locality_full: suburb full address
        :return: DPID or DID
        """
        try:
            table = self.resource_ddb.Table(DDB_ADDRESS_TABLE_NAME)
            response = table.get_item(
                Key={
                    'POSTCODE': code,
                    'ADDRESS_FULL': address_full
                }
            )

            if 'Item' in response and response['Item']:
                return response['Item']['DELIVY_POINT_ID']

            response = table.query(
                IndexName='POSTCODE-GROUP_FULL-index',
                KeyConditionExpression=Key('GROUP_FULL').eq(group_full) & Key('POSTCODE').eq(code)
            )

            try:
                if response['Items'][0]['DELIVY_POINT_GROUP_DID']:
                    return response['Items'][0]['DELIVY_POINT_GROUP_DID']
            except Exception as e:
                pass

            response = table.query(
                IndexName='POSTCODE-LOCALITY_FULL-index',
                KeyConditionExpression=Key('LOCALITY_FULL').eq(locality_full) & Key('POSTCODE').eq(code)
            )

            try:
                if response['Items'][0]['LOCALITY_DID']:
                    return response['Items'][0]['LOCALITY_DID']
            except Exception as e:
                pass

            return None
        except Exception as e:
            return None
