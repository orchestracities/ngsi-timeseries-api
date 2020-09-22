#!/usr/bin/env bash

docker build --cache-from smartsdk/quantumleap -t smartsdk/quantumleap ../../

docker-compose up -d
docker-compose stop orion
docker-compose stop mongo
sleep 10

docker run -i --rm loadimpact/k6 run --vus 10 --duration 60s - < notify-load-test.js

sleep 10

docker run -i --rm loadimpact/k6 run --vus 100 --duration 120s - < notify-load-test.js

sleep 10

docker-compose down -v
