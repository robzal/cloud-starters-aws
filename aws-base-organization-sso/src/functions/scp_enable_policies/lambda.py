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
        root_id = os.environ.get("ROOT_ID", "")
        org = boto3.client("organizations")

        # 'SERVICE_CONTROL_POLICY'|'RESOURCE_CONTROL_POLICY'|'TAG_POLICY'|'BACKUP_POLICY'|'AISERVICES_OPT_OUT_POLICY'|'CHATBOT_POLICY'|'DECLARATIVE_POLICY_EC2'|'SECURITYHUB_POLICY'
        # Just doing SCP and RCP for now
        print ('Enabling SCP')
        try:
            response = org.enable_policy_type(
                RootId=root_id,
                PolicyType='SERVICE_CONTROL_POLICY'
            )
        except org.exceptions.PolicyTypeAlreadyEnabledException:
            pass
        except Exception as e:
            raise e

        print ('Enabling RCP')
        try:
            response = org.enable_policy_type(
                RootId=root_id,
                PolicyType='RESOURCE_CONTROL_POLICY'
            )
        except org.exceptions.PolicyTypeAlreadyEnabledException:
            pass
        except Exception as e:
            raise e

        print ('Done')
        # helper.Data['UploadReference'] = upload_ref

    except Exception as error:
        print (str(error))
        raise Exception("error writing {}/{}/{} to {}/{}".format(source_bucket, source_key,source_url,dest_bucket,dest_key))

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
