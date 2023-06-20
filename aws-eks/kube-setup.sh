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

echo "Show Cluster info."
kubectl_info

echo "Patching Config Map."
kube_configmap_patch

echo "Setting up EBS CSI Driver."
kube_kustomization_apply "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"

## Using auth reconcile rather than apply is best practice for K8S Roles and Role bindings.
echo "Setting Up Cluster RoleBindings."
kube_manifest_apply ./k8s/cluster-roles-rolebindings.yaml .k8s-cluster-roles-rolebindings.yaml

echo "Setting Up Load Balancer Service Account."
kube_manifest_apply ./k8s/aws-load-balancer-service-account.yaml .k8s-aws-load-balancer-service-account.yaml

echo "Setting Up Cert Manager."
kube_manifest_apply ./k8s/cert-manager.yaml .k8s-cert-manager.yaml --validate=false

echo "Adding the load bal controller (already modified as per AWS doco)"
#https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html
kube_manifest_apply ./k8s/aws-load-balancer-2_2_0_full.yaml .k8s-aws-load-balancer-2_2_0_full.yaml --validate=false
