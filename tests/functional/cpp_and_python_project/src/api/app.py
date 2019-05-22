from flask import Flask, request, jsonify, abort, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging
from marshmallow import ValidationError
import os
from rq import Queue
from rq.job import Job
from werkzeug.contrib.fixers import ProxyFix

from charon import config
import charon.cloudutils
import charon.util
import charon.scanners.nessus
from charon.worker import conn

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

q = Queue(connection=conn)


def create_app():

    app = Flask(__name__)
    APIKEY = os.environ["CHARON_APIKEY"]
    CONFIG_FILE = os.environ["CHARON_CONFIG_FILE"]

    app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)
    limiter = Limiter(app, key_func=get_remote_address)

    def require_apikey(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if (
                request.headers.get("X-Api-Key")
                and request.headers.get("X-Api-Key") == APIKEY
            ):
                return func(*args, **kwargs)
            else:
                logger.debug("Invalid API key. {0}".format(request.json))
                logger.debug("Headers: {}".format(request.headers))
                logger.debug(
                    "Headers API key: {}".format(request.headers.get("X-Api-Key"))
                )
                abort(401)

        return decorated_function

    @app.route("/job", methods=["POST"])
    @limiter.limit("300 per hour")
    @require_apikey
    def index():
        logger.debug("Received request: {}".format(request.json))
        charon_request = {}
        content = request.json

        try:
            charon_request = {
                "request": {
                    "source_project_id": content.get("source_project_id"),
                    "dest_project_id": content.get("dest_project_id"),
                    "image_uuids": content.get("image_uuids"),
                }
            }
        except (TypeError, AttributeError):
            logger.warning("Request contents are incorrect")
            return Response(
                '{"Error": "Request must contain: source_project_id, dest_project_id, image_uuids"}',
                status=400,
                mimetype="application/json",
            )

        try:
            job_config = config.Config(CONFIG_FILE, charon_request)
        except ValidationError as e:
            logger.error("Error validating config. {}".format(e))
            error_string = (
                '{"Error": "There was an issue validating the config.' + str(e) + '"}'
            )
            return Response(error_string, status=400, mimetype="application/json")

        jobs = []
        for job in content.get("image_uuids"):
            test_job = q.enqueue("charon.util.run_tests", job_config, timeout=5000)
            jobs.append(test_job.get_id())
            logger.debug(
                "Dispatched job {0} for image_uuid {1}".format(test_job.get_id(), job)
            )

        return jsonify({"job_ids": jobs})

    @app.route("/job/<job_id>", methods=["GET"])
    def get_results(job_id):

        logger.debug("Received request: {}".format(request))
        job = Job(job_id, connection=conn)

        if job.is_finished:
            return jsonify({"result": str(job.result)})
        elif job.is_failed:
            return jsonify({"status": "failed", "result": job.exc_info})
        elif job._status == "started":
            return jsonify({"status": "running"})
        else:
            return jsonify({"status": "error", "result": job.exc_info})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5000)
