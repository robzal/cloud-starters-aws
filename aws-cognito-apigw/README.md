# cloud-starters-aws

A set of projects to use to begin AWS solutions with

Steps to Demonstrate
Deploy parameterised CFN stack
AWS Console - Create Cognito User and Add to existing Cognito group
Login to Cognito Hosted UI - exported in CFN Stack 
Grab redirected URL - this contains id_token parameter which is your JWT token
Drop that <JWT token value> into https://jwt.io to validate it is valid. You should see your username and cognito issuer details
Using Postman
    Use APIGW URL (incl resource paths) - exported in CFN stack
    Add a HTTP Header with the following value
        Authorization     Bearer <JWT token value> 