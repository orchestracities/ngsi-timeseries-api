from translators.table_cache import *
import pytest

def test_insert():
    y = TableCacheManager()
    y.add("Test.TestEntity", "boh")
    z = TableCacheManager()
    assert str(y) == str(z)
    z.add("Test2.TestEntity2", "boh2")
    assert str(y) == str(z)
    z.add("Test.TestEntity", "bohNew")
    assert str(y) == str(z)
    x = TableCacheManager()
    assert str(y) == str(z)
    assert str(y) == str(x)
    c_1 = x.get("Test.TestEntity")
    w = TableCacheManager()
    c_2 = w.get("Test.TestEntity")
    assert str(c_1) == str(c_2)
    w.pop("Test.TestEntity")
    assert str(w) == str(x)
    assert w.get("--meta--") is None