#!/bin/sh

docker-compose down
sleep 5
docker-compose up --build -d
