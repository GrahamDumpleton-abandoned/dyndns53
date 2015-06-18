#!/usr/bin/env bash

trap 'kill -TERM $PID' TERM INT

HOST=$OPENSHIFT_PYTHON_IP
PORT=$OPENSHIFT_PYTHON_PORT

waitress-serve --host=$HOST --port=$PORT dyndns53:app &

PID=$!
wait $PID
trap - TERM INT
wait $PID
STATUS=$?

exit $STATUS
