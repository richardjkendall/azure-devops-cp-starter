import logging
from flask_lambda import FlaskLambda
from flask import request, jsonify, make_response, g

from error_handler import error_handler, BadRequestException, SystemFailureException

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

@lambda_handler.route("/<string:project>", methods=["POST"])
@error_handler
def root(project):
  if not request.json:
    raise BadRequestException("Request should be JSON")
  if "eventType" not in request.json:
    raise BadRequestException("'eventType' is missing from request")
  if request.json["eventType"] != "git.push":
    d = {
      "eventType": request.json["eventType"],
      "status": "ignored"
    }
    return success_json_response(d)
  else:
    # this is a git.push!
    # now look for repo details for clone
    if "resource" not in request.json:
      raise BadRequestException("'resource' block is missing from request")
    else:
      if "repository" not in request.json["resource"]:
        raise BadRequestException("'resource'.'repository' block is missing from request")
      else:
        # get URL
        url = request.json["resource"]["repository"]["remoteUrl"]
        # check that the branch we care about is the one with the push
        


if __name__ == '__main__':
  lambda_handler.run(debug=True, port=5001, host="0.0.0.0", threaded=True)