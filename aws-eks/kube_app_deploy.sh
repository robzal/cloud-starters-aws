#!/bin/bash
# $1 = AWS REGION to work from
# $2 = ENV to load in
# $3 = CLI Profile to Assume, or use as source if $3 (optional)
# $4 = IAM Role ARN to assume using $2 as source (optional)

. ./scripts/aws_functions.sh
. ./scripts/kube_functions.sh


load_env $1 $2
set_aws_creds $1 $3 $4

echo "Setting up kubectl."
kubectl_init $1 $AWS_PROFILE $EKS_CLUSTER_NAME $KUBECTL_URL

echo "Deploying sample linux app."
kube_manifest_apply ./k8s/app-linux-nginx.yaml .k8s-app-linux-nginx.yaml --validate=false

echo "Deploying sample windows app."
kube_manifest_apply ./k8s/app-windows-iis.yaml .k8s-app-windows-iis.yaml --validate=false
