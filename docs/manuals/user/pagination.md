# Pagination

NGSIv2 implements a pagination mechanism in order to help clients to retrieve
large sets of resources. This mechanism works for all listing operations in
the API

- limit, in order to specify the maximum number of elements(minimum: 1 
                                                            default: 10000)
- offset, in order to skip a given number of elements at the beginning

In principle we should be able to paginate results, so that we can fetch e.g.
pages of 10000 results at a time as in:

    ```
    ... ? offset = 0 & limit = 10000  # fetch the first 10000 query results
    ... ? offset = 10001 & limit = 20000    # fetch the next 10000
    ...
    ```
Let's illustrate with an example:

    `GET <host_ip>:8668/v2/entities?offset=1&limit=10`

Offset to apply to the response results. For
example, if the query was to return `10` results and you use an offset of
`1`, the response will return the last `9` values. Make sure you don't give
more offset than the number of results."

Please refer [link](https://github.com/orchestracities/ngsi-timeseries-api/issues/417) for same.
