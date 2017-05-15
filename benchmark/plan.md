[x] - First discover how an Orion notification truly looks like (Orion docs and Comet docs show slightly different things)

[x] - In python, simulate entities with one attr of each type. Create random N instances.
        [x] - Use DateTime attr.
        [x] - Use geo:json attr.
        - Will not implement time and geo attrs for influx to complete comparison

[ ] - Create a simple tests one for Influx and one for Crate that:
    [x] - Insert N entities in db and retrieve them back. (List entities NGSI endpoint #1)
    [x] - Insert N entities, update them M times.
    [x] - Test: Retrieve attrs by EntityID NGSI endpoint #2.
    [ ] - Test custom complex queries (Query NGSI endpoint #3).
        # Per attribute
        [x] - attr_bool is True
        [x] - attr_str > "middle"
        [x] - attr_float > X
        [x] - attr_time > X
        [x] - attr_geo within X box.
        [ ] - Rest of geo ops: near, coveredBy, intersects, equals, disjoint -> TODO later
        # Aggregation
        [x] - Avg on attr_float
        [ ] - Rest of aggregation functions -> TODO later


[ ] - Support time index on a particular entity attribute (i.e, DateModified is not necesarilly the time index). 
    In this case, it could be good to have, within the notification, the name of the DateTime attribute that is to be used as the index. 
    Moreover, in that case the support would be restricted to one notification per entity change (avoid complexity of batched notifications).
    That attribute could be specified in the "notification url" when creating the subscription.
    Or, investigate HttpCustom notifications (ngsi v2)
    
    When using the proper subscriptions/notifications, checkout the notification attributes format (attrsFormat), maybe this way we can simplify the translation step.
    
    Recall Fede's point: and the problem cygnus has now, we want to write as fast as possible, but also batch a bit to avoid single-row writes.
    Using a queue in the middle could be helpful in this regard (a proper one, like rabbit)
    
[ ] - Use Grafana to plot some metrics examples and maybe derive new test cases.

[ ] - Dynamically create the tables based on the incoming entities. I.e, stop assuming form of entities. One table per entity type.

[ ] - Create new tests integrating Orion to act as notifications manager.

[ ] - Integrate developed endpoints back into swagger definition to complement/extend NGSI API.

Extras:
[ ] - Consider using Pandas for all time-series in python if Quantumleap gets smarter
[ ] - Compare results with what it's already available in FIWARE (orion walk-through, comet, etc)
[ ] - Complete adapter cornercases (Fully support Simple Query Language, or pattern-defined notifications)
[ ] - Authentication? Maybe simple use api of key.
[ ] - Integrate tests with docker into CI (http://blog.terranillius.com/post/docker_testing/)

Extra info:
    https://www.theregister.co.uk/2016/12/14/crateio_unboxes_cratedb_10/
