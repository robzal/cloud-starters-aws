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

deploy_stack $1 $AWS_PROFILE ${APP_CODE}-linux-image cfn/ec2-image-builder-linux.yaml cfn/ec2-image-builder-linux.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-windows-image cfn/ec2-image-builder-windows.yaml cfn/ec2-image-builder-windows.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  

# SECONDARY_REGIONS
if [[ -z $SECONDARY_REGIONS ]]; then
    echo "No Secondary Regions defined."
else
    echo "Deploying Stacks into Secondary Regions."
    for r in ${SECONDARY_REGIONS//,/ }
    do
        load_env $r $1
    done
fi