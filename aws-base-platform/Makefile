include .env

.DEFAULT_GOAL := all

all: deploy
.PHONY: all

deploymentrole-pre:

	$(shell cat ./cicd/pipeline-deployrole.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: deploymentrole-pre

deploymentrole: deploymentrole-pre

	aws cloudformation deploy \
		--template-file cicd/pipeline-deployrole.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix cicd \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-deployment-role" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${AWS_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)

.PHONY: deploymentrole

pipelineprereqs-pre:

	$(shell cat ./cicd/pipeline-prereqs.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: pipelineprereqs-pre

pipelineprereqs: pipelineprereqs-pre

	aws cloudformation deploy \
	--template-file ./cicd/pipeline-prereqs.yaml \
	--stack-name platform-pipeline-prereqs \
	--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
	--region ${AWS_REGION} \
	--profile ${BUILD_PROFILE} \
	--no-fail-on-empty-changeset \
	--no-execute-changeset \
	--parameter-overrides $(shell cat .params)

.PHONY: pipelineprereqs

pipeline-pre:

	$(shell cat ./cicd/pipeline.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: pipeline-pre

pipeline: pipeline-pre

	aws cloudformation deploy \
		--template-file ./cicd/pipeline.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix cicd \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-pipeline" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${BUILD_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)


.PHONY: pipeline

pipeline-multienv-pre:

	$(shell cat ./cicd/pipeline-multienv.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: pipeline-multienv-pre

pipeline-multienv: pipeline-multienv-pre

	aws cloudformation deploy \
		--template-file ./cicd/pipeline-multienv.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix cicd \
		--stack-name "${APP_CODE}-multienv-pipeline" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${BUILD_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)


.PHONY: pipeline-multienv

pipeline-rulesengine-pre:

	$(shell cat ./cicd/pipeline-rulesengine.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: pipeline-rulesengine-pre

pipeline-rulesengine: pipeline-rulesengine-pre

	# Copy the lambdas into the S3 deployments bucket for this CFN template to reference
	# Then copy the rules file and folders into the events bucket
	# Then build and deploy the pipeline
	aws s3 cp ./cicd/${LAMBDA_FILE_COMMIT_EVENT} s3://${LAMBDA_BUCKET}/cicd/ --profile ${BUILD_PROFILE}
	aws s3 cp ./cicd/${LAMBDA_FILE_COMMIT_FETCH} s3://${LAMBDA_BUCKET}/cicd/ --profile ${BUILD_PROFILE}
	aws s3 cp ./cicd/${LAMBDA_FILE_NEXT_EXECUTION} s3://${LAMBDA_BUCKET}/cicd/ --profile ${BUILD_PROFILE}
	aws s3api put-object --bucket ${PIPELINE_EVENTS_BUCKET} --key rules/ --profile ${BUILD_PROFILE}
	aws s3api put-object --bucket ${PIPELINE_EVENTS_BUCKET} --key events/ --profile ${BUILD_PROFILE}
	aws s3api put-object --bucket ${PIPELINE_EVENTS_BUCKET} --key events/${APP_CODE}/ --profile ${BUILD_PROFILE}
	aws s3 cp ./cicd/codepipeline.rules s3://${PIPELINE_EVENTS_BUCKET}/rules/${CODE_COMMIT_REPONAME}.rules --profile ${BUILD_PROFILE}

	aws cloudformation deploy \
		--template-file ./cicd/pipeline-rulesengine.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix cicd \
		--stack-name "${APP_CODE}-rulesengine-pipeline" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${BUILD_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)


.PHONY: pipeline-rulesengine

deploy-pre:

	$(shell cat ./cfn/template.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: deploy-pre

deploy: deploy-pre
	aws cloudformation deploy \
		--template-file cfn/template.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix ${APP_CODE} \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-stack" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${AWS_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)

.PHONY: deploy

PIPELINE_LAMBDAS=$(shell find .aws-sam/build/* -type d -maxdepth 0)

buildlambdas: 
	sam build \
		--template-file ./build/pipeline-lambdas.yaml \
		--region ${AWS_REGION} \
		--profile ${BUILD_PROFILE} \
		${SAM_DEBUG_OPTION}

	for dir in $(PIPELINE_LAMBDAS) ; do \
		echo $$dir; \
		cd "$$dir" && zip -r ../../../build/pipeline-lambdas/"$$(basename $$dir)"_${LAMBDA_VERSION}.zip * && cd - ; \
	done

.PHONY: buildlambdas