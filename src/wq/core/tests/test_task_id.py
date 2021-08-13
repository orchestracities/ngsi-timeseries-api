import pytest

from wq.core.task import CompositeTaskId

tags_supply = [[], [''], ['a', 'b'], ['a', 'b', 'c']]


@pytest.mark.parametrize('tags', tags_supply)
def test_uniqueness(tags):
    id1 = CompositeTaskId(*tags)
    id2 = CompositeTaskId(*tags)

    assert len(id1.id_seq()) == len(tags) + 1
    assert len(id2.id_seq()) == len(tags) + 1

    assert id1.id_seq() != id2.id_seq()


@pytest.mark.parametrize('tags', tags_supply)
def test_to_from_id_repr_is_identity(tags):
    task_id = CompositeTaskId(*tags)
    r = task_id.id_repr()
    parsed_seq = CompositeTaskId.from_id_repr(r)

    assert task_id.id_seq() == parsed_seq


@pytest.mark.parametrize('tags', tags_supply)
@pytest.mark.parametrize('n_elements', [1, 2, 3])
def test_parse_initial_segment(tags, n_elements):
    task_id = CompositeTaskId(*tags)
    init_seg_repr = task_id.id_repr_initial_segment(n_elements)
    parsed_seg = CompositeTaskId.from_id_repr(init_seg_repr)
    expected_seg = task_id.id_seq()[0:n_elements]

    assert parsed_seg == expected_seg
