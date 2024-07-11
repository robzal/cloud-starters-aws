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

echo "Deploying Stacks into Primary Region."

# Pipeline itself deployed to primary region in DevOps account only
if [[ ${AWS_ACCOUNT_ID} == ${DEVOPS_ACCOUNT} ]]; then 
    deploy_stack $1 $AWS_PROFILE ${APP_CODE}-multienv-pipeline cicd/pipeline-multienv.yaml cicd/pipeline-multienv.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    #deploy_stack $1 $AWS_PROFILE ${APP_CODE}-multibranch-pipeline cicd/pipeline-multibranch.yaml cicd/pipeline-multibranch.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
fi
# Deployment Role deployed to primary region in any chosen account
if [[ -n "$DEPLOYMENT_ROLE_ARN" ]]; then
    deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-deployment-role cicd/pipeline-deployment-role.yaml cicd/pipeline-deployment-role.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
fi