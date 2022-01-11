# Results Pagination

QuantumLeap API implements a pagination mechanism in order to help clients to
retrieve large sets of resources. The following parameters work for all listing
operations in the API:

- `limit`: in order to specify the maximum number of elements
  (minimum: `1` default: `10000`)
- `offset`: in order to select the starting point of the returned result set

Leveraging them it is possible to paginate results:

```json
...?offset=0&limit=10000        # fetch the first 10000 query results
...?offset=10001&limit=20000    # fetch the next 10000
...
```
