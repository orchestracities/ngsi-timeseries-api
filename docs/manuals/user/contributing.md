## Contributions

We welcome contributions and value your ideas. Please use GitHub Issues
if you would like to suggest ideas, request new features or enhancements,
or report bugs. To contribute code, open a GitHub Pull Requests. If you
are new to the project, we kindly ask you to review QuantumLeap's
[contribution guidelines][contrib] as well as FIWARE's [contribution
requirements][fiware-contrib].

To contribute code:

1. Fork the repository and clone the fork to your local development environment
1. Identify a modular contribution to the code (avoid too large contributions
    to simplify review)
1. Create a branch in your repository where you tackle the "modular
contributions"
   - For multiple contributions tackling different functionalities, create
   different branches
   - For all the new functionalities provide tests (see `setup_dev_env.sh`
   and `run.sh` in the root to understand how tests can be run locally)
1. When done, verify that all tests are passing
1. If so, create a pull request against our repository (we cannot review pull
   requests with failing tests)
1. Wait for the review
   - Implement required changes
   - Repeat until approval
1. Done :) You can delete the branch in your repository.


## Development Setup

The development is mostly in *python3* for now, and really in the early stages
so things will change for sure. For now, you can get started with:

```
git clone https://github.com/orchestracities/ngsi-timeseries-api.git
cd ngsi-timeseries-api
pipenv install

# if you want to set up a dev env to test everything locally, you'll need to...
source setup_dev_env.sh
```
Details on how to use Quantum Leap WSGI app in Gunicorn:

```
cd ngsi-timeseries-api/src
gunicorn server.wsgi --config server/gconfig.py
```
Security Settings:

###### limit_request_line
```
--limit-request-line INT
4094
```
The maximum size of HTTP request line in bytes.This parameter is used to limit the allowed size of a 
client’s HTTP request-line.

###### limit_request_fields

```
--limit-request-fields INT
100
```
This parameter is used to limit the number of headers in a request to prevent DDOS attack. 
Used with the limit_request_field_size it allows more safety. By default this value is 100 and can’t be larger than 32768.

###### limit_request_field_size
```
--limit-request-field_size INT
8190
```
Limit the allowed size of an HTTP request header field.
Value is a positive number or 0. Setting it to 0 will allow unlimited header field sizes.

[pytest](https://docs.pytest.org/en/latest/) is used as the testing framework,
but since most of QL's functionality is integration of components, you'll find
`docker-compose.yml` files in the test folders to be run as a setup for tests.
If you see `.travis.yml` file you'll see how they are running today, but
probably at some point it's worth exploring *pytest-docker* plugins.

The `requirements.txt` still needs to be split between testing and production,
that's also why the docker image is massive for now.

## Repository Structure

In the current project tree structure you can find:

- `ngsi-timeseries-api`
    - `docs`: Holds documentation files.
    - `docker`: To hold docker-related files for the scope of the project.
    - `experiments`: Sandbox for quick manual tests to try some stuff and
    derive new test cases.
    - `specification`: Contains the OpenAPI definition that QL implements.
    - `src`: Source code folder.
        - `geocoding`: Holds the code for interacting with OSM and doing geo-related processing.
        - `reporter`: Modules acting as the receiver of the notifications and API requests. It "parses/validates" them before handling tasks to the translators.
        - `translators`: Specific translators for each time-series databases,
        responsible for interacting with the lower-level database details.
        - `utils`: Common shared stuff looking for a better place to live in.




[contrib]: https://github.com/orchestracities/ngsi-timeseries-api/blob/master/CONTRIBUTING.md
    "Contributing to QuantumLeap"
[fiware-contrib]: https://github.com/FIWARE/contribution-requirements/
    "FIWARE Platform Contribution Requirements"
