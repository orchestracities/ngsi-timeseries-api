import pytest
from decimal import Decimal
from fractions import Fraction

from utils.kvt import node, forest, mforest


falsy = [None,
         False,
         0, 0.0, 0j, Decimal(0), Fraction(0, 1),
         '', (), [], {}, set(), range(0)]


@pytest.mark.parametrize('value', falsy)
def test_leaf_preserves_all_falsy_but_none(value):
    key = 'key'
    converted = node(key, value).to_dict()

    if value is None:
        assert converted is None
    else:
        assert converted == {key: value}


def test_empty_forest():
    assert forest().to_dict() is None


def test_forest_of_leaves():
    actual = forest(node('l1', 1), node('l2', 2)).to_dict()
    expected = [{'l1': 1}, {'l2': 2}]

    assert actual == expected


def test_forest_of_trees():
    target = forest(
        node('t1', 1),
        node('t2', forest(
            node('t2.1', forest(
                node('t2.1.1', 2),
                node('t2.1.2', 3),
            )),
            node('t2.2', 4)
        )),
        node('t3', 5)
    )

    actual = target.to_dict()
    expected = [
        {'t1': 1},
        {'t2': [
            {'t2.1': [
                {'t2.1.1': 2},
                {'t2.1.2': 3}
            ]},
            {'t2.2': 4}
        ]},
        {'t3': 5}
    ]

    assert actual == expected


def test_empty_mforest():
    assert mforest().to_dict() is None


def test_mforest_of_leaves():
    actual = mforest(node('l1', 1), node('l2', 2)).to_dict()
    expected = {'l1': 1, 'l2': 2}

    assert actual == expected


def test_mforest_of_trees():
    target = mforest(
        node('t1', 1),
        node('t2', mforest(
            node('t2.1', mforest(
                node('t2.1.1', 2),
                node('t2.1.2', 3),
            )),
            node('t2.2', 4)
        )),
        node('t3', 5)
    )

    actual = target.to_dict()
    expected = {
        't1': 1,
        't2': {
            't2.1': {
                't2.1.1': 2,
                't2.1.2': 3
            },
            't2.2': 4
        },
        't3': 5
    }

    assert actual == expected


def test_full_tree():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1', 1),
            node('l2', 2)
        )),
        node('n2', mforest(
            node('l3', 3),
            node('n2.1', forest(
                node('n2.1.1', mforest(
                    node('l5', 5),
                    node('l6', 6)
                )),
                node('l7', 7),
                node('l8', 8)
            )),
            node('l4', 4)
        )),
        node('n3', forest(
            node('n3.1', mforest(
                node('l9', 9),
                node('l10', 10)
            )),
            node('n3.2', mforest(
                node('l11', 11),
                node('l12', 12)
            ))
        ))
    ))

    expected = {
        'root': {
            'n1': {'l1': 1, 'l2': 2},
            'n2': {
                'l3': 3,
                'n2.1': [
                    {'n2.1.1': {'l5': 5, 'l6': 6}},
                    {'l7': 7},
                    {'l8': 8}
                ],
                'l4': 4
            },
            'n3': [
                {'n3.1': {'l9': 9, 'l10': 10}},
                {'n3.2': {'l11': 11, 'l12': 12}}
            ]
        }
    }

    assert root.to_dict() == expected


def test_prune_leaf():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1', None),
            node('l2', 2)
        )),
        node('n2', mforest(
            node('l3', 3),
            node('l4', 4)
        ))
    ))

    expected = {
        'root': {
            'n1': {
                'l2': 2
            },
            'n2': {
                'l3': 3,
                'l4': 4
            }
        }
    }

    assert root.to_dict() == expected


def test_prune_inner_node():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1', None),
            node('l2', None)
        )),
        node('n2', mforest(
            node('l3', 3),
            node('l4', 4)
        ))
    ))

    expected = {
        'root': {
            'n2': {
                'l3': 3,
                'l4': 4
            }
        }
    }

    assert root.to_dict() == expected


def test_prune_inner_nodes():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1.1', None),
            node('n1.2', mforest(
                node('l1.2.1', None)
            )),
            node('l1.3', None)
        )),
        node('n2', mforest(
            node('l2.1', 3),
            node('n2.2', mforest(
                node('l2.2.1', None),
                node('n2.2.1', mforest(
                    node('l2.2.1.1', None),
                    node('l2.2.1.2', None),
                ))
            )),
            node('l2.3', 4),
            node('n2.4', mforest(
                node('l2.4.1', 5),
                node('n2.4.2', mforest(
                    node('l2.4.2.1', None),
                    node('l2.4.2.2', 6)
                ))
            ))
        ))
    ))

    expected = {
        'root': {
            'n2': {
                'l2.1': 3,
                'l2.3': 4,
                'n2.4': {
                    'l2.4.1': 5,
                    'n2.4.2': {
                        'l2.4.2.2': 6
                    }
                }
            }
        }
    }

    assert root.to_dict() == expected


def test_prune_lists():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1', 1),
            node('l2', 2)
        )),
        node('n2', mforest(
            node('l3', 3),
            node('n2.1', forest(
                node('n2.1.1', mforest(
                    node('l5', None),
                    node('l6', 6)
                )),
                node('l7', 7),
                node('l8', 8)
            )),
            node('l4', 4)
        )),
        node('n3', forest(
            node('n3.1', mforest(
                node('l9', None),
                node('l10', None)
            )),
            node('n3.2', mforest(
                node('l11', None),
                node('l12', None)
            ))
        ))
    ))

    expected = {
        'root': {
            'n1': {'l1': 1, 'l2': 2},
            'n2': {
                'l3': 3,
                'n2.1': [
                    {'n2.1.1': {'l6': 6}},
                    {'l7': 7},
                    {'l8': 8}
                ],
                'l4': 4
            }
        }
    }

    assert root.to_dict() == expected


def test_dont_prune_falsy():
    root = node('root', mforest(
        node('n1', mforest(
            node('l1', 1),
            node('l2', 2)
        )),
        node('n2', mforest(
            node('l3', 3),
            node('n2.1', forest(
                node('n2.1.1', mforest(
                    node('l5', False),
                    node('l6', 6)
                )),
                node('l7', 7),
                node('l8', 8)
            )),
            node('l4', 4)
        )),
        node('n3', mforest(
            node('n3.1', mforest(
                node('l9', 0),
                node('l10', 0.0)
            )),
            node('n3.2', mforest(
                node('l11', set()),
                node('l12', {})
            ))
        ))
    ))

    expected = {
        'root': {
            'n1': {'l1': 1, 'l2': 2},
            'n2': {
                'l3': 3,
                'n2.1': [
                    {'n2.1.1': {'l5': False, 'l6': 6}},
                    {'l7': 7},
                    {'l8': 8}
                ],
                'l4': 4
            },
            'n3': {
                'n3.1': {'l9': 0, 'l10': 0.0},
                'n3.2': {'l11': set(), 'l12': {}}
            }
        }
    }

    assert root.to_dict() == expected
