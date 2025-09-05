#!/bin/bash
# $1 = AWS REGION to work from
# $2 = ENV to load in
# $3 = CLI Profile to Assume, or use as source if $3 (optional)
# $4 = IAM Role ARN to assume using $2 as source (optional)

# Set the -e option to break on error
set -e 

. ./scripts/aws_functions.sh
. ./scripts/kube_functions.sh


load_env $1 $2
set_aws_creds $1 $3 $4

echo "Setting up kubectl."
kubectl_init $1 $AWS_PROFILE $EKS_CLUSTER_NAME $KUBECTL_URL

echo "Show Cluster info."
kubectl_info

echo "Patching Config Map."
kube_configmap_patch

echo "Patching Config Map VPC."
kube_manifest_apply ./k8s/aws-configmap-vpc-windows.yaml .k8s-aws-configmap-vpc-windows.yaml

echo "Setting up EBS CSI Driver."
kube_kustomization_apply "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-$EKS_CLUSTER_VERSION"

## Using auth reconcile rather than apply is best practice for K8S Roles and Role bindings.
echo "Setting Up Cluster RoleBindings."
kube_manifest_apply ./k8s/cluster-roles-rolebindings.yaml .k8s-cluster-roles-rolebindings.yaml

echo "Setting Up Load Balancer Service Account."
kube_manifest_apply ./k8s/aws-load-balancer-service-account.yaml .k8s-aws-load-balancer-service-account.yaml

echo "Setting Up Cert Manager."
# Check if you have the correct cert-manager manifest
# https://github.com/cert-manager/cert-manager/tags
# kube_manifest_apply ./k8s/cert-manager_1_13_5.yaml .k8s-cert-manager_1_13_5.yaml --validate=true
# kube_manifest_apply ./k8s/cert-manager_1_16_5.yaml .k8s-cert-manager_1_16_5.yaml --validate=true
kube_manifest_apply ./k8s/cert-manager_1_18_2.yaml .k8s-cert-manager_1_18_2.yaml --validate=true

echo "Waiting for Cert Manager to initialise."
sleep 300

echo "Adding the load bal controller (already modified as per AWS doco)"
#https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html
#https://docs.aws.amazon.com/eks/latest/userguide/lbc-manifest.html
kube_manifest_apply ./k8s/aws-load-balancer-2_13_3_full.yaml .k8s-aws-load-balancer-2_13_3_full.yaml --validate=false
kube_manifest_apply ./k8s/aws-load-balancer-2_13_3_ingclass.yaml .k8s-aws-load-balancer-2_13_3_ingclass.yaml --validate=false
