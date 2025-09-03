#!/bin/bash
# $1 = AWS REGION to work from
# $2 = ENV to load in
# $3 = CLI Profile to Assume, or use as source if $3 (optional)
# $4 = IAM Role ARN to assume using $2 as source (optional)

# Set the -e option to break on error
set -e 

. ./scripts/aws_functions.sh


load_env $1 $2
set_aws_creds $1 $3 $4

echo "Deploying Stacks into Primary Region $1."

create_init_bucket $1 $AWS_PROFILE ${INIT_CLOUDFORMATION_BUCKET} ${AWS_ACCOUNT}
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-admin cfn/base-admin.yaml cfn/base-admin.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-audit cfn/base-audit.yaml cfn/base-audit.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-iam-ops cfn/base-IAM-ops-roles.yaml cfn/base-IAM-ops-roles.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-devops cfn/base-devops.yaml cfn/base-devops.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-VPC cfn/base-VPC.yaml cfn/base-VPC.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-r53-ssl cfn/base-r53-ssl.yaml cfn/base-r53-ssl.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  

# SECONDARY_REGIONS
if [[ -z $SECONDARY_REGIONS ]]; then
    echo "No Secondary Regions defined."
else
    echo "Deploying Stacks into Secondary Regions."
    for r in ${SECONDARY_REGIONS//,/ }
    do
        echo "Deploying Stacks into $r."
        load_env $r $2
        create_init_bucket $r $AWS_PROFILE ${INIT_CLOUDFORMATION_BUCKET} ${AWS_ACCOUNT}
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-admin cfn/base-admin.yaml cfn/base-admin.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-audit cfn/base-audit.yaml cfn/base-audit.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-iam-ops cfn/base-IAM-ops-roles.yaml cfn/base-IAM-ops-roles.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-devops cfn/base-devops.yaml cfn/base-devops.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-VPC cfn/base-VPC.yaml cfn/base-VPC.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-r53-ssl cfn/base-r53-ssl.yaml cfn/base-r53-ssl.params ${INIT_CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    done
fi