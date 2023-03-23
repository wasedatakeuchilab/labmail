import os
import pathlib

import pytest
import pytest_mock

from tests import FixtureRequest


@pytest.fixture(params=["str", "Path"])
def filepath(
    request: FixtureRequest[str], filename: str, tmpdir: str
) -> str | os.PathLike[str]:
    match request.param:
        case "str":
            return os.path.join(tmpdir, str(filename))
        case "Path":
            return pathlib.Path(tmpdir) / filename
        case _:
            raise NotImplementedError


@pytest.fixture(autouse=True)
def mock_google_resource(mocker: pytest_mock.MockerFixture) -> None:
    """
    This fixture is aimed to prevent developers from requesting Google API by mistake.
    """
    mocker.patch("googleapiclient.discovery.build")
