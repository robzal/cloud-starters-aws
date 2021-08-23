#!/bin/bash
vpc="vpc-0a0b4366ab0c398e2" 
aws ec2 describe-internet-gateways --filters 'Name=attachment.vpc-id,Values='$vpc --profile wxadmin | grep InternetGatewayId 
aws ec2 describe-subnets --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep SubnetId 
aws ec2 describe-route-tables --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep RouteTableId 
aws ec2 describe-network-acls --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep NetworkAclId 
aws ec2 describe-vpc-peering-connections --filters 'Name=requester-vpc-info.vpc-id,Values='$vpc --profile wxadmin | grep VpcPeeringConnectionId 
aws ec2 describe-vpc-endpoints --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep VpcEndpointId 
aws ec2 describe-nat-gateways --filter 'Name=vpc-id,Values='$vpc --profile wxadmin | grep NatGatewayId 
aws ec2 describe-security-groups --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep GroupId 
aws ec2 describe-instances --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep InstanceId 
aws ec2 describe-vpn-connections --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep VpnConnectionId 
aws ec2 describe-vpn-gateways --filters 'Name=attachment.vpc-id,Values='$vpc --profile wxadmin | grep VpnGatewayId 
aws ec2 describe-network-interfaces --filters 'Name=vpc-id,Values='$vpc --profile wxadmin | grep NetworkInterfaceId 
