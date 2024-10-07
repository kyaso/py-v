from pyv.port import Port


def check_port(port: Port, expected_port_type, expected_data_type):
    """Utility function to test ports.

    It checks whether `port` is an instance of `expected_port_type`
    (e.g. `Input`), and whether the port's data type matches
    `expected_data_type` (e.g. `int`).
    """
    assert isinstance(port, expected_port_type)
    assert port._type == expected_data_type
