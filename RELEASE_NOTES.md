# QuantumLeap Release Notes

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
