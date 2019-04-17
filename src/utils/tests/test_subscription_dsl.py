from utils.subscription_dsl import throttling


def test_throttling():
    assert throttling(None).to_dict() == {'throttling': 1}
    assert throttling(0).to_dict() == {'throttling': 0}
    assert throttling(1).to_dict() == {'throttling': 1}
