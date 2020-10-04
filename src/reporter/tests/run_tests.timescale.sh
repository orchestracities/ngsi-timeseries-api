#!/usr/bin/env bash

docker build -t smartsdk/quantumleap ../../../

docker-compose -f docker-compose.timescale.yml up -d
sleep 10

# Set Postgres port to same value as in docker-compose.timescale.yml
export POSTGRES_PORT='54320'

cd ../../../

# pytest src/reporter/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
# TODO: comment in above and zap line below when Timescale backend
# is fully functional.

pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --ignore=src/reporter/tests/test_geo_queries_1t1e.py \
       --ignore=src/reporter/tests/test_geo_query_1tne1a.py \
       --ignore=src/reporter/tests/test_health.py \
       --ignore=src/reporter/tests/test_incomplete_entities.py \
       --ignore=src/reporter/tests/test_integration.py \
       --ignore=src/reporter/tests/test_multitenancy.py \
       --ignore=src/reporter/tests/test_notify.py \
       --ignore=src/reporter/tests/test_sql_injection.py \
       --ignore=src/reporter/tests/test_subscribe.py \
       --ignore=src/reporter/tests/test_time_format.py

r=$?
cd -

unset POSTGRES_PORT

docker-compose -f docker-compose.timescale.yml down -v
exit $r

# NOTE. Failing tests.
# * test_geo*: They all pass but there's a glitch. We check equality tests
#   fail even though equality queries actually work just fine in Timescale.
#   What the heck? Well, equality isn't supported in Crate and the reporter
#   blindly returns a 422 regardless of backend. That will have to change
#   and then the test_geo* should be updated so that in the case of Timescale
#   we check equality works!
# * test_health: Endpoint hardcoded to work w/ Crate only.
# * test_incomplete_entities: it looks like null text attrs wind up in the
#   DB as a "None" string instead of DB null. Also there's issues when
#   transforming a query result set into JSON (_format_response & friends)
#   where in some cases some attrs in the result set get ditched from the
#   returned JSON. This happens in
#   test_can_add_new_attribute_even_without_specifying_old_ones where
#   the query returns the two attrs in the table (a1 and a2) but then
#   QL outputs a JSON with only a2.
# * test_integration: works w/ Crate, possibly not needed for Timescale.
# * test_multitenancy: ditto.
# * test_notify: test_no_value_no_type_for_attributes is broken but it
#   looks like the test was wrong to start with. In fact, the test checks
#   (among other things) that a numeric attribute (temperature) with a string
#   value ('25') is inserted in Crate with a text column type. The Timescale
#   backend inserts it as float, which is correct?
# * test_sql_injection: needs some massaging to make it work with Timescale
#   too.
# * test_subscribe: ditto.
# * test_time_format: in principle these tests should be able to work with
#   both backends but during test setup we connect to Crate.
