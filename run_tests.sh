#!/bin/bash

docker pull smartsdk/quantumleap
docker build --cache-from smartsdk/quantumleap -t smartsdk/quantumleap .

cd src/translators/tests
sh run_tests.sh
tot=$?
cd -

cd src/reporter/tests
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/geocoding/tests
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/utils/tests
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/tests/
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

docker rmi quantumleap

exit $tot
