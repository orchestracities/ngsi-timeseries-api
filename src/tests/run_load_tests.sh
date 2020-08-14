#!/usr/bin/env bash

docker-compose up -d
docker-compose stop orion
docker-compose stop mongo
sleep 10

docker run -i loadimpact/k6 run --vus 10 --duration 60s - <script.js

sleep 10

docker run -i loadimpact/k6 run --vus 100 --duration 120s - <script.js

sleep 10

docker-compose down