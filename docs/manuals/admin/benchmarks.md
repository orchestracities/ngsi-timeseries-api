# Basic benchmarks

QuantumLeap heavily relies on crate (or timescale) to query and store data model
configuration, this implies during insert an high number of queries on the
backend, despite the change of models between an insert and another of the same
entity type should not be that frequent.

As tested, caching reduce such number of queries, and thus increase throughput.
Previous test used in-memory cache, but that's not ideal in a concurrent
environment, thus we developed experimental support for REDIS based caching.

To measure basic insertion performances we developed a simple load script based
on [k6](https://k6.io/) that you can find
[here](https://github.com/smartsdk/ngsi-timeseries-api/blob/master/src/tests/run_load_tests.sh)

Example:

```bash
$ docker run -i --rm loadimpact/k6 run --vus 30 --duration 60s - < notify-load-test.js

    checks.....................: 100.00% ✓ 6000 ✗ 0   
    data_received..............: 1.6 MB  27 kB/s
    data_sent..................: 1.6 MB  27 kB/s
    http_req_blocked...........: avg=302.26µs min=1.62µs      med=6.21µs   max=1.05s   p(90)=10.21µs  p(95)=18µs    
    http_req_connecting........: avg=262.78µs min=0s          med=0s       max=1.05s   p(90)=0s       p(95)=0s      
    http_req_duration..........: avg=208.12ms min=16.92ms     med=155.56ms max=1.06s   p(90)=409.38ms p(95)=514.53ms
    http_req_receiving.........: avg=1.2ms    min=-8.817564ms med=158.96µs max=133.5ms p(90)=2.69ms   p(95)=5.99ms  
    http_req_sending...........: avg=89.36µs  min=12.59µs     med=38.08µs  max=20.85ms p(90)=111.97µs p(95)=218.72µs
    http_req_tls_handshaking...: avg=0s       min=0s          med=0s       max=0s      p(90)=0s       p(95)=0s      
    http_req_waiting...........: avg=206.82ms min=16.78ms     med=153.98ms max=1.06s   p(90)=406.54ms p(95)=513.29ms
    http_reqs..................: 6000    99.814509/s
    iteration_duration.........: avg=30.02s   min=30.02s      med=30.02s   max=30.03s  p(90)=30.02s   p(95)=30.02s  
    iterations.................: 60      0.998145/s
    vus........................: 30      min=30 max=30
    vus_max....................: 30      min=30 max=30
```

Tests shows that:

- caching metadata improves throughput of inserts , but usage of redis, has not
  the same impact as in memory

- the number of queries linked to metadata is not the only element affecting
  insert performance, due to the nature of http request, up to QuantumLeap
  v0.7.6, we created a db connection for each insert, opening the connection
  takes time.
  From v0.8 we reuse existing connections. This proved to increase throughput
  of 100% compared just to just redis caching.

System used for testing:
Mac2016 with 3.1 GhZ i7 (i.e. 4 cores) and 16GB Ram

- Baseline (v0.7.6): 44 req/s - 600 ms avg response time -
  (crate queries peak: select 111 q/sec, insert 54 q/sec)

- Redis caching: 60 req/s -  (no data collected on response time)

- In memory caching:  95 req/s - (no data collected on response time)

- Redis caching + connection re-usage: 100 req/s - 200 ms avg response time
  (crate queries peak: select 7 q/sec, insert 142 q/sec)

- Connection re-usage (without any cache): 55 req/s  - 400 ms avg response time
  (crate queries peak: select 177 q/sec, insert 86 q/sec)
  