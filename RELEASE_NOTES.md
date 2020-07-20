# QuantumLeap Release Notes

## 0.7.6

#### New features
- Save original data on translation error (#335)
- Make maximum number of rows a query can retrieve configurable (#330)
- Support CrateDB `4.x` series (#300)
- History of attributes from different entities with different types (#294)
- Introduce support for log level configuration (#299)
- History of attributes from different entities of the same type (#293)
- Make `entities` endpoint list IDs of all existing entities (#264)
- Move `version`, `config` and `health` endpoint to API root path (#261)

#### Bug fixes
- Log values of environment variables when reading them in (#326)
- Reduce code duplication between CrateDB and Timescale translators;
  use UTC time consistently across the board for time indexing; fix
  date time SQL injection vulnerability (#315)
- Ignore attributes with null values (#298)
- Accept quoted values in API `fromDate` and `toDate` parameters (#285)
- Use standard header names for FiWare service and service path (#283)
- Update tests for incomplete entities to take into account changes introduced
  by PR #278 (#282)
- Filter empty entities out of notification payload (#278)
- Pin Python/Alpine docker image to avoid dependency hell (#271)
- Make `/v2` return list of available API endpoints (#255)
- Update network interface in Travis build (#260)
- Update FIWARE CSS to avoid redirect URL (#252)

#### Documentation
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

#### Important: Backward compatibility
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

#### Important: Backward compatibility
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
