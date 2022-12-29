# QuantumLeap Release Notes

## 0.9.0-dev

### New features

- Removed subscription API (#493)
- Replaced geocoder with [geopy](https://geopy.readthedocs.io/en/stable/) (#610)
- Bumped pillow from 8.4.0 to 9.0.0
- Aligned missing Fiware-servicePath behaviour with the one of Orion
  Context Broker (#564). This is a breaking change! Before no value for
  Fiware-servicePath was interpreted as python None, from now on, None
  will be replaced with /. This affects only users that manually injected
  data, since Orion, assume / when no servicePath is passed.
- Added more test cases for Aggregation (#499)
- fix translator initialization
- List Addix among adopters (#649)
- Replaced string with the constants (#650)
- Added idPattern ain query parameter (#648)
- Remove duplicate code in src/reporter/tests/test_timescale_types.py (#657)
- Removed comments on line no.462 and 467 in sql_translator.py (#659)
- Added logs in src/wq/ql/notify.py (#656)
- Added logs in src/wq/core/task.py (#662)
- Replaced entity with getter (#652)
- Resolved TODO in Dockerfile (#680)
- Resolved TODO at src/reporter/tests/test_timescale_types.py (#667)

### Bug fixes

- Fix issues with integration tests and backward compatibility tests
- Fix for linter failures (#670)
- Fix for issue broken docker image (#674)

### Continuous Integration

- Improve github action for docker images (#624)
- Add caching to docker image builds (#626)
- Update CI to use CrateDB 4.6.7 and Orion 3.3.1
- Add maintenance type to pr template

### Documentation

- Fix links in pr template (#620)
- Mention running tests locally as well as linting in PR template (#621)
- Fix variable names for CrateDB authentication (#636)

### Technical debt

## 0.8.3

### New features

- Added support for NGSI-LD temporal property 'modifiedAt' and 'observedAt' (#433)
- Added sql query to retrieve only last values of entities (#500)
- Support configuration of back off factor for CrateDB (#503)
- Added exception handling and updated response where
  'AggrMethod cannot be applied' (#498)
- Added a warning to use 'id' and 'type' from version 0.9 in all
   query responses (#584)
- Added instanceId for each entry received (#565)
- Support CrateDB authentication (#474)
- Updated PG8000 to 1.23.0 (#586)

### Bug fixes

- Fixed automated docker builds are broken (#557)
- Fixed arbitrary type arrays cause errors when inserting (#537)
- Fixed OpenAPI spec for /wq/management (#544)
- Fixed attributes names in /v2/entities query (#478)
- Fixed index ordering in /v2/entities query (#521)
- Fixed Deprecated warning by updating "warn" to "warning" (#605)

### Continuous Integration

- Increase test coverage (#524)
- Added workflow to check that `RELEASE_NOTES.md` is updated (#582)
- Added autopep8 workflow also to external pull requests (#601)
- Added request to update release notes to the pull request template (#585)
- Added codeql-analysis workflow (#588)
- Added wait for insert in instanceId and aggregation tests (#588)
- Added ci support for Crate 4.6.x (#594)

### Documentation

- Improved contributing documentation (#557)
- Introduced reference about `options=sysAttrs` for ngsi-ld time indexing (#546)
- Documented API pagination (#511)
- Revised documentation (#596)
- Fixed typos in roadmap and release notes (#617)

### Technical debt

## 0.8.2

### New features

- Support for CRATE 4.5 (#430)
- Introduced queue workflow support & upgraded gunicorn (#501)

### Bug fixes

- Fix "None" Tenant query caching (required for no multi-tenant orion deployment)

### Documentation

### Technical debt

## 0.8.1

### New features

- Optimise Gunicorn config for Docker image (#410)
- Batch inserts (#445)
- Increase resiliency to badly formatted data and support data casting (#444)

### Bug fixes

- Fix broken health check if no cache is used (#446)

## 0.8.0

### New features

- Experimental NGSI-LD support
  - Make the notify endpoint accept NGSI-LD payloads, convert them to
    tabular format and store them in the DB backend (#373)
  - Retain NGSI-v2 backward compatibility (#373)
  - Verify basic Orion-LD interoperability (#413)
- Improved performance
  - Make CrateDB async writes the default but allow the setting to be
    overwritten through configuration (#384)
  - Reduce DB queries on insert through a Redis metadata cache (#373)
  - Pool DB connections (#373)
- Expose configuration settings to enable/disable caching of geo-queries
  and metadata queries on insert (#429)
- Better logs
  - Adopt Orion log format and improve log messages (#373)
  - Log FIWARE correlation ID to support tracking of requests from
    agents (through Orion) to QuantumLeap (#373)
  - Add process and thread ID to log entries (#367)
  - Make log messages more descriptive and use debug log level (#355)
  - Timestamp log entries (#352)
- Assign NGSI attribute values a DB type according to their JSON type
  if no NGSI type is present rather than defaulting to text (#373)
- Make all API endpoints work with Timescale as a backend (#374)
- Support running QuantumLeap as a WSGI app in Gunicorn (#357)
- Collect telemetry time-series to analyse performance (#411)

### Bug fixes

- Honour default DB backend setting in YAML configuration (#405)
- Change health status from critical to warning when cache backend
  is down (#402)
- Explicitly add new columns to CrateDB tables to cater to corner cases
  where new columns aren't added if using Crate's dynamic column policy (#373)
- Log a warning if there's a type mismatch between NGSI and DB date-time
  rather than making queries crash (#387)
- Use proper ISO 8601 date-times and FIWARE service path match operator
  in CrateDB queries (#371)
- Use proper CrateDB types rather than deprecated aliases (#370)
- Assign entities to their respective service paths when a notification
  contains multiple service paths (#363, #364, #365)
- Return HTTP 500 on DB insert failure (#346)

### Documentation

- Note delay to be expected between an entity insertion and its subsequent
  availability for querying (#420)
- Update Japanese documentation (#414)
- Substantial updates regarding Redis cache, benchmarks and NGSI-LD
  support (#373)
- Gunicorn security settings for QuantumLeap (#380)
- Mention CrateDB lacks support for 3D coordinates (#340)

### Technical debt

- Clean up and refactor translator tests (#403)

## 0.7.6

### New features

- Save original data on translation error (#335)
- Make maximum number of rows a query can retrieve configurable (#330)
- Support CrateDB `4.x` series (#300)
- History of attributes from different entities with different types (#294)
- Introduce support for log level configuration (#299)
- History of attributes from different entities of the same type (#293)
- Make `entities` endpoint list IDs of all existing entities (#264)
- Move `version`, `config` and `health` endpoint to API root path (#261)

### Bug fixes

- Log values of environment variables when reading them in (#326)
- Reduce code duplication between CrateDB and Timescale translators;
  use UTC time consistently across the board for time indexing; fix
  date time SQL injection vulnerability (#315)
- Ignore attributes with null values (#298)
- Accept quoted values in API `fromDate` and `toDate` parameters (#285)
- Use standard header names for FIWARE service and service path (#283)
- Update tests for incomplete entities to take into account changes introduced
  by PR #278 (#282)
- Filter empty entities out of notification payload (#278)
- Pin Python/Alpine docker image to avoid dependency hell (#271)
- Make `/v2` return list of available API endpoints (#255)
- Update network interface in Travis build (#260)
- Update FIWARE CSS to avoid redirect URL (#252)

### Documentation

- Update Japanese documentation to cater for CrateDB `4.x` and environment
  variables (#333)
- Update contributors list (#307)
- Remove "Migrating STH Comet data" manual section as no longer supported (#267)
- Document data format expected by `notify` endpoint (#268)
- Timescale backend documentation (#263)
- Update Japanese documents (#280)
- Update broken link in in sanity check section of Japanese manual (#291)
- Updated broken links in sanity check section of manual (#289)
- Update broken links in CrateDB section of manual (#286)
- Update GitHub issue template (#259)
- State DB versions in README

### Important: Backward compatibility

This release breaks API backward compatibility. Existing `0.7.5` clients may
**not** be able to work with this new Quantum Leap version without code
changes.
In detail: version `0.7.6` changes the URL of the version, health and config
endpoints as indicated below:

      0.7.5           0.7.6
      -----           -----
    /v2/version      /version
    /v2/config       /config
    /v2/health       /health

Note that the semantics of the endpoints remains the same as version
 `0.7.5`.

## 0.7.5

- Fix bug with lastN parameter (#249)
- Update specification version to align with QL versions (#218)

## 0.7.4

- Fix bug with Custom Time Index header handling (#247)
- Timescale backend fixes (#243 #246)
- Bring back /ui endpoint (#229)
- Update dependencies (#244)

## 0.7.3

- Relax Crate health check (#239)
- Timescale backend teething troubles (#237)
- add coverall badge (#236)
- Coverage tool integration with travis (#221)

## 0.7.2

- Initial Timescale DB support (#231)

## 0.7.1

- Japanses Translations Update (#220)
- Remove OSM checks by default (#226)

## 0.7.0

- Flatten JSON in query results (#213)
- Data migration from STH-Comet to QuantumLeap (#184)

### Important: Backward compatibility

This release breaks API backward compatibility. Existing 0.6.3 clients will
**not** be able to work with Quantum Leap 0.7.0 without code changes.
In detail: version 0.7.0 changes the structure of query results. Up to
version 0.6.3, Quantum Leap used the following JSON format for query results:

    {
        data: {
           ...query results...
        }
    }

Version 0.7.0 removes the `data` field and puts all the fields that make up
the query result at the top level as in e.g.

    {
        entityId: ...,
        index: ...,
        values: ...
    }

## 0.6.3

- Fix queries involving attribute names (#206)

## 0.6.2

- Update connexion version (#203)
- Support nulls in NGSI_GEOPOINT values (#198)
- Documentation fixes (#195) (#200)
- Remove deprecated crate grafana plugin (#190)
- Support multiple data elements in notifications (#185)

## 0.6.1

- Fix CI issues (#186)
- Update package dependencies (#157)
- Added Backwards Compatibility testing (#173)
- Time_index enhancement (#172)
- Bugfix (#177)

## 0.6

- Update documentation (#168)
- Add curl to Docker image (#167)
- Enhanced Time Index selection policy (#161)
- Update vulnerable dependency (#158)
- Bugfixes in crate translator (#136)
- Bugfixes in geocoder (#105)

## 0.5.1

- Minor bugfix (#163)

## 0.5

Release 0.5 of QuantumLeap adds support for geographical queries and features
a streamlined, much smaller docker image as well as several bug fixes.

- Full support for geographical queries as specified by the FIWARE-NGSI v2
  Specification except for equality queries (#111)
- Optimised docker image, size is now down to 170 MB (#116)
- Support for missing entity attributes (#122)
- Metadata query fixes (#115)
- Documentation fixes (#112)

## 0.4.1

- Add: /health API endpoint (#68)
- Add: aggrPeriod support (#89)
- Add: Improve orion subscription options (#69)
- Chg: Use Pipenv, drop requirements.txt (#99)
- Fix: some inconsistent HTTP return errors
- Other minor fixes and adjustments
