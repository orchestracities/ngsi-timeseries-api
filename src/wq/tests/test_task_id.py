import pytest

from wq.task import CompositeTaskId

tags_supply = [[], [''], ['a', 'b'], ['a', 'b', 'c']]


@pytest.mark.parametrize('tags', tags_supply)
def test_uniqueness(tags):
    id1 = CompositeTaskId(*tags)
    id2 = CompositeTaskId(*tags)

    assert len(id1.id_seq()) == len(tags) + 1
    assert len(id2.id_seq()) == len(tags) + 1

    assert id1.id_seq() != id2.id_seq()


@pytest.mark.parametrize('tags', tags_supply)
def test_to_from_rq_key_is_identity(tags):
    task_id = CompositeTaskId(*tags)
    key = task_id.to_rq_key()
    parsed_seq = CompositeTaskId.from_rq_key(key)

    assert task_id.id_seq() == parsed_seq


@pytest.mark.parametrize('tags', tags_supply)
@pytest.mark.parametrize('n_elements', [1, 2, 3])
def test_key_matcher(tags, n_elements):
    task_id = CompositeTaskId(*tags)
    matcher = task_id.rq_key_matcher(n_elements)

    assert matcher.endswith('*')

    matched_elements = CompositeTaskId.from_rq_key(matcher[:-1])
    all_elements = task_id.id_seq()

    assert all_elements[0:n_elements] == matched_elements
