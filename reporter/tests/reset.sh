#!/bin/sh

docker-compose down
sleep 2
docker-compose up --build -d
