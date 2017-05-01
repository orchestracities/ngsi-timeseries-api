[x] - First discover how an Orion notification truly looks like (Orion docs and Comet docs show slightly different things)

[x] - In python, simulate entities with one attr of each type. Create random N instances.
    [x] - Use DateTime attr.
    [x] - Use geo:json attr.
    [ ] - Implement time and geo attrs for influx to complete comparison?

[ ] - Create a simple tests one for Influx and one for Crate that:
    [x] - Insert N entities in db and retrieve them back. (List entities NGSI endpoint #1)  
    [x] - Insert N entities, update them M times.
    [x] - Test: Retrieve attrs by EntityID NGSI endpoint #2.
    
    [ ] - Test custom complex queries (Query NGSI endpoint #3).
        # Per attribute
        [ ] - attr_bool is True
        [ ] - attr_str > "middle"
        [ ] - attr_float > X
        [ ] - attr_time > X
        [ ] - attr_geo within X box.
        # Combined
        [ ] - 1 geo + 1 float + 1 str
        [ ] - 1 time + 1 float + 1 str
        [ ] - 1 geo + 1 str
        # Aggregation
        [ ] - Avg/Percentiles on attr_float


[ ] - Consider using Pandas for all timeseries in python.

[ ] - If deciding for Crate, test performance differences between having a single table vs a table per entity type.

[ ] - Create new tests integrating Orion to act as notifications manager.
[ ] - Consider using locust to get metrics of performance?

[ ] - Compare results with what it's already available in FIWARE (orion walkthrough, comet, etc)

[ ] - Use Grafana to plot some metrics examples and maybe derive new test cases.

[ ] - Dynamically create the tables based on the incoming entities. I.e, stop assuming form of entities.
[ ] - Complete adapter cornercases (Support Simple Query Language, or pattern-defined notifications)
[ ] - Integrate developed endpoints back into swagger definition to complement/extend NGSI api.

[ ] - Integrate tests with docker into CI.