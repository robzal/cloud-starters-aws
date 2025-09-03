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

echo "Building bundles"

build_layers
build_lambdas
build_docker

echo "Uploading bundles into Primary Region $1."

# UPLOAD to PRIMARY REGION
upload_layers $1 $AWS_PROFILE ${DEPLOYMENT_BUCKET} %%functionname $S3_OBJECT_ACL
upload_lambdas $1 $AWS_PROFILE ${DEPLOYMENT_BUCKET} %%functionname $S3_OBJECT_ACL
upload_docker $1 $AWS_PROFILE ${ECR_REGISTRY} true

# SECONDARY_REGIONS
if [[ -z $SECONDARY_REGIONS ]]; then
    echo "No Secondary Regions defined."
else
    echo "Uploading bundles into Secondary Regions."
    for r in ${SECONDARY_REGIONS//,/ }
    do
        echo "Uploading bundles Stacks into $r."
        load_env $r $2
        upload_layers $r $AWS_PROFILE ${DEPLOYMENT_BUCKET} %%functionname $S3_OBJECT_ACL 
        upload_lambdas $r $AWS_PROFILE ${DEPLOYMENT_BUCKET} %%functionname $S3_OBJECT_ACL 
        upload_docker $r $AWS_PROFILE ${ECR_REGISTRY} true
    done
fi