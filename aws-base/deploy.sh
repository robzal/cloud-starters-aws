#!/bin/bash
# $1 = ENV to load in
# $2 = CLI Profile to Assume, or use as source if $3 (optional)
# $3 = IAM Role ARN to assume using $2 as source (optional)

load_env () {
    LOCAL_FILE=./.env
    COMMON_FILE=./config/.env._common
    COMMON_REGIONAL_FILE=./config/.env._common.$2
    ENV_FILE=./config/.env.$1
    ENV_REGIONAL_FILE=./config/.env.$1.$2

    if [ -f "$LOCAL_FILE" ]; then
        echo "Local $LOCAL_FILE exists. Loading.";
        . $LOCAL_FILE
    else
        if [ -f "$COMMON_FILE" ]; then
            echo "$COMMON_FILE exists. Loading.";
            . $COMMON_FILE
        fi

        if [ -f "$COMMON_REGIONAL_FILE" ]; then
            echo "$COMMON_REGIONAL_FILE exists. Loading.";
            . $COMMON_REGIONAL_FILE
        fi

        if [ -f "$ENV_FILE" ]; then
            echo "$ENV_FILE exists. Loading.";
            . $ENV_FILE
        fi

        if [ -f "$ENV_REGIONAL_FILE" ]; then
            echo "$ENV_REGIONAL_FILE exists. Loading.";
            . $ENV_REGIONAL_FILE
        fi
    fi
}

deploy_stack () {

	cat $4 | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

	aws cloudformation deploy \
		--stack-name $1 \
		--region $2 \
		--template-file $3 \
		--s3-bucket $5 \
		--s3-prefix $6 \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--no-fail-on-empty-changeset \
		--parameter-overrides $(cat .params) \
		$7
}

set_aws_creds () {

    if [[ -z "$2" ]]; then
    echo "No AWS CLI Profile specified" 
    else
        if [[ -z "$3" ]]; then
            echo "No IAM Role Provided. Using CLI Profile specified" 
            export AWS_PROFILE=$2 
        else
            echo "$3 IAM Role specified. Using $2 CLI Profile as its source" 
            aws configure set aws_access_key_id "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .AccessKeyId)"
            aws configure set aws_secret_access_key "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .SecretAccessKey)"
            aws configure set aws_session_token "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .Token)"
            aws configure set profile.deployrole.region ap-southeast-2
            aws configure set profile.deployrole.source_profile $2
            aws configure set profile.deployrole.role_arn $3
            export AWS_PROFILE=deployrole 
        fi

    fi
}


set_aws_creds $1 $2 $3

# PRIMARY_REGION
load_env $1 $PRIMARY_REGION

deploy_stack ${APP_CODE}-admin ${PRIMARY_REGION} cfn/base-admin.yaml cfn/base-admin.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack ${APP_CODE}-audit ${PRIMARY_REGION} cfn/base-audit.yaml cfn/base-audit.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack ${APP_CODE}-iam-ops ${PRIMARY_REGION} cfn/base-IAM-ops-roles.yaml cfn/base-IAM-ops-roles.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack ${APP_CODE}-devops ${PRIMARY_REGION} cfn/base-devops.yaml cfn/base-devops.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack ${APP_CODE}-VPC ${PRIMARY_REGION} cfn/base-VPC.yaml cfn/base-VPC.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack ${APP_CODE}-r53-ssl ${PRIMARY_REGION} cfn/base-r53-ssl.yaml cfn/base-r53-ssl.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  

# SECONDARY_REGIONS
for r in ${SECONDARY_REGIONS//,/ }
do
    load_env $1 $r
    deploy_stack ${APP_CODE}-admin ${r} cfn/base-admin.yaml cfn/base-admin.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    deploy_stack ${APP_CODE}-audit ${r} cfn/base-audit.yaml cfn/base-audit.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    deploy_stack ${APP_CODE}-iam-ops ${r} cfn/base-IAM-ops-roles.yaml cfn/base-IAM-ops-roles.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    deploy_stack ${APP_CODE}-devops ${r} cfn/base-devops.yaml cfn/base-devops.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    deploy_stack ${APP_CODE}-VPC ${r} cfn/base-VPC.yaml cfn/base-VPC.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    deploy_stack ${APP_CODE}-r53-ssl ${r} cfn/base-r53-ssl.yaml cfn/base-r53-ssl.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
done
