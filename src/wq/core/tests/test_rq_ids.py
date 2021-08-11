import pytest

from wq.core.rqutils import RQ_JOB_KEY_PREFIX, \
    job_id_to_job_key, job_id_from_job_key, job_key_matcher


job_id_supply = ['', ':', ' ', ' :', ': ', ' : ', '::', ': :',
                 'x', 'x:y', ':x', '::x', '::x::y', 'x : y:']


@pytest.mark.parametrize('job_id', job_id_supply)
def test_to_from_key_is_identity(job_id):
    key = job_id_to_job_key(job_id)
    jid = job_id_from_job_key(key)

    assert jid == job_id


@pytest.mark.parametrize('job_id', job_id_supply)
def test_from_to_key_is_identity(job_id):
    key = f"{RQ_JOB_KEY_PREFIX}{job_id}"
    jid = job_id_from_job_key(key)
    k = job_id_to_job_key(jid)

    assert k == key


@pytest.mark.parametrize('job_id', job_id_supply)
def test_job_key_matcher(job_id):
    pattern = f"{job_id}*"
    key_pattern = job_key_matcher(pattern)
    parsed = job_id_from_job_key(key_pattern)

    assert parsed == pattern


def test_jid_to_key_error_on_none():
    with pytest.raises(ValueError):
        job_id_to_job_key(None)


def test_jid_from_key_error_on_none():
    with pytest.raises(ValueError):
        job_id_from_job_key(None)


def test_job_key_matcher_error_on_none():
    with pytest.raises(ValueError):
        job_key_matcher(None)
