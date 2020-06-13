# azure-devops-cp-starter
Lambda function which can pull from azure devops git repos and trigger code pipelines

This lambda function responses to 'git.push' event web hooks from Azure Devops, clones the code repository and branch where the push happened, zips it up and then uploads the zip file to s3.

From there it is expected that S3 triggers a CloudWatch Event which starts a CodePipeline.

It uses basic authentication.

## Environment Variables

The function needs the following environment variables to be set, it will fail without them

|Variable|Purpose|
|---|---|
|API_USERNAME|Username to use for basic authentication|
|PASS_PARAM|Name of SSM parameter which stores the basic authentication password, should be a SecureString|
|AD_USERNAME|Username to use when cloning git repo from Azure|
|AD_TOKEN_PARAM|Name of SSM parameter which stores the token used to authenticate with Azure when cloning, should be a SecureString|
|S3_BUCKET|Name of S3 bucket to use for uploads|
