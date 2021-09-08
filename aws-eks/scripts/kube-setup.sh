#read in the appropriate env file
. .env

KUBEFILE=./kubectl
if test -f "$KUBEFILE"; then
    echo "$KUBEFILE already downloaded exists."
else
    echo "Downloading $FILE"
    curl -LO $KUBECTL_URL
fi
chmod +x ./kubectl
export PATH=$PWD/:$PATH

# requires either VPC peering to target account for private endpoints, or whitelist public endpoint
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION --profile $AWS_PROFILE
kubectl get nodes -o wide
kubectl get svc -o wide
kubectl get cm -n kube-system aws-auth -o yaml > .k8s-aws-auth.yaml
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master" || true

#add the load bal service account
#read in env variables
envsubst < ./k8s/aws-load-balancer-service-account.yaml > .k8s-aws-load-balancer-service-account.yaml
kubectl apply -f .k8s-aws-load-balancer-service-account.yaml

#add the cert manager
kubectl apply --validate=false -f ./k8s/cert-manager.yaml

#add the load bal controller (already modified as per AWS doco)
#https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html
#read in env variables
envsubst < ./k8s/aws-load-balancer-2_2_0_full.yaml > .k8s-aws-load-balancer-2_2_0_full.yaml
kubectl apply --validate=false -f .k8s-aws-load-balancer-2_2_0_full.yaml

#now make some conig changes to the default EKS install
#error responses are suppressed as the silly api call throws errors when the Cluster already has the config changes applied and cant apply two immediately after each other
aws eks update-cluster-config \
--region $AWS_REGION \
--name $EKS_CLUSTER_NAME \
--resources-vpc-config endpointPublicAccess=true,publicAccessCidrs="$ALLOWED_PUBLIC_IPS",endpointPrivateAccess=true \
--profile $AWS_PROFILE > /dev/null 2>&1; exit 0

# only one call at a time to update-cluster-config seems to work, so you'll need to comment out the above and uncomment the below to enable logging
# sleep 180
# aws eks update-cluster-config \
# --region $AWS_REGION \
# --name $EKS_CLUSTER_NAME \
# --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' \
# --profile $AWS_PROFILE > /dev/null 2>&1; exit 0
