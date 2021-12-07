#!/usr/bin/env bash


rep=$(curl -s --unix-socket /var/run/docker.sock http://ping > /dev/null)
status=$?

if [ $status -eq 7 ]; then
    echo 'docker is not running - test will not be executed'
    exit 1
fi

echo "creating test directory..."
mkdir -p test-results



test_suite_header () {
  echo "======================================================================="
  echo "        $1 TESTS"
  echo "======================================================================="
}

tot=$?

if [ -z $tests ] || [ $tests = "translator" ]; then
  cd src/translators/tests
  test_suite_header "TRANSLATOR"
  sh run_tests.sh
  loc=$?
  if [ "$tot" -eq 0 ]; then
    tot=$loc
  fi
  cd -
fi

if [ -z $tests ] || [ $tests = "reporter" ]; then
  cd src/reporter/tests
  test_suite_header "REPORTER"
  sh run_tests.sh
  loc=$?
  if [ "$tot" -eq 0 ]; then
    tot=$loc
  fi
  cd -
fi

if [ -z $tests ] || [ $tests = "integration" ]; then
  cd src/tests/
  test_suite_header "BACKWARD COMPAT & INTEGRATION"
  sh run_tests.sh
  loc=$?
  if [ "$tot" -eq 0 ]; then
    tot=$loc
  fi
  cd -
fi

if [ -z $tests ] || [ $tests = "others" ]; then
  cd src/geocoding/tests
  test_suite_header "GEO-CODING"
  sh run_tests.sh
  loc=$?
  if [ "$tot" -eq 0 ]; then
    tot=$loc
  fi
  cd -

  cd src/cache/tests
  test_suite_header "CACHE"
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

  cd src/wq/tests
  test_suite_header "WORK QUEUE"
  sh run_tests.sh
  loc=$?
  if [ "$tot" -eq 0 ]; then
    tot=$loc
  fi
  cd -
fi

exit $tot
