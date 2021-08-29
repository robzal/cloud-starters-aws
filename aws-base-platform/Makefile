include .env

.DEFAULT_GOAL := all
SHELL := /bin/bash

ifeq ($(MAKECMDGOALS),admin)
	include ./config/.env.admin
endif

ifeq ($(MAKECMDGOALS),tools)
	include ./config/.env.tools
endif

ifeq ($(MAKECMDGOALS),shared)
	include ./config/.env.shared
endif

ifeq ($(MAKECMDGOALS),dev)
	include ./config/.env.dev
endif

ifeq ($(MAKECMDGOALS),prod)
	include ./config/.env.prod
endif


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

.PHONY: pipeline-prereqs pipeline-role pipeline
pipeline-prereqs:
	@echo if the final $${CLOUDFORMATION_BUCKET} bucket doesnt exist, temporarily change it to an existing bucket before creating the proper CLOUDFORMATION_BUCKET
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-prereqs.yaml,cicd/pipeline-prereqs.params,${APP_CODE}-cicd-core)
pipeline-role:
	$(call deployaws,${AWS_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline-deployrole.yaml,cicd/pipeline-deployrole.params,${APP_CODE}-${ENVIRONMENT}-deployment-role)
pipeline:
	$(call deployaws,${BUILD_PROFILE},cicd,${CHANGESET_OPTION},cicd/pipeline.yaml,cicd/pipeline.params,${APP_CODE}-pipeline)

.PHONY: admin build shared dev prod
admin build shared dev prod:
	@echo if the final $${CLOUDFORMATION_BUCKET} bucket doesnt exist, temporarily change it to an existing bucket before creating the proper CLOUDFORMATION_BUCKET
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-buckets.yaml,cfn/platform-buckets.params,${APP_CODE}-buckets)
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-cicd-core.yaml,cfn/platform-cicd-core.params,${APP_CODE}-cicd-core)
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-audit.yaml,cfn/platform-audit.params,${APP_CODE}-audit)
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-ops-IAM.yaml,cfn/platform-ops-IAM.params,${APP_CODE}-ops-iam)

	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-vpc.yaml,cfn/platform-vpc.params,${APP_CODE}-${ENVIRONMENT}-vpc)
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-vpc-peering.yaml,cfn/platform-vpc-peering.params,${APP_CODE}-${ENVIRONMENT}-vpc-peering)
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-r53-ssl.yaml,cfn/platform-r53-ssl.params,${APP_CODE}-${ENVIRONMENT}-dns-ssl)

.PHONY: deploy deployvpn
deploy: admin build shared dev prod

deployvpn:
	$(call deployaws,${AWS_PROFILE},${APP_CODE},${CHANGESET_OPTION},cfn/platform-VPN-endpoint.yaml,cfn/platform-VPN-endpoint.params,${APP_CODE}-vpn-endpoint)
