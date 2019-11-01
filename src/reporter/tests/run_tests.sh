#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 12

cd ../../../

echo '=====================> I/F'
ip a

echo '=====================> docker ps'
docker ps

echo '=====================> localhost'
ping -c 1 localhost
curl http://localhost:8668/v2/version

echo '=====================> 127.0.0.1'
ping -c 1 127.0.0.1
curl http://127.0.0.1:8668/v2/version

echo '=====================> 0.0.0.0'
ping -c 1 0.0.0.0
curl http://0.0.0.0:8668/v2/version

h=$(hostname)
echo "=====================> ${h}"
ping -c 1 ${h}
curl "http://${h}:8668/v2/version"

ip=$(hostname -I | awk '{print $1}')
echo "=====================> ${ip}"
ping -c 1 ${ip}
curl "http://${ip}:8668/v2/version"


r=$?
cd -

docker-compose down -v
exit $r
