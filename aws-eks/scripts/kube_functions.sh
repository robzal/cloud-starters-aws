PROJECT_ROOT=.

kubectl_init() {

    # $1 = AWS REGION
    # $2 = AWS PROFILE
    # $3 = EKS CLUSTER NAME
    # $4 = KUBECTL DOWNLOAD URL

    KUBEFILE=./kubectl
    if test -f "$KUBEFILE"; then
        echo "$KUBEFILE already downloaded exists."
    else
        echo "Downloading kubectl file - $4"
        curl -LO $4
    fi
    chmod +x $KUBEFILE
    export PATH=$PWD/:$PATH

    echo aws eks update-kubeconfig --name $3 --region $1 --profile $2
    aws eks update-kubeconfig --name $3 --region $1 --profile $2

}

kubectl_info() {

    kubectl get nodes -o wide
    kubectl get svc -o wide

}

kube_configmap_patch () {

    # query existing auth
    kubectl get cm -n kube-system aws-auth -o yaml > .k8s-aws-auth.yaml

    # patch rolebindings - add roles to current, read in vars and apply
    # read in env variables into patch
    envsubst < k8s/aws-configmap-patch.yaml > .aws-auth.yaml
    # append current into patch
    grep -i -A 10000  'mapRoles:' .k8s-aws-auth.yaml | tail -n +2 >> .aws-auth.yaml
    cat .aws-auth.yaml

    # apply modified configmap
    kubectl apply -f .aws-auth.yaml

}

kube_manifest_apply () {

    # $1 = MANIFEST FILE
    # $2 = WORKING FILE
    # $3 = VALIDATION OPTION

    #read in env variables
    envsubst < $1 > $2

    # apply the manifest
    kubectl apply $3 -f $2

}

kube_kustomization_apply () {

    # $1 = KUSTOMIZATION DIRECTORY

    # apply the kustomization directory
    kubectl apply -k $1

}
