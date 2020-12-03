#!/bin/bash

test_suite_header () {
  echo "======================================================================="
  echo "        $1 TESTS"
  echo "======================================================================="
}

docker pull smartsdk/quantumleap
docker build --cache-from smartsdk/quantumleap -t smartsdk/quantumleap .

cd src/translators/tests
test_suite_header "TRANSLATOR"
sh run_tests.sh
tot=$?
cd -

cd src/reporter/tests
test_suite_header "REPORTER"
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/geocoding/tests
test_suite_header "GEO-CODING"
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/sql/tests
test_suite_header "SQL"
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/utils/tests
test_suite_header "UTILS"
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

cd src/tests/
test_suite_header "BACKWARD COMPAT & INTEGRATION"
sh run_tests.sh
loc=$?
if [ "$tot" -eq 0 ]; then
   tot=$loc
fi
cd -

docker rmi quantumleap

exit $tot
