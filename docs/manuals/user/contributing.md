# Contributions

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
1. Recall to update docs. Markdown documents, need to follow best practises.
  To help you in linting your markdown before pushing changes, use the script
  `lint.md.sh`.
1. If so, create a pull request against our repository (we cannot review pull
  requests with failing tests)
1. Wait for the review
    - Implement required changes
    - Repeat until approval
1. Done :) You can delete the branch in your repository.

## Requirements

- [Python 3.8](https://docs.python-guide.org/starting/installation/)
- [Docker](https://docs.docker.com/get-docker/)
- [Docker compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

[pytest](https://docs.pytest.org/en/latest/) is used as the testing framework,
but since most of QL's functionality is integration of components, you'll find
`docker-compose.yml` files in the test folders to be run as a setup for tests.
If you see `.circleci/config.yml` file you'll see how they are running today, but
probably at some point it's worth exploring *pytest-docker* plugins.

## Development Setup

Once you installed the requirements, setting up the development environment
is straight forward:

```bash
git clone https://github.com/orchestracities/ngsi-timeseries-api.git
cd ngsi-timeseries-api
pipenv install --dev

# if you want to set up a dev env to test everything locally, you'll need to...
source setup_dev_env.sh
```

To run tests (assuming you run `source setup_dev_env.sh`):

```bash
sh run_tests.sh
```

## Using Gunicorn & fine tuning it

Details on how to use Quantum Leap WSGI app in Gunicorn:

```bash
cd ngsi-timeseries-api/src
gunicorn server.wsgi --config server/gconfig.py
```

### Security Settings

#### limit_request_line

```bash
--limit-request-line INT
4094
```

#### limit_request_fields

```bash
--limit-request-fields INT
100
```

This parameter is used to limit the number of headers in a request to prevent
DDOS attack.  Used with the `limit_request_field_size` it allows more safety.
By default this value is 100 and can’t be larger than 32768.

#### limit_request_field_size

```bash
--limit-request-field_size INT
8190
```

Limit the allowed size of an HTTP request header field.
Value is a positive number or 0. Setting it to 0 will allow unlimited header
field sizes.

## Repository Structure

In the current project tree structure you can find:

- `ngsi-timeseries-api`
  - `docs`: Holds documentation files.
  - `docker`: To hold docker-related files for the scope of the project.
  - `experiments`: Sandbox for quick manual tests to try some stuff and
  derive new test cases.
  - `specification`: Contains the OpenAPI definition that QL implements.
  - `src`: Source code folder.
    - `geocoding`: Holds the code for interacting with OSM and doing geo-related
      processing.
    - `reporter`: Modules acting as the receiver of the notifications and API
      requests. It "parses/validates" them before handling tasks
      to the translators.
    - `translators`: Specific translators for each time-series databases,
    responsible for interacting with the lower-level database details.
    - `utils`: Common shared stuff looking for a better place to live in.

[contrib]: https://github.com/orchestracities/ngsi-timeseries-api/blob/master/CONTRIBUTING.md
    "Contributing to QuantumLeap"
[fiware-contrib]: https://github.com/FIWARE/contribution-requirements/
    "FIWARE Platform Contribution Requirements"
