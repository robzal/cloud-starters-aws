
include .env

.DEFAULT_GOAL := all

all: deploy dockerimages
.PHONY: all

define deployaws

	cat $(5) | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

	aws cloudformation deploy \
		--template-file $(4) \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix $(2) \
		--stack-name $(6) \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--region ${AWS_REGION} \
		--profile $(1) \
		--no-fail-on-empty-changeset \
		$(3) \
		--parameter-overrides $$(cat .params)

endef

.PHONY: pipeline-prereqs pipeline-role pipeline
pipeline-prereqs:
	@echo if the final $${CLOUDFORMATION_BUCKET} bucket doesnt exist, temporarily change it to an existing bucket before creating the proper CLOUDFORMATION_BUCKET
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-prereqs.yaml,cicd/pipeline-prereqs.params,${APP_CODE}-cicd-core)
pipeline-role:
	$(call deployaws,${AWS_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-deployrole.yaml,cicd/pipeline-deployrole.params,${APP_CODE}-${ENVIRONMENT}-deployment-role)
pipeline:
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline.yaml,cicd/pipeline.params,${APP_CODE}-${ENVIRONMENT}-pipeline)

build:
	cat ./cfn/template-sam.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp

	envsubst < .params.tmp > .params

	sam build \
		--template-file ./cfn/template-sam.yaml \
		--region ${AWS_REGION} \
		--profile ${BUILD_PROFILE} \
		${SAM_DEBUG_OPTION}

.PHONY: build

deploy: build

	sam package \
		--template-file .aws-sam/build/template.yaml \
		--output-template-file .template-out.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix ${APP_CODE} \
		--profile ${BUILD_PROFILE} \
		--region ${AWS_REGION} \
		${SAM_DEBUG_OPTION}

	sam deploy \
		--template-file .template-out.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix ${APP_CODE} \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-stack" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${AWS_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $$(cat .params) \
		${SAM_DEBUG_OPTION}

.PHONY: deploy

runbuild: build run
.PHONY: runbuild

run:
	sam local start-api \
		--port ${SAM_API_PORT} \
		--docker-volume-basedir ${PWD}/.aws-sam/build \
		--debug-port ${SAM_DEBUG_PORT} \
		--region ${AWS_REGION} \
		--parameter-overrides $$(cat .params) \
		${SAM_DEBUG_OPTION}

.PHONY: run

dockerimages:

	@echo Logging into ECR
	aws ecr get-login-password --region ap-southeast-2 --profile ${AWS_PROFILE} | docker login --username AWS --password-stdin ${DOCKER_REPOSITORY}

	@echo Building and Packaging DataLoad Docker Image
	docker image build --tag ${DOCKER_REPOSITORY}/${DOCKER_IMAGE} -f docker/DataLoad/Dockerfile .
	@echo Pushing DataLoad Image to ECR
	docker push ${DOCKER_REPOSITORY}/${DOCKER_IMAGE}

.PHONY: dockerimages
