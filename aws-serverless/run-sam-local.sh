#!/bin/bash
# $1 = AWS REGION to work from
# $2 = ENV to load in
# $3 = CLI Profile to Assume, or use as source if $3 (optional)
# $4 = IAM Role ARN to assume using $2 as source (optional)

. ./scripts/aws_functions.sh
. ./scripts/aws_sam_functions.sh

load_env $1 $2
set_aws_creds $1 $3 $4

echo "Building Serverless Stack."
build_sam_stack $1 $AWS_PROFILE cfn/serverless-sam.yaml ${SAM_DEBUG_OPTION}
# package_sam_stack $1 $AWS_PROFILE  ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${SAM_DEBUG_OPTION}

echo "Running SAM API Local."
run_sam_local $1 $AWS_PROFILE  cfn/serverless-sam.yaml cfn/serverless-sam.params ${SAM_API_PORT} ${SAM_DEBUG_PORT} ${SAM_DEBUG_OPTION} 
