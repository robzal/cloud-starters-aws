include .env

.DEFAULT_GOAL := all
SHELL := /bin/bash

all: deploy
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

.PHONY: pipeline-prereqs pipeline-role pipeline pipeline-multienv pipeline-rulesengine
pipeline-prereqs:
	@echo if the final $${CLOUDFORMATION_BUCKET} bucket doesnt exist, temporarily change it to an existing bucket before creating the proper CLOUDFORMATION_BUCKET
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-prereqs.yaml,cicd/pipeline-prereqs.params,${APP_CODE}-cicd-core)
pipeline-role:
	$(call deployaws,${AWS_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-deployrole.yaml,cicd/pipeline-deployrole.params,${APP_CODE}-${ENVIRONMENT}-deployment-role)
pipeline:
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline.yaml,cicd/pipeline.params,${APP_CODE}-${ENVIRONMENT}-pipeline)
pipeline-multienv:
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-multienv.yaml,cicd/pipeline-multienv.params,${APP_CODE}-pipeline)
pipeline-rulesengine:
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-rulesengine.yaml,cicd/pipeline-rulesengine.params,${APP_CODE}-rulesengine-pipeline)

.PHONY: deploy
deploy:
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/template.yaml,cfn/template.params,${APP_CODE}-${ENVIRONMENT}-stack)

PIPELINE_LAMBDAS=$(shell find .aws-sam/build/* -type d -maxdepth 0)

.PHONY: buildlambdas
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
