#!/bin/bash
# $1 = AWS REGION to work from
# $2 = ENV to load in
# $3 = CLI Profile to Assume, or use as source if $3 (optional)
# $4 = IAM Role ARN to assume using $2 as source (optional)

. ./scripts/aws_functions.sh

load_env $1 $2
set_aws_creds $1 $3 $4

build_lambdas
upload_lambdas $1 $AWS_PROFILE ${DEPLOYMENT_BUCKET} %%functionname 
build_docker
upload_docker $1 $AWS_PROFILE ${ECR_REGISTRY} true
