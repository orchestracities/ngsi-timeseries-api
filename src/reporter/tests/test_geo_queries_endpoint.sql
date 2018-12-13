--
-- Crate SQL statements useful for manual testing of geo queries.
--

-- =============================================================================
create table ettestdevice (
    entity_id string primary key,
    entity_type string,
    fiware_servicepath string,
    time_index timestamp,
    location geo_shape,
    location_centroid geo_point
)

drop table ettestdevice

-- =============================================================================
insert into ettestdevice
(entity_id, entity_type, fiware_servicepath, time_index,
    location, location_centroid)
values ('d1', 'TestDevice', '', 1544515561000,
    {type='LineString', coordinates=[[0, 0], [2, 0]]}, 'POINT(1 0)');

insert into ettestdevice
(entity_id, entity_type, fiware_servicepath, time_index,
    location, location_centroid)
values ('d2', 'TestDevice', '', 1544515561000,
    {type='LineString', coordinates=[[0, 1], [2, 1]]}, 'POINT(1 1)');

-- =============================================================================
select * from ettestdevice;
delete from ettestdevice;

-- =============================================================================
-- near [min, max]: expect d2
select * from ettestdevice where
((distance(location_centroid, 'POINT(1.0001 1.0)') >= 10)
and (distance(location_centroid, 'POINT(1.0001 1.0)') <= 20));

-- =============================================================================
-- covered by: expect d1
select * from ettestdevice
where match (location, {type='LineString', coordinates=[[0, 0], [2, 0]]}) using within;

-- covered by: expect d1, d2
select * from ettestdevice
where match (location, {type='Polygon', coordinates=[[[-0.1, -0.1], [2.1, -0.1], [2.1, 1.1], [-0.1, 1.1], [-0.1, -0.1]]]})
    using within;

-- =============================================================================
-- intersects: expect d1
select * from ettestdevice
where match (location, {type='LineString', coordinates=[[1, 0], [2, 0]]})
    using intersects;

-- intersects: expect d2
select * from ettestdevice
where match (location, {type='Point', coordinates=[1, 1]}) using intersects

-- intersects: expect d1, d2
select * from ettestdevice
where match (location, {type='Polygon', coordinates=[[[0.1, -0.1], [1, -0.1], [1, 1.1], [0.1, 1.1], [0.1, -0.1]]]})
    using intersects;

-- =============================================================================
-- disjoint: expect d1, d2
select * from ettestdevice
where match (location, {type='Polygon', coordinates=[[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]]})
    using disjoint;

-- disjoint: expect none
select * from ettestdevice
where match (location, {type='Polygon', coordinates=[[[0.1, -0.1], [1, -0.1], [1, 1.1], [0.1, 1.1], [0.1, -0.1]]]})
    using disjoint;

-- =============================================================================
-- equals: expect d1
select * from ettestdevice
where match (location, {type='LineString', coordinates=[[0, 0], [2, 0]]}) using within
    and within({type='LineString', coordinates=[[0, 0], [2, 0]]}, location)
