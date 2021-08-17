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

deploy-cluster-pre:

	$(shell cat ./cfn/ecs-cluster.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: deploy-cluster-pre

deploy-cluster: deploy-cluster-pre
	aws cloudformation deploy \
		--template-file cfn/ecs-cluster.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix ${APP_CODE} \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-ecs-cluster" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${AWS_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)

.PHONY: deploy-cluster

deploy-app-pre:

	$(shell cat ./cfn/ecs-app.params | sed 's/\r//g' | sed 's/\n//g' > .params.tmp)
	envsubst < .params.tmp > .params

.PHONY: deploy-app-pre

deploy-app: deploy-app-pre
	aws cloudformation deploy \
		--template-file cfn/ecs-app.yaml \
		--s3-bucket ${CLOUDFORMATION_BUCKET} \
		--s3-prefix ${APP_CODE} \
		--stack-name "${APP_CODE}-${ENVIRONMENT}-ecs-app" \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${AWS_REGION} \
		--profile ${AWS_PROFILE} \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides $(shell cat .params)

.PHONY: deploy-app