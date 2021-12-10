# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from conftest import crate_translator, timescale_translator

import pytest

from translators.tests.conftest import check_crate

translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_health_pass(translator):
    health = translator.get_health()
    assert health['status'] == 'pass'


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_health_fail(docker_services, translator):
    docker_services._docker_compose.execute('stop', 'crate')
    docker_services._docker_compose.execute('stop', 'timescale')
    health = translator.get_health()
    assert health['status'] == 'fail'
    docker_services.start('crate')
    docker_services.start('timescale')
    docker_services.start('quantumleap-db-setup')

    docker_services.wait_for_service(
        "crate",
        4200,
        check_server=check_crate,
    )
