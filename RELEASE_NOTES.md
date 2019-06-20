# QuantumLeap Release Notes

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
