#!/bin/bash

docker build -t quantumleap .

cd client/tests
tot=$(sh run_tests.sh)
cd -

cd translators/tests
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd reporter/tests
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

docker rmi quantumleap

exit $tot
