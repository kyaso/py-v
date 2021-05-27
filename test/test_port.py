import pytest
from port import *

class TestPort:
    def test_read(self):
        A = Port()
        A.val = 42
        assert A.read() == 42
    
    def test_write(self):
        A = Port()
        A.write(123)
        assert A.val == 123
    
    def test_connect(self):
        A = Port()
        B = Port()
        C = Port()
        B.connect(A)
        C.connect(B)

        # Check drivers
        assert B._driver == A
        assert C._driver == B
        assert A._driver == A

        # Write to A
        A.write(410)
        assert B.read() == 410
        assert C.read() == 410

        # Write to B (shouldn't be possible)
        with pytest.raises(Exception):
            B.write(46)
        
        # Write to C (same as B)
        with pytest.raises(Exception):
            C.write(38)

class TestPortX:
    def test_portx(self):
        # Init
        A = PortX('one', 'two', 'three')

        # Test write
        A.write('one', 42, 'two', 45)
        assert A.val['one'].val == 42
        assert A.val['two'].val == 45
        assert A.val['three'].val == 0

        # Test reading all subports
        ret = A.read()
        assert ret['one'] == 42
        assert ret['two'] == 45
        assert ret['three'] == 0

        # Test reading one subport
        ret = A.read('one')
        assert ret == 42

        # Test reading another subport
        ret = A.read('two')
        assert ret == 45

        # Test reading multiple subports
        val1, val2 = A.read('two', 'one')
        assert val1 == 45
        assert val2 == 42

        # Test writing to all subports using dict
        new = {'one':89, 'two':12, 'three':90}
        A.write(new)
        assert A.val['one'].val == 89
        assert A.val['two'].val == 12
        assert A.val['three'].val == 90

        # Test reading with square brackets operator
        for key, val in A.val.items():
            assert A[key] is A.val[key]

        # Test connecting other port to sub-port
        B = Port()
        A['two'].connect(B)
        B.write(5678)
        assert A.val['two'].read() == 5678

    def test_errors(self):
        A = PortX('one', 'two', 'three') 

        # Test invalid sq. brackets assignment
        with pytest.raises(TypeError):
            A['three'] = 3

        # Test connecting non-PortX
        with pytest.raises(TypeError):
            A.connect(42) # Just pass an integer as "driver"
        

