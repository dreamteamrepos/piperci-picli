import json
import os
import redis
from rq import Worker, Queue, Connection
import time

from charon import config
from charon.scanners import base
from charon.notifications import base
import charon.notifications.mattermost
import charon.cloudutils.openstack
import charon.functional
import charon.scanners.nessus
import charon.util

listen = ["default"]

redis_url = os.getenv("REDIS_URL", "redis://redis:6379")

conn = redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
