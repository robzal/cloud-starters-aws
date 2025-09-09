import logging
import boto3
import botocore
import os
from crhelper import CfnResource

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
helper = CfnResource()


@helper.create
@helper.update
def enable_scp(event,context):
    try:
        ssoadmin = boto3.client("sso-admin")

        print ('Checking SSO Instance')

        response = ssoadmin.list_instances(
        )

        if 'Instances' not in response or len(response['Instances']) == '0':
            print('No SSO instances found. Cant configure AWS SSO' )
            raise Exception ('No SSO instances found. Cant configure AWS SSO')

        print('Instances found. Selecting the first instance' )
        print (len(response['Instances']))

        InstanceArn = response['Instances'][0]['InstanceArn']
        print('InstanceArn')
        print(InstanceArn)
        helper.Data['InstanceArn'] = InstanceArn
        IdentityStoreId = response['Instances'][0]['IdentityStoreId']
        print('IdentityStoreId')
        print(IdentityStoreId)
        helper.Data['IdentityStoreId'] = IdentityStoreId

        print ('Done')

    except Exception as error:
        print (str(error))
        raise error

@helper.delete
def no_op(event,context):
    pass

def handler(event, context):
    if "StackId" in event:
        helper(event, context)
    else:
        logger.error("CFN stackid not found so dont go any further")


if __name__ == '__main__':
    SF_Record = {}
    handler(SF_Record, "")
