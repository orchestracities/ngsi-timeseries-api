import pytest
from redis import Redis
from rq import Queue
from rq.job import Job

from wq.core.rqutils import RqJobKey, RqJobId, \
    job_id_to_job_key, find_job_keys, find_job_ids, \
    starts_with_matcher, find_job_ids_in_registry, \
    find_pending_job_ids, find_successful_job_ids, find_failed_job_ids, \
    load_jobs


job_id_supply = [[], ['my:jobbie'], ['1', '2', 'bbx==:Aw==:', 'my:jobbie']]


def to_keys(job_ids: [RqJobId]) -> [RqJobKey]:
    return [job_id_to_job_key(j) for j in job_ids]


class FakeRedis(Redis):

    def __init__(self, keys: [RqJobKey]):
        self.key_supply = keys

    def iter_keys(self):
        for k in self.key_supply:
            yield k.encode('utf-8')

    def scan_iter(self, *args, **kwargs):
        return self.iter_keys()

    def zscan_iter(self, *args, **kwargs):
        for k in self.iter_keys():
            score = 0
            yield k, score

    def close(self):
        pass


def setup_fake_redis(keys: [RqJobKey], monkeypatch):
    r = FakeRedis(keys)
    monkeypatch.setattr('wq.core.rqutils.redis_connection', lambda: r)


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_job_keys(monkeypatch, job_ids):
    keys = to_keys(job_ids)
    setup_fake_redis(keys, monkeypatch)

    found = [x for x in find_job_keys('*')]
    assert found == keys


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_job_ids(monkeypatch, job_ids):
    keys = to_keys(job_ids)
    setup_fake_redis(keys, monkeypatch)

    found = [x for x in find_job_ids('*')]
    assert found == job_ids


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_job_ids_starting_with(monkeypatch, job_ids):
    keys = to_keys(job_ids)
    setup_fake_redis(keys, monkeypatch)

    matcher = starts_with_matcher('wot-eva')
    found = [x for x in find_job_ids(matcher)]
    assert found == job_ids


def test_starts_with_matcher_error_on_none():
    with pytest.raises(ValueError):
        starts_with_matcher(None)


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_job_ids_in_registry(monkeypatch, job_ids):
    setup_fake_redis(job_ids, monkeypatch)

    found = [x for x in find_job_ids_in_registry('reg', 'wot-eva*')]
    assert found == job_ids


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_pending_job_ids(monkeypatch, job_ids):
    setup_fake_redis(job_ids, monkeypatch)
    q = Queue(connection=object())

    found = [x for x in find_pending_job_ids(q, 'wot-eva*')]
    assert found == (job_ids * 3)    # (*)
# NOTE.
# We scan the mock three times, once for each started, deferred and scheduled
# job registries.


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_successful_job_ids(monkeypatch, job_ids):
    setup_fake_redis(job_ids, monkeypatch)
    q = Queue(connection=object())

    found = [x for x in find_successful_job_ids(q, 'wot-eva*')]
    assert found == job_ids


@pytest.mark.parametrize('job_ids', job_id_supply)
def test_find_failed_job_ids(monkeypatch, job_ids):
    setup_fake_redis(job_ids, monkeypatch)
    q = Queue(connection=object())

    found = [x for x in find_failed_job_ids(q, 'wot-eva*')]
    assert found == job_ids


def generate_job_ids_to_fetch(size: int):
    def to_jid(i: int):
        return None if i % 10 == 0 else str(i)
    return [to_jid(i) for i in range(size)]


def fake_fetch_many(job_ids, connection, serializer=None):
    def to_job(jid):
        return None if jid is None else Job(id=jid, connection=connection)
    return [to_job(jid) for jid in job_ids]


@pytest.mark.parametrize('job_ids', [
    [], ['1'], generate_job_ids_to_fetch(100),
    generate_job_ids_to_fetch(110)
    # batch size = 100 & cost = 1, so 110 should get split into 2 batches
])
def test_load_jobs(monkeypatch, job_ids):
    monkeypatch.setattr('wq.core.rqutils.Job.fetch_many', fake_fetch_many)
    js = load_jobs(job_ids)

    actual_job_ids = [j.id for j in js]
    expected_job_ids = [i for i in job_ids if i is not None]

    assert actual_job_ids == expected_job_ids
