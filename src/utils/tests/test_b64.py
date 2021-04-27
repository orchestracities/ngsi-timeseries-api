import pytest

from utils.b64 import *


char_supply = [c for c in '0xY!"#$%&()*+,-./:;<=>?@[]^_`{|}~å'] + \
              ["'", '\\', ' ', '\t', '\n', '\r']

plain_text_supply = [''] + char_supply + \
                    [''.join([x, y]) for x in char_supply for y in char_supply]


def test_to_b64_error_on_none():
    with pytest.raises(AttributeError):
        to_b64(None)


@pytest.mark.parametrize('plain_text', plain_text_supply)
def test_to_from_is_identity(plain_text):
    encoded = to_b64(plain_text)
    decoded = from_b64(encoded)

    assert plain_text == decoded


@pytest.mark.parametrize('xs', [
    [''], ['/x/y'], ['/x/y', '123'], ['/x/y', '123', 'abc'],
    ['', ''], ['x', ''], ['', 'x'],
    ['', '', ''], ['x', '', ''], ['', 'x', ''], ['', '', 'x']
])
def test_to_from_list_is_identity_if_len_gt_0(xs):
    encoded = to_b64_list(xs)
    decoded = from_b64_list(encoded)

    assert xs == decoded


@pytest.mark.parametrize('xs', [[], ['']])
def test_to_b64_list_return_empty(xs):
    assert to_b64_list(xs) == ''


def test_from_b64_list_return_singleton():
    assert from_b64_list('') == ['']


def test_to_b64_list_error_on_none():
    with pytest.raises(TypeError):
        to_b64_list(None)


def test_from_b64_list_error_on_none():
    with pytest.raises(AttributeError):
        from_b64_list(None)
