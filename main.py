import logging
from flask_lambda import FlaskLambda
from flask import request, jsonify, make_response, g

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
def root(project):
  d = {
    "test": "test",
    "project": project
  }
  return success_json_response(d)

if __name__ == '__main__':
  lambda_handler.run(debug=True, port=5001, host="0.0.0.0", threaded=True)