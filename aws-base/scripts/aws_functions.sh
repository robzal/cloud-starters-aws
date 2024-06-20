PROJECT_ROOT=.

load_env () {
    # $1 = REGION to load in
    # $2 = ENV to load in
    LOCAL_FILE=$PROJECT_ROOT/.env
    COMMON_FILE=$PROJECT_ROOT/config/.env._common
    COMMON_REGIONAL_FILE=$PROJECT_ROOT/config/.env._common.$1
    ENV_FILE=$PROJECT_ROOT/config/.env.$2
    ENV_REGIONAL_FILE=$PROJECT_ROOT/config/.env.$2.$1

    export VERSION=`git rev-parse --short=7 HEAD 2>/dev/null; true`
    if [[ -z "$VERSION" ]]; then
        export VERSION=${CODEBUILD_RESOLVED_SOURCE_VERSION: 0:7}
        if [[ -z "$VERSION" ]]; then
            export VERSION=${COMMIT_ID: 0:7}
            if [[ -z "$VERSION" ]]; then
                export VERSION=1.0.0
            fi
        fi
    fi

    if [ -f "$LOCAL_FILE" ]; then
        echo "Local $LOCAL_FILE exists. Loading.";
        . $LOCAL_FILE
    else
        if [ -f "$COMMON_FILE" ]; then
            echo "$COMMON_FILE exists. Loading.";
            . $COMMON_FILE
        fi

        if [ -f "$COMMON_REGIONAL_FILE" ]; then
            echo "$COMMON_REGIONAL_FILE exists. Loading.";
            . $COMMON_REGIONAL_FILE
        fi

        if [ -f "$ENV_FILE" ]; then
            echo "$ENV_FILE exists. Loading.";
            . $ENV_FILE
        fi

        if [ -f "$ENV_REGIONAL_FILE" ]; then
            echo "$ENV_REGIONAL_FILE exists. Loading.";
            . $ENV_REGIONAL_FILE
        fi
    fi

}

set_aws_creds () {

    # $1 = REGION to load in
    # $2 = CLI Profile to Assume, or use as source if $3 (optional)
    # $3 = IAM Role ARN to assume using $2 as source inside AWS Compute (optional)

    if [[ -z "$2" ]]; then
    echo "No AWS CLI Profile specified" 
    else
        if [[ -z "$3" ]]; then
            echo "No IAM Role Provided. Using CLI Profile specified - $2" 
            export AWS_PROFILE=$2 
            export AWS_ACCOUNT_ID=`aws sts get-caller-identity --query "Account" --output text --profile $AWS_PROFILE`
        else
            echo "$3 IAM Role specified. Using $2 CLI Profile as its source" 
            aws configure set aws_access_key_id "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .AccessKeyId)"
            aws configure set aws_secret_access_key "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .SecretAccessKey)"
            aws configure set aws_session_token "$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI | jq -r .Token)"
            aws configure set profile.deployrole.region $1
            aws configure set profile.deployrole.source_profile $2
            aws configure set profile.deployrole.role_arn $3
            export AWS_PROFILE=deployrole 
            export AWS_ACCOUNT_ID=`aws sts get-caller-identity --query "Account" --output text --profile $AWS_PROFILE`
        fi

    fi
}

build_lambdas () {

    F_DIR=$PROJECT_ROOT/src/functions
    B_DIR=$PROJECT_ROOT/build
    P_DIR=$PROJECT_ROOT/packages
    for d in $(find $F_DIR -type d -mindepth 1 -maxdepth 1 | awk -F/ '{print $NF}'); do 
        echo $d; 
        if [ ! -d $B_DIR ] 
        then
            mkdir $B_DIR;
        fi
        if [ ! -d $B_DIR/$d ] 
        then
            mkdir $B_DIR/$d;
        fi
        if [ ! -d $P_DIR ] 
        then
            mkdir $P_DIR;
        fi
        if [ ! -d $P_DIR/lambdas ] 
        then
            mkdir $P_DIR/lambdas;
        fi
        rm -rf $B_DIR/$d/*
        pip3 install -t $B_DIR/$d -r $F_DIR/$d/requirements.txt
        cp $F_DIR/$d/*.py $B_DIR/$d
        if [ -f $P_DIR/lambdas/$d-$VERSION.zip ] 
        then
            rm $P_DIR/lambdas/$d-$VERSION.zip;
        fi
        pushd $B_DIR/$d
        zip -r ../../$P_DIR/lambdas/$d-$VERSION.zip *
        popd
    done
}

build_layers () {

    F_DIR=$PROJECT_ROOT/src/layers
    B_DIR=$PROJECT_ROOT/build
    P_DIR=$PROJECT_ROOT/packages
    for d in $(find $F_DIR -type d -mindepth 1 -maxdepth 1 | awk -F/ '{print $NF}'); do 
        echo $d; 
        if [ ! -d $B_DIR ] 
        then
            mkdir $B_DIR;
        fi
        if [ ! -d $B_DIR/$d ] 
        then
            mkdir $B_DIR/$d;
        fi
        if [ ! -d $P_DIR ] 
        then
            mkdir $P_DIR;
        fi
        if [ ! -d $P_DIR/layers ] 
        then
            mkdir $P_DIR/layers;
        fi
        rm -rf $B_DIR/$d/*
        mkdir $B_DIR/$d/python
        cp $F_DIR/$d/python/*.py $B_DIR/$d/python
        if [ -f $P_DIR/layers/$d-$VERSION.zip ] 
        then
            rm $P_DIR/layers/$d-$VERSION.zip;
        fi
        pushd $B_DIR/$d
        zip -r ../../$P_DIR/layers/$d-$VERSION.zip *
        popd
    done
}

build_docker () {

    D_DIR=$PROJECT_ROOT/docker
    for d in $(find $D_DIR -type d -mindepth 1 -maxdepth 1 | awk -F/ '{print $NF}'); do 
        IMAGE_NAME=$d
        echo Building the Docker image $IMAGE_NAME...

        cat $D_DIR/$d/build.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp
        envsubst < .params.tmp > .params

        echo docker build -t $IMAGE_NAME:$VERSION -f $D_DIR/$d/Dockerfile $(cat .params) .
        docker build -t $IMAGE_NAME:$VERSION -f $D_DIR/$d/Dockerfile $(cat .params) .
    done
}

upload_lambdas () {

    # $1 = AWS REGION
    # $2 = AWS PROFILE
    # $3 = UPLOAD BUCKET
    # $4 = UPLOAD BUCKET FOLDER
    # $5 = UPLOAD FILE ACL (optional)

    P_DIR=$PROJECT_ROOT/packages/lambdas
    for ff in $(find $P_DIR -type f -maxdepth 1 -name "*.zip") ; do 
        echo $ff;
        # package file name
        f=$(echo $ff | awk -F/ '{print $NF}');
        # package function name
        f2=$(echo $f | sed s/"-$VERSION.zip"//);
        # TODO extact function name from $ff

        k=$4
        if [ "$4" == "/" ]; then
            echo "Uploading to Root Folder ";
            k="";
        elif [ "$4" == "%%functionname" ]; then
            echo "Uploading to $f2 Function Name Subfolder ";
            k=$f2/;
        else
            echo "Uploading to $4 ";
            k=$4
        fi
        echo aws s3api put-object --bucket $3 --key $k$f --body $ff --profile $2 --region $1;
        aws s3api put-object --bucket $3 --key $k$f --body $ff --profile $2 --region $1;
        if [[ ! -z "$5" ]]; then
            aws s3api put-object-acl --bucket $3 --key $k$f --acl $5 --profile $2 --region $1;
        fi
    done

}

upload_layers () {

    # $1 = AWS REGION
    # $2 = AWS PROFILE
    # $3 = UPLOAD BUCKET
    # $4 = UPLOAD BUCKET FOLDER
    # $5 = UPLOAD FILE ACL (optional)

    P_DIR=$PROJECT_ROOT/packages/layers
    for ff in $(find $P_DIR -type f -maxdepth 1 -name "*.zip") ; do 
        echo $ff;
        # package file name
        f=$(echo $ff | awk -F/ '{print $NF}');
        # package function name
        f2=$(echo $f | sed s/"-$VERSION.zip"//);
        # TODO extact function name from $ff

        k=$4
        if [ "$4" == "/" ]; then
            echo "Uploading to Root Folder ";
            k="";
        elif [ "$4" == "%%functionname" ]; then
            echo "Uploading to $f2 Function Name Subfolder ";
            k=$f2/;
        else
            echo "Uploading to $4 ";
            k=$4
        fi
        echo aws s3api put-object --bucket $3 --key $k$f --body $ff --profile $2 --region $1;
        aws s3api put-object --bucket $3 --key $k$f --body $ff --profile $2 --region $1;
        if [[ ! -z "$5" ]]; then
            aws s3api put-object-acl --bucket $3 --key $k$f --acl $5 --profile $2 --region $1;
        fi
    done

}

upload_docker () {

    # $1 = AWS REGION
    # $2 = AWS PROFILE
    # $3 = ECR_ENDPOINT
    # $4 = UPLOAD LATEST TAG (true/false)

    # This function relies on similar build logic in build_docker function

    D_DIR=$PROJECT_ROOT/docker

    echo Logging in to Amazon ECR...
    docker login -u AWS -p $(aws ecr get-login-password --region $1 --profile $2) $3

    for d in $(find $D_DIR -type d -mindepth 1 -maxdepth 1 | awk -F/ '{print $NF}'); do 
        IMAGE_NAME=$d
        ECR_REGISTRY=$3
        echo Building the Docker image $IMAGE_NAME...

        echo docker tag $IMAGE_NAME:$VERSION $ECR_REGISTRY/$IMAGE_NAME:$VERSION
        docker tag $IMAGE_NAME:$VERSION $ECR_REGISTRY/$IMAGE_NAME:$VERSION
        if [[ "$4" == "true" ]]; then
            echo docker tag $IMAGE_NAME:$VERSION $ECR_REGISTRY/$IMAGE_NAME:latest
            docker tag $IMAGE_NAME:$VERSION $ECR_REGISTRY/$IMAGE_NAME:latest
        fi

        echo Make sure the ECR Repo is there...
        set +e        
        output=$(aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region $1 --profile $2  2>&1)
        if [ $? -ne 0 ]; then
            if echo ${output} | grep -q RepositoryNotFoundException; then
                echo -e "$IMAGE_NAME Repo doesn't exist"
                echo -e "Creating $IMAGE_NAME via Cloudformation Stack now"
                set -e
                aws cloudformation deploy \
                    --template-file ./cicd/ecr-repo.yaml \
                    --stack-name ecr-repo-$IMAGE_NAME \
                    --parameter-overrides RepoName=$IMAGE_NAME DeploymentAccountIds=$DEPLOYMENT_ACCOUNTS \
                    --region $1 \
                    --profile $2
            else
                >&2 echo ${output}
                exit
            fi
        else
            echo -e "$IMAGE_NAME Repo exists"
        fi
        set -e
        echo Pushing the Docker image...
        echo docker push $ECR_REGISTRY/$IMAGE_NAME:$VERSION
        docker push $ECR_REGISTRY/$IMAGE_NAME:$VERSION
        if [[ "$4" == "true" ]]; then
            echo docker push $ECR_REGISTRY/$IMAGE_NAME:latest
            docker push $ECR_REGISTRY/$IMAGE_NAME:latest
        fi
    done
}

deploy_stack () {

	cat $5 | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

    export OLDIFS=$IFS
    export IFS=$'\n'
	aws cloudformation deploy \
		--region $1 \
        --profile $2 \
		--stack-name $3 \
		--template-file $4 \
		--s3-bucket $6 \
		--s3-prefix $7 \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--no-fail-on-empty-changeset \
		--parameter-overrides $(cat .params) \
		$8
    export IFS=$OLDIFS
}
