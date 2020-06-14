# azure-devops-cp-starter
Lambda function which can pull from azure devops git repos and trigger code pipelines

This lambda function responses to 'git.push' event web hooks from Azure Devops, clones the code repository and branch where the push happened, zips it up and then uploads the zip file to s3.

From there it is expected that S3 triggers a CloudWatch Event which starts a CodePipeline.

It uses basic authentication.

## How it works

Configure Azure Devops POST 'git.push' events to ```https://<endpoint>/<project>/<branch>```
  
Where

* endpoint = endpoint the API is deployed on
* project = the subfolder in the S3 bucket where the zip file will be created
* branch = should match the branch that you are sending events for

The resulting zip file will be uploaded to the bucket twice

1. at key ```<project>/latest.zip```
2. at key ```<project>/<commit hash>.zip```

### Test locally

You can test this locally by running running the script with the right environment variables set e.g.

```
API_USERNAME=test PASS_PARAM=/api/test/password AD_USERNAME=user AD_TOKEN_PARAM=/ad/git/token S3_BUCKEt=cp-objects python3 main.py
```

You can then expose it using ngrok and send events via the ngrok endpoint e.g.

```
ngrok http 5001
```

## Environment Variables

The function needs the following environment variables to be set, it will fail without them

|Variable|Purpose|
|---|---|
|API_USERNAME|Username to use for basic authentication|
|PASS_PARAM|Name of SSM parameter which stores the basic authentication password, should be a SecureString|
|AD_USERNAME|Username to use when cloning git repo from Azure|
|AD_TOKEN_PARAM|Name of SSM parameter which stores the token used to authenticate with Azure when cloning, should be a SecureString|
|S3_BUCKET|Name of S3 bucket to use for uploads|
