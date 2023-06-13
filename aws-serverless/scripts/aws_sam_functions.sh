PROJECT_ROOT=.

build_sam_stack () {

	sam build \
		--region $1 \
        --profile $2 \
		--template-file $3 \
		$4 #${SAM_DEBUG_OPTION}

}

package_sam_stack () {

	sam package \
		--region $1 \
        --profile $2 \
		--template-file .aws-sam/build/template.yaml \
		--output-template-file .template-out.yaml \
		--s3-bucket $3 \
		--s3-prefix $4 \
		$5 #${SAM_DEBUG_OPTION}

}

deploy_sam_stack () {

	cat $5 | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

	sam deploy \
		--region $1 \
        --profile $2 \
		--stack-name $3 \
		--template-file .template-out.yaml \
		--s3-bucket $6 \
		--s3-prefix $7 \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--no-fail-on-empty-changeset \
		--parameter-overrides $(cat .params) \
		$8
        #${SAM_DEBUG_OPTION}
}

run_sam_local () {

    # $1 region
    # S2 profile
    # $3 template file
    # $4 param file
    # $5 ${SAM_API_PORT} 
    # $6 ${SAM_DEBUG_PORT} 
    # $7 ${SAM_DEBUG_OPTION} 

	cat $4 | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

    echo ${PWD}

	sam local start-api \
		--region $1 \
        --profile $2 \
		--template-file $3 \
		--port $5 \
		--docker-volume-basedir ${PWD}/src \
		--debug-port $6 \
		--parameter-overrides $(cat .params) \
		$7

}