#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 12

cd ../../../

echo '=====================> localhost'
curl http://localhost:8668/v2/version

echo '=====================> 127.0.0.1'
curl http://127.0.0.1:8668/v2/version

echo '=====================> 0.0.0.0'
curl http://0.0.0.0:8668/v2/version

h=$(hostname)
echo "=====================> ${h}"
curl "http://${h}:8668/v2/version"

ip=$(hostname -I | awk '{print $1}')
echo "=====================> ${ip}"
curl "http://${ip}:8668/v2/version"


r=$?
cd -

docker-compose down -v
exit $r
