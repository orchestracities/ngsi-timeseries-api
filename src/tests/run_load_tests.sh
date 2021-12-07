#!/usr/bin/env bash

#remember to start your quantumleap set up, e.g.
# docker build --cache-from orchestracities/quantumleap -t orchestracities/quantumleap ../../
# docker-compose up -d
# docker-compose stop orion
# docker-compose stop mongo

vegeta attack -targets=vegeta.test -rate=50 -duration=30s | tee results.bin | vegeta report

sleep 10

vegeta attack -targets=vegeta.test -rate=100 -duration=30s | tee results.bin | vegeta report
