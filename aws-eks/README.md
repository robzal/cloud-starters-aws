## Setup
### Workstation PreRequisites
- AWS CLI
- GMake for local build and deployment processing

### AWS Account Structure
- Build / Mgmt Account - 583812563872
- EKS Workloads - 862017364710

### Included AWS Resource templates
- CICD Pipeline (deploy once per environment in AWS build account)
- EKS Base Platform (deploy once per environment in the AWS resource account)
- EKS RNL Resources (deploy once per environment in the AWS resource account)

### Deploying Resources from Workstation using Makefile

Uses these environment vars at a minimum from the .env file
```
    export APP_CODE=EKS-Platform
    export ENVIRONMENT=ROBZ
    export AWS_REGION=ap-southeast-2
    export AWS_DEFAULT_REGION=ap-southeast-2
    export AWS_PROFILE=webprod
    export PIPELINE_BUCKET=583812563872-pipelines
    export PIPELINE_KMS_KEY_ARN=arn:aws:kms:ap-southeast-2:583812563872:key/db041cc6-935a-4b34-a539-d5c3ea6669ec
    export CLOUDFORMATION_BUCKET=583812563872-cloudformation
    export BUILD_BUCKET=583812563872-builds
    export BUILD_PROFILE=vr-mgmt
    export CODE_COMMIT_REPO=ECS-BitBucket-Sync
    export CODE_COMMIT_BRANCH=ci/ROBZ
    export DEPLOYMENT_ROLE_ARN=arn:aws:iam::862017364710:role/Purple-PlatformStack-Pipe-CloudFormationExecutionR-1K4VK6HCBAA2B
    export DEPLOYMENT_ACCOUNT=862017364710
    export CODE_BUILD_IMAGE=aws/codebuild/standard:4.0
    export CODE_BUILD_COMPUTE=BUILD_GENERAL1_MEDIUM
    export BUILD_VPC_ID=vpc-8bfcb8ec
    export BUILD_VPC_SUBNET_IDS=subnet-0c24fe54
    export BUILD_VPC_SECGROUP_ID=sg-9a64c0e2
```

#### CICD Pipeline
```bash
make pipeline
requires above environment vars
```
#### Solution Resources
```bash
make deploy
make deploy_rnl
requires above environment vars + template parameters also in the.env file
```

## Solution Development - Making Changes

#### Setting up a new environment to build and deploy to

Its a pretty simple process to add additional environments to this platform.

Heres the list of steps

- create a new repo branch off master - named ci/$ENVIRONMENT
- create a new environment file (using an existing as a start point) - ./config/.env.$ENVIRONMENT
- make necessary updates to that ./config/.env.$ENVIRONMENT file
- copy ./config/.env.$ENVIRONMENT to ./.env
- deploy the CICD pipeline for that pipeline
```bash
make pipeline
```
- commit and push these changes to ci/$ENVIRONMENT
- the previously deploy cicd pipeline will pick up the commit, and deploy and configure the EKS platform stacks in the deployment account

#### Adding or editing environment variables and cloudformation parameters

Config values are required to drive both the local workstation environment, and also to provide CICD context in the AWS environment, plus of course for the main solution cloudformation template parameters. 

The values are often different per environment, and can env be different between stack instances in the one environment (AWS Account)

We use .env files to hold this context, with sensitive values for the cloudformation templates stored in ParameterStore, and the key to the value held in the .env file.

For local environment work, copy the desired .env.xxx file into the root .env file. This is used in the MakeFile targets.

In AWS CICD CodePipelines, the pipelines make the same copy automatically, using the exact .env filename provided in the pipeline. 

To add new cloudformation parameters into the solution (or to remove them) the following is required.
- Add a new value into each .env in the solution
- Add a mapping to that value in the .params.tempkate. This is used by sam deploy and sam local
- Add a mapping to that value in the .conf.template file. This is used by codepipline cloudformation deploy

