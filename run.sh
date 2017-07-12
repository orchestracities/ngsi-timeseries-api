#!/bin/bash

docker build -t quantumleap .

cd client/tests && sh run_tests.sh && cd -
cd translators/tests && sh run_tests.sh && cd -
cd reporter/tests && sh run_tests.sh && cd -
