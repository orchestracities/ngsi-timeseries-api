#!/usr/bin/env bash

#
# curl commands useful for manual testing of geo queries.
# The queries below are the HTTP version of the ones in the companion file
# 'test_geo_queries_endpoint.sql'.
#

export BASE_1T1ENA_URL=http://0.0.0.0:8668/v2/types/TestDevice/attrs/location


###### covered by

# expect d1
curl "${BASE_1T1ENA_URL}?georel=coveredBy&geometry=line&coords=0,0;0,2"

# expect d1, d2
curl "${BASE_1T1ENA_URL}?georel=coveredBy&geometry=polygon&coords=-0.1,-0.1;-0.1,2.1;1.1,2.1;1.1,-0.1;-0.1,-0.1"


###### intersects

# expect d1
curl "${BASE_1T1ENA_URL}?georel=intersects&geometry=line&coords=0,1;0,2"

# expect d2
curl "${BASE_1T1ENA_URL}?georel=intersects&geometry=point&coords=1,1"

# expect d1, d2
curl "${BASE_1T1ENA_URL}?georel=intersects&geometry=polygon&coords=-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1"


###### disjoint

# expect d1, d2
curl "${BASE_1T1ENA_URL}?georel=disjoint&geometry=polygon&coords=0,3;0,4;1,4;1,3;0,3"

# expect none
curl "${BASE_1T1ENA_URL}?georel=disjoint&geometry=polygon&coords=-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1"


###### equals

# expect query not supported
curl "${BASE_1T1ENA_URL}?georel=equals&geometry=line&coords=0,0;0,2"


###### invalid geo params

curl "${BASE_1T1ENA_URL}?georel=disjoint&coords=0,0;0,2"