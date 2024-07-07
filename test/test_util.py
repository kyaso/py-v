import pytest
from pyv.util import getBit, getBits, getBitVector, VMap, PyVObj, VArray
from unittest.mock import MagicMock
from pyv.module import Module
from pyv.port import Input


def test_getBit():
    assert getBit(1, 0) == 1
    assert getBit(1, 1) == 0
    assert getBit(8, 3) == 1


def test_getBits():
    assert getBits(3, 1, 0) == 3
    assert getBits(3, 1, 1) == 1
    assert getBits(3, 0, 0) == 1
    assert getBits(15, 3, 2) == 3
    assert getBits(0xdeadbeef, 31, 1) == 0x6F56DF77


def test_getBitVector():
    assert getBitVector(0xAA, 0) == [1, 0, 1, 0, 1, 0, 1, 0]
    assert getBitVector(0xAA, 11) == [0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    with pytest.warns(UserWarning):
        assert getBitVector(0x39, 4) == [1, 0, 0, 1]


class TestVMap:
    @pytest.fixture
    def map(self) -> VMap:
        obj1 = PyVObj()
        obj1._init = MagicMock()
        obj2 = PyVObj()
        obj2._init = MagicMock()
        map_ = VMap({'foo': obj1, 'bar': obj2})
        return map_

    def test_constructor(self):
        map = VMap({'foo': 0, 'bar': 1})
        assert map._elems == {'foo': 0, 'bar': 1}

    def test_should_throw_exception_if_invalid_dict(self):
        with pytest.raises(TypeError):
            _ = VMap(42)

    def test_init_visited(self, map: VMap):
        assert map._visited == False
        map._init()
        assert map._visited == True

    def test_init_subobjs(self, map: VMap):
        map._init()
        map._elems['foo']._init.assert_called_once()
        map._elems['bar']._init.assert_called_once()

    def test_init_subobj_naming(self, map: VMap):
        map.name = "alpha.map"
        map._init()
        assert map._elems['foo'].name == 'alpha.map.foo'
        assert map._elems['bar'].name == 'alpha.map.bar'

    def test_init_parent_passthrough(self, map: VMap):
        parent = PyVObj()
        map._init(parent)
        map._elems['foo']._init.assert_called_once_with(parent)
        map._elems['bar']._init.assert_called_once_with(parent)

    def test_init_exception_when_non_pyvobj(self, map: VMap):
        map._elems['char'] = 42
        with pytest.raises(Exception):
            map._init()

    def test_access_operator(self, map: VMap):
        assert map['foo'] == map._elems['foo']
        assert map['bar'] == map._elems['bar']

    def test_module_process_pass_through(self, map: VMap):
        mod = Module()
        mod.map = map
        map._elems['input'] = Input(int)

        mod._init()

        assert map['input']._processMethodHandler._processMethods == [mod.process]


class TestVArray:
    @pytest.fixture
    def arr(self) -> VArray:
        obj1 = PyVObj()
        obj1._init = MagicMock()
        obj2 = PyVObj()
        obj2._init = MagicMock()
        arr_ = VArray(obj1, obj2)
        return arr_

    def test_constructor(self):
        arr = VArray(42, 64)
        assert arr._elems == [42, 64]

    def test_init_visited(self, arr: VArray):
        assert arr._visited == False
        arr._init()
        assert arr._visited == True

    def test_init_subobjs(self, arr: VArray):
        arr._init()
        arr._elems[0]._init.assert_called_once()
        arr._elems[1]._init.assert_called_once()

    def test_init_subobj_naming(self, arr: VArray):
        arr.name = "alpha.arr"
        arr._init()
        assert arr._elems[0].name == 'alpha.arr[0]'
        assert arr._elems[1].name == 'alpha.arr[1]'

    def test_init_parent_passthrough(self, arr: VArray):
        parent = PyVObj()
        arr._init(parent)
        arr._elems[0]._init.assert_called_once_with(parent)
        arr._elems[1]._init.assert_called_once_with(parent)

    def test_init_exception_when_non_pyvobj(self, arr: VArray):
        arr._elems.append(42)
        with pytest.raises(Exception):
            arr._init()

    def test_access_operator(self, arr: VArray):
        assert arr[0] == arr._elems[0]
        assert arr[1] == arr._elems[1]

    def test_module_process_pass_through(self, arr: VArray):
        mod = Module()
        mod.arr = arr
        arr._elems.append(Input(int))

        mod._init()

        assert arr[2]._processMethodHandler._processMethods == [mod.process]
