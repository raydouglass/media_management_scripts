import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "test_logging.yaml")


def assertAudioLength(expected: int, actual: int):
    """
    Checks if the actualy is within 2% of the expected. This is required because conversion to AAC adds a tiny amount of time
    :param expected:
    :param actual:
    :return:
    """
    min = expected
    max = expected * 1.02
    if not (min <= actual <= max):
        raise AssertionError("{} != {} ({}-{})".format(expected, actual, min, max))
