import pytest
from pyv.util import VContainer, get_bit, get_bits, get_bit_vector, VMap, PyVObj, VArray
from unittest.mock import MagicMock
from pyv.module import Module
from pyv.port import Input


def test_get_bit():
    assert get_bit(1, 0) == 1
    assert get_bit(1, 1) == 0
    assert get_bit(8, 3) == 1


def test_get_bits():
    assert get_bits(3, 1, 0) == 3
    assert get_bits(3, 1, 1) == 1
    assert get_bits(3, 0, 0) == 1
    assert get_bits(15, 3, 2) == 3
    assert get_bits(0xdeadbeef, 31, 1) == 0x6F56DF77


def test_get_bit_vector():
    assert get_bit_vector(0xAA, 0) == [1, 0, 1, 0, 1, 0, 1, 0]
    assert get_bit_vector(0xAA, 11) == [0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    with pytest.warns(UserWarning):
        assert get_bit_vector(0x39, 4) == [1, 0, 0, 1]


class TestVContainer:
    class DUT_Container(VContainer):
        def __init__(self):
            super().__init__()

            self.obj1 = PyVObj()
            self.obj1._init = MagicMock()
            self.obj2 = PyVObj()
            self.obj2._init = MagicMock()
            self.A_i = Input(int)

    @pytest.fixture
    def con(self) -> DUT_Container:
        return self.DUT_Container()

    def test_init_visited(self, con: DUT_Container):
        assert con._visited == False
        con._init(None)
        assert con._visited == True

    def test_init_parent_passthrough(self, con: DUT_Container):
        parent = PyVObj()
        con._init(parent)
        con.obj1._init.assert_called_once_with(parent)
        con.obj2._init.assert_called_once_with(parent)

    def test_module_process_pass_through(self, con: DUT_Container):
        class Mod(Module):
            def __init__(self, name=''):
                super().__init__(name)
                self.con = con

            def process(self):
                pass

        mod = Mod()
        mod._init()

        assert con.A_i._process_method_handler._process_methods == [mod.process]

    def test_init_subobj_naming(self, con: DUT_Container):
        con.name = "alpha.foo"
        con._init(None)
        assert con.obj1.name == "alpha.foo.obj1"
        assert con.obj2.name == "alpha.foo.obj2"
        assert con.A_i.name == "alpha.foo.A_i"


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
        map._init(None)
        assert map._visited == True

    def test_init_subobjs(self, map: VMap):
        map._init(None)
        map._elems['foo']._init.assert_called_once()
        map._elems['bar']._init.assert_called_once()

    def test_init_subobj_naming(self, map: VMap):
        map.name = "alpha.map"
        map._init(None)
        assert map._elems['foo'].name == 'alpha.map.foo'
        assert map._elems['bar'].name == 'alpha.map.bar'

    def test_init_subobj_naming_int_key(self, map: VMap):
        map.name = "alpha.map"
        map._elems[42] = PyVObj()
        map._init(None)
        assert map._elems[42].name == 'alpha.map.42'

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
        class Mod(Module):
            def __init__(self, name=''):
                super().__init__(name)
                self.map = map
                self.map._elems['input'] = Input(int)

            def process(self):
                pass

        mod = Mod()
        mod._init()

        assert map['input']._process_method_handler._process_methods == [mod.process]

    def test_items(self, map: VMap):
        assert map.items() == map._elems.items()


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
        arr._init(None)
        assert arr._visited == True

    def test_init_subobjs(self, arr: VArray):
        arr._init(None)
        arr._elems[0]._init.assert_called_once()
        arr._elems[1]._init.assert_called_once()

    def test_init_subobj_naming(self, arr: VArray):
        arr.name = "alpha.arr"
        arr._init(None)
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
        class Mod(Module):
            def __init__(self, name=''):
                super().__init__(name)
                self.arr = arr
                self.arr._elems.append(Input(int))

            def process(self):
                pass

        mod = Mod()
        mod._init()

        assert arr[2]._process_method_handler._process_methods == [mod.process]
