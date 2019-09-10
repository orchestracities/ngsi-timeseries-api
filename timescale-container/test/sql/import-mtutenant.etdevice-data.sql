\c quantumleap

COPY mtutenant.etdevice(
     accumulatedprecipitationlevel24,
     airhumidity,
     airpressure,
     airtemperature,
     batterylevel,
     entity_id,
     entity_type,
     fiware_servicepath,
     latitude,
     leafweatness,
     location,
     location_centroid,
     longitude,
     manufacturername,
     precipitationlevel,
     previousprecipitationlevel,
     soilmoisture450,
     soilmoisture800,
     soiltemperature,
     solarradiation,
     time_index,
     timeinstant,
     winddirection,
     windspeed
)
FROM '/mtutenant.etdevice.csv'
WITH (FORMAT CSV, HEADER, DELIMITER ',', QUOTE '''');
