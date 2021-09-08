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

#deploy a sample linux app
#read in env variables
envsubst < ./k8s/app-linux-nginx.yaml > .k8s-app-linux-nginx.yaml
kubectl apply --validate=false -f .k8s-app-linux-nginx.yaml

#deploy a sample windows app
#read in env variables
envsubst < ./k8s/app-windows-iis.yaml > .k8s-app-windows-iis.yaml
kubectl apply --validate=false -f .k8s-app-windows-iis.yaml
