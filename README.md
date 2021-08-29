# cloud-starters-aws

### Note about $$$
There are charges incurred by deploying and running some of these solutions. Beware of this. My advice is to immediately delete these deployed resources (solution and pipelines if created) to prevent inadvertant charges to keep accumulating. Generally I have featured toggled the cost incurring resources (NATGWs, cluster instances, audit services) but some are not such so always keep an eye on your accrued expenses

### About
This open source repo contains a set of AWS DevOps and Infra As Code solutions with which to begin your AWS journey and projects.

Its an ongoing passion project of mine, an attempt to contribute some ideas and learnings back to my colleagues in the AWS cloud computing.

You can hopefully take any one of these projects, and use them to kick start your own solution development and deployment, building upon what is provided and using & extending the patterns that I have started. But if they dont suit you or your organisation, thats cool too. I'd love to see how you do yours!

### Objectives
My objectives in creating these projects are to:

- Provide a basic example of a landing zone for a multiaccount AWS environment (core resources and controls)
- Provide examples of most common types of infrastructure and solutions, how to define them as code, and put an automated, repo driven deployment mechanism around it
- Provide examples of a few different pipeline patterns, deploying to single or multiple AWS environments

### What you need to provide:

- One or more AWS accounts with sufficient rights to deploy and run these samples
- A local Bash terminal (Mac, Linux or WSL2 in Windows)
- AWS CLI V2 installed and configured for those AWS accounts
- SAM CLI installed locally (for solutions using SAM)
- Docker installed (for solutions using Docker)
- GNU Make installed
- Git Client installed
- Visual Studio Code, Sublime Text or other Text Editor with Git integrated

### To Consider
What I think is important for anyone building and deploying infrastructure and apps into the cloud (AWS or other) to consider is:

-  keep code and config SEPARATE. Your code should be able to be run and deployed to different AWS accounts, networks and organisations by only changing the config files / config store values.
-  try via the console, but try harder via code, committed somewhere
-  manually deployed CLI, cloudformation or terraform is ALWAYS better than no CLI, cloudformation or terraform
-  make deployment pipelines a wrapper around the same code that you can run and test in your local terminal
-  git branching - well thats a whole different religious discussion for a different time
-  remember compute time and size is money in the cloud. Always try and not have oversized, idle, self managed resources running for long periods. Rather take the serverless option if its available unless you REALLY know what you're doing. The ''Í've got the server, it might as well run'' philosphy will send you broke!
-  Minimise IAM user accounts, or preferably use SSO with an external provider. Always assume roles to do your work, including across accounts, especially to run your apps and your pipelines. Credentials hurt when they leak, role names dont.
-  NEVER put sensitive data or credentials into your source code commits


### How to get begin

-  Nominate which AWS account will be your Admin Account (used by base-platform project for security roles), your Build Account (used by all projects), and optionally Shared, Dev and Prod accounts to model a multi account topology. Its fine to use the same AWS account for multiple or all of these functions if you only have one or two AWS accounts. These account IDs are used in quite a few settings defined in the sample .env files such as bucket names, arns, etc. Fill in values as needed 
-  Setup up IAM roles in the AWS Account(s) that will be used by local CLI (via Make commands) to deploy the Pipeline resources and Workload resources in your AWS account(s).
-  Configure and test AWS CLI Profiles to use these roles (requiring AWS CLI credentials to also be configured unless using SSO). Refer https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html
-  Open a bash terminal in the root of the project you wish to use.

-  Developing and Deploying Locally via Makefile

    - Each project contains a makefile. Make commands make extensive use of environment variables, and all projects use an .env file specifically in the project's root folder (excluded from checkins) to read in these settings, so copy & rename one of the sample config files (in the /config folder) and edit it as needed. The base-platform project will also use the additional 
    - Generally each project will support various make targets depending on what they deploy, and these rely on multiple environment variables (read in from .env file). The base-platform project calls in additional .env files depending on the target, as this project is patterned to deploy to multiple environments, even when run locally. Every project will have a core 'deploy' target

    - make deploy

    - Make targets that contain aws cloudformation CLI calls (almsot all of them) pass in the $CHANGESET_OPTION variable which by default is set to CHANGESET_OPTION=--no-execute-changeset, which deploys the cloudformation changeset, but doesnt execute it. This give users the ability to check what is being created / updated before actually deploying it. This can be changed by updating value to CHANGESET_OPTION= which will immediately execute the changeset after creating it. If choosing the latter, The make execution output will display the progress for the cloudformatio stack creation. If choosing the --no-execute-changeset option, you will need to go into the cloudformation console and manually execute the changeset for that stack.

-  Deploying Workloads via CICD Pipelines (using AWS CodePipeline)

    - this is a very high level overview of how to setup CICD pipelines for you solution. There are many options and flavours and the intention here is just to provide you a starting point with code and config examples to get you started. It is recommended that you think through branching strategy, workflow and required environments, and feed those into your automation design, but for now..... 

    - once the initial development and shakeout of the solution (make deploy) has been completed, best practice for ongoing build and deployment involves automatically building (CI) and deploying (CD) further any changes made to your code, to the appropriate environments. Branching strategies and environment management are outside the scope of this README but there are many options.
    - the aws-copepipeline project in this repo shows a number of codepipeline solution options (and many more still possible)
        - pipeline per environment (statically bound to a repo branch)
        - pipeline per multiple sequenced environments (statucally bound to a repo branch)
        - pipeline per deployment target with dynamic branching rules
    - in all cases the first step is to create an AWS Code Commit repository in your nominated AWS Build account (CodeCommit is just an AWS hosted git repo). This is a manual console exercise.
    - then we need to clone that repo somewhere to our local machine (outside of the cloud-starts-aws structure)
    - copy your working code that have used as a starter, and updated & configured for your needs into the new cloned folder
    - commit and push into the new CodeCommit repo
    - update the root folder .env and config folder env.xxx to refer to your new CodeCommit repo, including these settings
        - export CODE_COMMIT_REPONAME=pipeline-test
        - export CODE_COMMIT_BRANCH=master
        - export DEPLOYMENT_ROLE_ARN=arn:aws:iam::238160719262:role/DeploymentRole
    - time to deploy the CodePipeline, to use with this new git repo, to run when future commits are made:
        - (if needed) make pipeline-prereqs
        - make pipeline-role
        - make pipeline
    - once the pipelines are deployed, they will run when the wired up branches are commit to in the CodeCommit repository
    - the generic pipelines provided generally have these stages defined by these declaratuve build instructions
        predeploy - (./buildspec-predeploy.yaml)
        postdeploy - (./buildspec-deploy.yaml)
    - HAPPY CICD'ing
