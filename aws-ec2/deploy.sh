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

deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-linux-instance cfn/ec2-linux.yaml cfn/ec2-linux.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-windows-instance cfn/ec2-windows.yaml cfn/ec2-windows.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-linux-asg cfn/ec2-linux-scaling.yaml cfn/ec2-linux-scaling.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
deploy_stack $1 $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-windows-asg cfn/ec2-windows-scaling.yaml cfn/ec2-windows-scaling.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  

# SECONDARY_REGIONS
if [[ -z $SECONDARY_REGIONS ]]; then
    echo "No Secondary Regions defined."
else
    echo "Deploying Stacks into Secondary Regions."
    for r in ${SECONDARY_REGIONS//,/ }
    do
        echo "Deploying Stacks into $r."
       load_env $r $2
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-linux-instance cfn/ec2-linux.yaml cfn/ec2-linux.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-windows-instance cfn/ec2-windows.yaml cfn/ec2-windows.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-linux-asg cfn/ec2-linux-scaling.yaml cfn/ec2-linux-scaling.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
        deploy_stack $r $AWS_PROFILE ${APP_CODE}-${ENVIRONMENT}-ec2-windows-asg cfn/ec2-windows-scaling.yaml cfn/ec2-windows-scaling.params ${CLOUDFORMATION_BUCKET} ${APP_CODE} ${CHANGESET_OPTION}  
    done
fi