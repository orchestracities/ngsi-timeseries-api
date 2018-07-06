## Contributions

Contributions are more than welcome in the form of pull requests.

You can either pick one of the [open issues](https://github.com/smartsdk/ngsi-timeseries-api/issues)
to work on, or provide enhancements according to your own needs. In any case,
we suggest getting in touch beforehand to make sure the contribution will be
aligned with the current development status.

To contribute:

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
so things will change for sure. For now, you can start with:

    git clone https://github.com/smartsdk/ngsi-timeseries-api.git
    cd ngsi-timeseries-api
    python3 -m venv env
    pip install -r requirements.txt

    # if you want to test everything locally, you'll need to...
    source setup_dev_env.sh

[pytest](https://docs.pytest.org/en/latest/) is used as the testing framework,
but since most of QL's functionality is integration of components, you'll find `docker-compose.yml` files in the test folders to be run as a setup for tests.
If you see `.travis.yml` file you'll see how they are running today, but
probably at some point it's worth exploring *pytest-docker* plugins.

The `requirements.txt` still needs to be split between testing and production,
that's also why the docker image is massive for now.

## Repository Structure

In the current project tree structure you can find:

- `ngsi-timeseries-api`
    - `client`: Holds a simple Orion Context Broker client to ease integration
    testing. To be moved out of this repo.
    - `doc`: Holds documentation files.
    - `docker`: To hold docker-related files for the scope of the project.
    - `experiments`: Sandbox for quick manual tests to try some stuff and
    derive new test cases.
    - `geocoding`: Holds the code for interacting with OSM and doing
    geo-related processing.
    - `reporter`: Modules acting as the receiver of the notifications and API
    requests. It "parses/validates" them before handling tasks to the
    translators.
    - `specification`: Holds the swagger-based *ngsi-tsdb* API specification
    that QL implements.
    - `translators`: Specific translators for each time-series databases,
    responsible for interacting with the lower-level database details.
    - `utils`: Common shared stuff looking for a better place to live in.
