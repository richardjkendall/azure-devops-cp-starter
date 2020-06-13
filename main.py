import logging, os, shutil
import boto3
import tempfile
from zipfile import ZipFile
import uuid

from flask_lambda import FlaskLambda
from flask import request, jsonify, make_response, g
from pygit2 import Repository, clone_repository, credentials, RemoteCallbacks


from error_handler import error_handler, BadRequestException, SystemFailureException, BranchMismatchException
from security import secured

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s')
lambda_handler = FlaskLambda(__name__)
logger = logging.getLogger(__name__)

ssm = boto3.client("ssm")
s3 = boto3.client("s3")

def check_environment():
  if "BRANCH" not in os.environ:
    logger.error("Missing BRANCH environment variable")
    exit(-1)
  if "API_USERNAME" not in os.environ:
    logger.error("Missing API_USERNAME environment variable")
    exit(-1)
  if "PASS_PARAM" not in os.environ:
    logger.error("Missing PASS_PARAM environment variable")
    exit(-1)
  if "AD_USERNAME" not in os.environ:
    logger.error("Missing AD_USERNAME environment variable")
    exit(-1)
  if "AD_TOKEN_PARAM" not in os.environ:
    logger.error("Missing AD_TOKEN_PARAM environment variable")
    exit(-1)
  if "S3_BUCKET" not in os.environ:
    logger.error("Missing S3_BUCKET environment variable")
    exit(-1)

check_environment()

# get the parameters
# API password
api_password_param = ssm.get_parameter(Name=os.environ["PASS_PARAM"], WithDecryption=True)
api_password = api_password_param['Parameter']['Value']

# AD token
ad_token_param = ssm.get_parameter(Name=os.environ["AD_TOKEN_PARAM"], WithDecryption=True)
ad_token = ad_token_param['Parameter']['Value']

git_creds = credentials.UserPass(
  username=os.environ["AD_USERNAME"],
  password=ad_token
)

def success_json_response(payload):
  """
  Turns payload into a JSON HTTP200 response
  """
  response = make_response(jsonify(payload), 200)
  response.headers["Content-type"] = "application/json"
  return response

def clone_repo(repo, creds, branch, s3bucket, key):
  """
  Clone git repo, zip and upload to S3
  """
  # create folder
  tempfolder = tempfile.TemporaryDirectory()
  tempfolder_name = os.path.realpath(tempfolder.name)
  logger.info("Temp dir for clone: %s" % (tempfolder_name))
  clone_repository(
    url=repo,
    path=tempfolder_name,
    checkout_branch=branch,
    callbacks=RemoteCallbacks(credentials=creds)
  )
  logger.info("Cloned")
  # zip it up
  zipfile = tempfile.NamedTemporaryFile(suffix=".zip")
  zipfile_name = os.path.realpath(zipfile.name)
  logger.info("Zipping up to: %s" % (zipfile_name))
  zf = ZipFile(zipfile_name, "w")
  for dirname, subdirs, files in os.walk(tempfolder_name):
    try:
      subdirs.remove('.git')
    except ValueError:
      pass
    zdirname = dirname[len(tempfolder_name)+1:]
    zf.write(dirname, zdirname)
    for filename in files:
      zf.write(os.path.join(dirname, filename), os.path.join(zdirname, filename))
  zf.close()
  logger.info("Zip complete")
  # upload to s3
  s3_file_id = uuid.uuid4().hex
  s3_key = "%s/%s.zip" % (key, s3_file_id)
  s3.upload_file(zipfile_name, s3bucket, s3_key)

@lambda_handler.route("/<string:project>", methods=["POST"])
@error_handler
@secured(username=os.environ["API_USERNAME"], password=api_password)
def root(project):
  if not request.json:
    logger.info("Request not JSON")
    raise BadRequestException("Request should be JSON")
  if "eventType" not in request.json:
    logger.info("Request is missing eventType")
    raise BadRequestException("'eventType' is missing from request")
  if request.json["eventType"] != "git.push":
    logger.info("Request eventType is not supported: {et}".format(et=request.json["eventType"]))
    d = {
      "eventType": request.json["eventType"],
      "project": project,
      "status": "ignored"
    }
    return success_json_response(d)
  else:
    # this is a git.push!
    # now look for repo details for clone
    if "resource" not in request.json:
      logger.info("Resource block missing from request")
      raise BadRequestException("'resource' block is missing from request")
    else:
      if "repository" not in request.json["resource"]:
        logger.info("Repository information missing from request")
        raise BadRequestException("'resource'.'repository' block is missing from request")
      else:
        # get URL
        url = request.json["resource"]["repository"]["remoteUrl"]
        # check that the branch we care about is the one with the push
        branch_match = True
        refs = request.json["resource"]["refUpdates"]
        for ref in refs:
          logger.info("Ref name: {name}".format(name=ref["name"]))
          if ref["name"] != "refs/heads/{b}".format(b=os.environ["BRANCH"]):
            branch_match = False
        if not branch_match:
          logger.info("Branch does not match")
          raise BranchMismatchException("Expecting branch '{b}'".format(b=os.environ["BRANCH"]))
        else:
          logger.info("Request okay")
          # clone the repo
          local_folder = clone_repo(
            repo = url,
            creds = git_creds,
            branch = os.environ["BRANCH"],
            s3bucket=os.environ["S3_BUCKET"],
            key=project
          )
          d = {
            "eventType": request.json["eventType"],
            "remoteUrl": url,
            "branch": os.environ["BRANCH"],
            "project": project,
            "status": "processed"
          }
          return success_json_response(d)

if __name__ == '__main__':
  lambda_handler.run(debug=True, port=5001, host="0.0.0.0", threaded=True)