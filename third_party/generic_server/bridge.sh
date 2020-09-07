#!/usr/bin/env bash

set -e

CLIENT_PORT=$1
SERVER_PORT=$2

DIR=$(mktemp -d)

SERVER=${DIR}/server
CLIENT=${DIR}/client

echo "SERVER: ${SERVER}"
echo "CLIENT: ${CLIENT}"

trap 'kill $(jobs -p)' EXIT
trap "rm -rf $DIR" EXIT

while true; do
  echo "SPAWNING..."
  rm -f $CLIENT
  rm -f $SERVER

  mkfifo $CLIENT
  mkfifo $SERVER

  nc -l ${CLIENT_PORT} < ${SERVER} > ${CLIENT} &
  CLIENT_PID=$1
  nc -l ${SERVER_PORT} < ${CLIENT} > ${SERVER} &
  SERVER_PID=$!

  printf "" > $CLIENT
  wait

  echo "Died, restarting"
done
