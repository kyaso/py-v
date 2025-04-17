"""Utility stuff."""

from typing import Any, Dict, List
import warnings


# TODO: Move this class to its own module
class PyVObj:
    """This class represent all Py-V objects (such as modules, ports,
    registers). Currently, this is used for initializing the names of every
    object in the design.
    """
    def __init__(self, name="noName") -> None:
        self.name = name
        """Name of this object"""
        self._visited = False

    def _init(self, parent=None):
        """Initializes the object.

        This includes the following steps:
        - Set the name of each child PyVObj instance
        - Recursively call `_init()` for each child `PyVObj` instance
        """
        if self._visited:
            return
        self._visited = True

        for key, obj in self.__dict__.items():
            if isinstance(obj, (PyVObj)):
                obj.name = self.name + "." + key
                obj._init(self)


class VContainer(PyVObj):
    """A class to group together `PyVObj` instances in a class-like
    manner.
    """
    def __init__(self):
        super().__init__()

    def _init(self, parent: PyVObj):
        if self._visited:
            return
        self._visited = True

        for key, obj in self.__dict__.items():
            if isinstance(obj, (PyVObj)):
                obj.name = self.name + "." + key
                obj._init(parent)


class VMap(PyVObj):
    """A class to group together `PyVObj` instances in a dictionary-like
    manner.

    VMap allows for the organization and manipulation of multiple `PyVObj`
    instances as a single collection, similar to a Python dictionary.
    """

    def __init__(self, dict_: dict) -> None:
        """Create a new VMap.

        Initialize the VMap with a dictionary of `PyVObj` objects.

        Args:
            dict_ (dict): A dictionary where keys are of any type and values
            are `PyVObj` objects.

        Raises:
            TypeError: If `dict_` is not a dictionary.
        """
        super().__init__()
        if not isinstance(dict_, dict):
            raise TypeError("ERROR: Please provide a valid dict to VMap!")
        self._elems: Dict[Any, PyVObj] = dict_

    def _init(self, parent: PyVObj):
        """Initialize the VMap elements.

        Sets the name and initializes each element in the VMap.

        Args:
            parent (PyVObj, optional): The parent object for initialization.
            Defaults to None.
        """
        if self._visited:
            return
        self._visited = True

        for key, obj in self._elems.items():
            obj.name = self.name + "." + str(key)
            obj._init(parent)

    def __getitem__(self, key):
        """Retrieve an element from the VMap by key.

        Args:
            key: The key of the element to retrieve.

        Returns:
            PyVObj: The element associated with the specified key.
        """
        return self._elems[key]

    def items(self):
        """Returns the list of items in _elems.
        """
        return self._elems.items()


class VArray(PyVObj):
    """A class to group together `PyVObj` instances in a list-like manner.

    VArray allows for the organization and manipulation of multiple `PyVObj`
    instances as a single collection, similar to a Python list.
    """

    def __init__(self, *args) -> None:
        """Create a new VArray.

        The elements of the VArray are passed as positional arguments.
        Each element provided as an argument will be included in the VArray.

        Args:
            *args: Variable length argument list. Each argument represents an
            element to be included in the VArray.
        """
        super().__init__()
        self._elems: List[PyVObj] = list(args)

    def _init(self, parent: PyVObj):
        """Initialize the VArray elements.

        Sets the name and initializes each element in the VArray.

        Args:
            parent (PyVObj, optional): The parent object for initialization.
            Defaults to None.
        """
        if self._visited:
            return
        self._visited = True

        for i, obj in enumerate(self._elems):
            obj.name = self.name + f"[{i}]"
            obj._init(parent)

    def __getitem__(self, idx):
        """Retrieve an element from the VArray by index.

        Args:
            idx (int): The index of the element to retrieve.

        Returns:
            PyVObj: The element at the specified index.
        """
        return self._elems[idx]


# XLEN
XLEN = 32

# 32 bit mask
MASK_32 = 0xffffffff


def msb_32(val) -> int:
    """Returns the MSB of a 32 bit value."""

    return (val & 0x80000000) >> 31


def get_bit(val, idx: int) -> int:
    """Gets a bit."""

    return (val >> idx) & 1


def get_bits(val, hiIdx: int, loIdx: int) -> int:
    """Returns a bit slice of a value.

    Args:
        val: Original value.
        hiIdx: Upper (high) index of slice.
        loIdx: Lower index of slice.

    Returns:
        The bit slice.
    """

    return (~(MASK_32 << (hiIdx - loIdx + 1)) & (val >> loIdx))


def signext(val, width: int):
    """Sign-extends a value (`val`) of width `width` bits to 32-bits."""

    msb = get_bit(val, width - 1)

    if msb:  # 1
        val = MASK_32 & ((-1) << width | val)

    return val


def get_bit_vector(val: int, len: int = 0):
    """Convert a number into a list with its binary representation.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        val (int): The value that we want to express as a binary list.
        len (int): Use this to pass a fixed length which the output vector
            should have. The bitlength of `val` must be less-than or equal to
            `len`, otherwise an exception is raised.

            A  value of 0 (default) will result in the minimum length needed to
            hold the binary representation of `val`.

    Returns:
        A list containing the bits of `val`.
    """
    if len == 0:
        return [1 if digit == '1' else 0 for digit in bin(val)[2:]]
    elif len >= val.bit_length():
        leading_zeros = [0 for _ in range(len - val.bit_length())]
        return (leading_zeros
                + [1 if digit == '1' else 0 for digit in bin(val)[2:]])
    else:
        num_trunc_bits = val.bit_length() - len
        warnings.warn(f"Util get_bit_vector(): Requested vector length ({len}) shorter than bit_length of value ({val.bit_length()}). Truncating upper {num_trunc_bits} bits.")  # noqa: E501
        return [
            1 if digit == '1' else 0 for digit in bin(val)[2 + num_trunc_bits:]
        ]


def bit_vector_2_num(bitVec: list):
    """Convert a bit list to a number.

    The list is assumed to be in "MSB-at-index-0" ordering.

    Args:
        bitVec (list): The bit list that we want to convert to a number.

    Returns:
        Integer value of input bit vector.
    """
    bitStr = ''.join(str(b) for b in bitVec)
    return int(bitStr, 2)
