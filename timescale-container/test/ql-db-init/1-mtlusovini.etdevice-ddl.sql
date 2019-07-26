CREATE SCHEMA IF NOT EXISTS mtlusovini;

CREATE TABLE IF NOT EXISTS mtlusovini.etdevice (
    accumulatedprecipitationlevel24 float,
    airhumidity float,
    airpressure float,
    airtemperature float,
    batterylevel float,
    entity_id text,
    entity_type text,
    fiware_servicepath text,
    latitude text,
    leafweatness float,
    location jsonb,
    location_centroid geometry,
    longitude text,
    manufacturername text,
    precipitationlevel float,
    previousprecipitationlevel float,
    soilmoisture450 float,
    soilmoisture800 float,
    soiltemperature float,
    solarradiation float,
    time_index timestamp WITH TIME ZONE NOT NULL,
               -- hyper-table requires a non-null time index
    timeinstant timestamp WITH TIME ZONE,
    winddirection text,
    windspeed float
);

SELECT create_hypertable('mtlusovini.etdevice', 'time_index',
                         if_not_exists => true);
