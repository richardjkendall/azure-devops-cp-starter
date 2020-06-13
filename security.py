from functools import wraps
import logging
import base64
from flask import request, make_response, jsonify, g

from error_handler import AccessDeniedException

logger = logging.getLogger(__name__)

def secured(username, password):
  """
  Decorator for checking for basic auth which matches what we need
  """
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      """
      check for basic auth header
      """
      logger.info("expected username: %s, expected password: %s" % (username, password))
      if "Authorization" in request.headers or "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Basic"):
          decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
          decoded_bits = decoded.split(":")
          provided_username = decoded_bits[0]
          provided_password = decoded_bits[1]
          if provided_username == username and provided_password == password:
            logger.info("Username/password match")
            return f(*args, **kwargs)
          else:
            logger.info("Username/password mismatch")
            raise AccessDeniedException("Username/password is mismatched")
        else:
          logger.info("We only support basic authentication")
          raise AccessDeniedException("Only basic authentication is supported")
      else:
        logger.info("Authorization header is missing")
        raise AccessDeniedException("Header is missing")
    return decorated_function
  return decorator
