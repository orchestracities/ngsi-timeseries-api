**To migrate data from STH-Comet to QuantumLeap**

Fiware GE STH-Comet support NGSIv1 while QuantumLeap support NGSIv2. As NGSIv1 is being deprecated from Fiware Orion so using QuantumLeap will be preferred.
If we need to store data that was previously in STH-Comet to QuantumLeap we will have to follow the following steps:

1. Exporting Data from MongoDB
2. Adding Data into CrateDB

Migration-0.0.1-SNAPSHOT.jar file can be used to perform above task automatically. 

Jar file have dependency over ```application.properties``` , ```convert_json.py``` and ```dependency-jars``` to present at the same location as that of jar.

To run the jar user will have to configure following parameters in application.properties file:

1. To change the IP Address where Mongodb is running, change the value of the parameter: mongodbUrl
2. To change the port number where Mongodb is running, change the value of the parameter: mongodbPortNo
3. To change the IP Address where QuantumLeap is running, change the value of the parameter: qlUrl
4. To change the Port number where QuantumLeap is running, change the value of the parameter: qlPort
5. To change the IP Address where Cratedb is running, change the value of the parameter: cratedbUrl
6. To change the Port number where Cratedb is running, change the value of the parameter: cratedbPort
7. To change the Database Prefix (i.e. the name of the database starts starts with), change the value of the parameter: dbPrefix (for windows only). For Linux based system, its value is automatically taken from Environment Variable or config.js.
8. To change the dataModel, change the value of the parameter: dataModel (for windows only). For Linux based system, its value is automatically taken from Environment Variable or config.js.
9. To change the Container name for MongoDB, change the value of the parameter: mongoContainer (for Linux os only).
10. To change the Container name for STH-Comet, change the value of the parameter: sthContainer (for Linux os only).
11.	To specify whether STH-Comet is installed using docker, change the value of the parameter: isDocker (for Linux os only).

After making the above changes, use maven tool to rebuild the jar from code or use given jar.

**Note**
* The jar can be currently run on Windows and Linux platform only.
* An extra column “recvtime” is created in the CrateDB database table in this process which cannot be removed as Cratedb does not support the feature of dropping a column.
* In case of source installation of STH-Comet on Linux system, jar should run from the same location where fiware-sth-comet is present.

**Limitations**
* The parameters <Fiware-servicePath>, <entity-id> and <entity-type> are extracted from the STH collection name by splitting the name on the basis of ```_```. The data will not be properly migrated to QuantumLeap if the <fiware-servicePath> or <entity-id> or <entity-type> contains ```_```.

**View the data migrated in QuantumLeap**
The data can be viewed by the following two ways.
1. Using CrateDB GUI available at http://[CRATEDB_HOST:CRATEDB_PORT]/4200
2. Using QuantumLeap API:
```GET http://[QUANTUMLEAP_HOST]:[QUANTUMLEAP_PORT]/8688/v2/entities/<entity-id>```
Send Request Headers (if the data is not stored in the default database – “doc”) 
```fiware-service : dummyservice```
```fiware-servicePath : /dummyservicepath```
```Content-Type : “application/json”```

