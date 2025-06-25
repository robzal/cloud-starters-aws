import { StackProps } from "aws-cdk-lib";

export interface EnvProps {
    account: string;
    region: string;
    environment: string;
    vpcId: string;
}

export interface EnvStackProps extends StackProps {
    envProps: EnvProps;
}
