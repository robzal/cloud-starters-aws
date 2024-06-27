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

echo "Deploying Pipeline Stack into Primary Region."

deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-pipeline cicd/pipeline.yaml cicd/pipeline.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  

