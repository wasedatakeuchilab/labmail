import pathlib
import typing as t

import pytest

PT = t.TypeVar("PT")


class FixtureRequest(pytest.FixtureRequest, t.Generic[PT]):
    param: PT


def get_testcase_dir(__file__: str) -> pathlib.Path:
    return pathlib.Path(__file__.replace("test_", "testcases/")).with_suffix("")
