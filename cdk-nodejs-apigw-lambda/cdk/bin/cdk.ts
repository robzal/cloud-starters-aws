#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { EnvProps, EnvStackProps } from "../lib/env-props";
import { ApiGatewayParallelStepFunctionsStack } from "../lib/apigw-lambda";

const app = new App();

const env_code: string = app.node.tryGetContext("env");
const env_props: EnvProps = app.node.tryGetContext(env_code);
const env = {
    account: process.env.AWS_DEPLOYMENT_ACCOUNT_ID ?? env_props.account,
    region: process.env.AWS_REGION ?? env_props.region
  }

const stack_props: EnvStackProps = {
  env: env,  
  envProps: env_props
};

new ApiGatewayParallelStepFunctionsStack(
  app,
  'apigateway-parallel-stepfunctions-stack-2',
  stack_props
)
app.synth();