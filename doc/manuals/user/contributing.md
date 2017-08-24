## Contributions

Contributions are more than welcome in the form of pull requests.

You can either pick one of the open issues to work on, or provide enhancements according to your own needs. In any case, we suggest getting in touch beforehand to make sure the contribution will be aligned with the current development status.

## Development Setup and Structure

The development is mostly python3 based for now, and really in the early stages so things will change for sure. For now, you can start with:

    git clone https://github.com/smartsdk/ngsi-timeseries-api.git
    cd ngsi-timeseries-api
    python3 -m venv env
    pip install -r requirements.txt

    # if you want to test everything locally, you'll need to...
    source setup_dev_env.sh

Pytest is used as the testing framework, but since most of QL's functionality is integration of components, you'll find ```docker-compose.yml``` files in the test folders to be run as a setup for tests. If you see ```.travis.yml``` file you'll see how they are running today, but probably at some point it's worth exploring pytest-docker plugins.

The ```requirements.txt``` still needs to be split between testing and production, that's why the docker image is massive for now.

In the file tree structure you can find (to be refactored soon):

- **ngsi-timeseries-api**
    - **client**: holds a simple Orion Context Broker client to ease integration testing. To be moved out of here at some point.
    - **experiments**: sandbox for quick manual tests to try some stuff and derive new test cases.
    - **python-flask** : will hold the implementation of the swagger-defined API controllers.
    - **reporter**: this module is acting as the receiver of the notifications, who "parses/validates" them before being handled to the translators.
    - **translators**: specific translators for timeseries databases.
    - **utils**: common shared stuff looking for a better place to live in.
