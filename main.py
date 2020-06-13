import logging, os
import boto3
import tempfile
from flask_lambda import FlaskLambda
from flask import request, jsonify, make_response, g

from error_handler import error_handler, BadRequestException, SystemFailureException, BranchMismatchException
from security import secured

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s')
lambda_handler = FlaskLambda(__name__)
logger = logging.getLogger(__name__)



def success_json_response(payload):
  """
  Turns payload into a JSON HTTP200 response
  """
  response = make_response(jsonify(payload), 200)
  response.headers["Content-type"] = "application/json"
  return response

def clone_to_s3(repo, creds, branch, s3bucket, key):
  """
  Clone git repo, zip and upload to S3
  """
  # create folder
  tempfolder = tempfile.TemporaryDirectory()
  tempfolder_name = os.path.realpath(tempfolder.name)
  logger.info("Temp dir for clone: %s" % (tempfolder_name))
  pass


@lambda_handler.route("/<string:project>", methods=["POST"])
@error_handler
@secured(username="test", password="test2")
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
          d = {
            "eventType": request.json["eventType"],
            "remoteUrl": url,
            "branch": os.environ["BRANCH"],
            "project": project,
            "status": "processed"
          }
          return success_json_response(d)

if __name__ == '__main__':
  if "BRANCH" not in os.environ:
    logger.error("Missing BRANCH environment variable")
    exit(-1)
  lambda_handler.run(debug=True, port=5001, host="0.0.0.0", threaded=True)