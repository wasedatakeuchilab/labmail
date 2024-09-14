from __future__ import annotations

import base64
import email.mime.text as mime_text
import os
import typing as t

import pytest
import pytest_mock

from labmail import gmail_api
from tests import FixtureRequest

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.gmail.v1 import schemas


def test_get_default_scopes() -> None:
    assert gmail_api.get_default_scopes() == [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]


@pytest.fixture(
    params=[None, [], gmail_api.get_default_scopes()],
    ids=["none", "empty", "default"],
)
def scopes(request: FixtureRequest[list[str] | None]) -> list[str] | None:
    return request.param


@pytest.mark.parametrize(
    "client_config",
    [None, {}, gmail_api.get_default_config()],
    ids=["none", "empty", "default"],
)
def test_new_credentials(
    client_config: dict[str, t.Any],
    scopes: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mock = mocker.patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_config")
    creds = gmail_api.new_credentials(client_config, scopes)
    assert creds == mock.return_value.run_local_server.return_value
    if client_config is None:
        client_config = gmail_api.get_default_config()
    if scopes is None:
        scopes = gmail_api.get_default_scopes()
    mock.assert_called_once_with(client_config, scopes)


@pytest.mark.parametrize("filename", ["test_load_credentials.json"])
def test_load_credentials(
    filepath: str | os.PathLike[str],
    scopes: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mock = mocker.patch(
        "google.oauth2.credentials.Credentials.from_authorized_user_file",
        return_value=mocker.Mock(valid=True, refresh_token=None),
    )
    creds = gmail_api.load_credentials(filepath, scopes=scopes)
    assert creds == mock.return_value
    mock.assert_called_once_with(filepath, scopes)
    mock.return_value.refresh.assert_not_called()


@pytest.mark.parametrize("filename", ["test_load_credentials.json"])
def test_load_credentials_invalid_refreshable(
    filepath: str | os.PathLike[str],
    scopes: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mock = mocker.patch(
        "google.oauth2.credentials.Credentials.from_authorized_user_file",
        return_value=mocker.Mock(valid=False, refresh_token="refresh_token"),
    )
    creds = gmail_api.load_credentials(filepath, scopes=scopes)
    assert creds == mock.return_value
    mock.assert_called_once_with(filepath, scopes)
    mock.return_value.refresh.assert_called_once()


@pytest.mark.parametrize("filename", ["test_load_credentials.json"])
def test_load_credentials_invalid_unrefreshable(
    filepath: str | os.PathLike[str],
    scopes: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mock = mocker.patch(
        "google.oauth2.credentials.Credentials.from_authorized_user_file",
        return_value=mocker.Mock(valid=False, refresh_token=None),
    )
    with pytest.raises(ValueError):
        gmail_api.load_credentials(filepath, scopes=scopes)
    mock.assert_called_once_with(filepath, scopes)
    mock.return_value.refresh.assert_not_called()


@pytest.mark.parametrize("filename", ["test_save_credentials.json"])
def test_save_credentials(
    filepath: str | os.PathLike[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    creds_mock = mocker.Mock(to_json=mocker.Mock(return_value="{}"))
    gmail_api.save_credentials(creds_mock, filepath)
    creds_mock.to_json.assert_called_once_with()
    with open(filepath) as f:
        assert f.read() == creds_mock.to_json.return_value


@pytest.mark.parametrize("filename", ["test_credentials.json"])
def test_credentials(
    filepath: str | os.PathLike[str],
    scopes: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    creds_mock = mocker.Mock(to_json=mocker.Mock(return_value="{}"))
    load_mock = mocker.patch(
        "labmail.gmail_api.load_credentials", side_effect=ValueError
    )
    new_mock = mocker.patch(
        "labmail.gmail_api.new_credentials", return_value=creds_mock
    )
    save_mock = mocker.patch("labmail.gmail_api.save_credentials")
    with gmail_api.credentials(filepath, scopes) as creds:
        assert creds == creds_mock
        load_mock.assert_called_once_with(filepath, scopes)
        new_mock.assert_called_once_with(scopes=scopes)
        save_mock.assert_not_called()
    save_mock.assert_called_once_with(creds_mock, filepath)


def test_build(mocker: pytest_mock.MockerFixture) -> None:
    build_mock = mocker.patch("googleapiclient.discovery.build")
    creds_mock = mocker.Mock()
    rsc = gmail_api.build(creds_mock)
    assert rsc == build_mock.return_value
    build_mock.assert_called_once_with(
        serviceName="gmail",
        version="v1",
        credentials=creds_mock,
    )


@pytest.mark.parametrize("messages", [[{}], [], None])
@pytest.mark.parametrize("next_page_token", ["page_token", None])
@pytest.mark.parametrize("result_size_estimate", [0, 100, None])
def test_list_message_returns(
    messages: list[schemas.Message] | None,
    next_page_token: str | None,
    result_size_estimate: int,
    mocker: pytest_mock.MockerFixture,
) -> None:
    response: schemas.ListMessagesResponse = dict()
    if messages is not None:
        response["messages"] = messages
    if next_page_token is not None:
        response["nextPageToken"] = next_page_token
    if result_size_estimate is not None:
        response["resultSizeEstimate"] = result_size_estimate
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().messages().list
    list_mock.return_value.execute.return_value = response
    result = gmail_api.list_message(rsc_mock)
    assert result[0] == response.get("messages", list())
    assert result[1] == response.get("nextPageToken", "")
    assert result[2] == response.get("resultSizeEstimate", 0)


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("query", ["", "query"])
@pytest.mark.parametrize("max_results", [100, 200])
@pytest.mark.parametrize("page_token", [None, "page_token"])
@pytest.mark.parametrize("label_ids", [None, ["label"]])
@pytest.mark.parametrize("include_spam_trash", [True, False])
def test_list_message_api_call(
    user_id: str,
    query: str,
    max_results: int,
    page_token: str | None,
    label_ids: list[str] | None,
    include_spam_trash: bool,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail_api.list_message(
        rsc_mock,
        user_id,
        query=query,
        max_results=max_results,
        page_token=page_token,
        label_ids=label_ids,
        include_spam_trash=include_spam_trash,
    )
    list_mock = rsc_mock.users().messages().list
    list_mock.assert_called_once_with(
        userId=user_id,
        q=query,
        maxResults=max_results,
        pageToken=page_token or "",
        labelIds=label_ids or [],
        includeSpamTrash=include_spam_trash,
    )
    list_mock.return_value.execute.assert_called_once_with()


@pytest.mark.parametrize("message", [{}])
def test_get_message_returns(
    message: schemas.Message,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    get_mock = rsc_mock.users().messages().get
    get_mock.return_value.execute.return_value = message
    assert gmail_api.get_message(rsc_mock, id="id") == message


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("id", ["foo", "bar"])
@pytest.mark.parametrize("format", ["minimal", "full", "raw", "metadata"])
def test_get_message_api_call(
    user_id: str,
    id: str,
    format: t.Literal["minimal", "full", "raw", "metadata"],
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail_api.get_message(rsc_mock, user_id, id=id, format=format)
    get_mock = rsc_mock.users().messages().get
    get_mock.assert_called_once_with(userId=user_id, id=id, format=format)
    get_mock.return_value.execute_assert_called_once_with()


@pytest.mark.parametrize("message", [{}])
def test_send_message_returns(
    message: schemas.Message,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    send_mock = rsc_mock.users().messages().send
    send_mock.return_value.execute.return_value = message
    assert gmail_api.send_message(rsc_mock, message=mime_text.MIMEText("")) == message


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("body", ["", "This is a mail test."])
def test_send_message_api_call(
    user_id: str,
    body: str,
    mocker: pytest_mock.MockerFixture,
) -> None:
    message = mime_text.MIMEText(body)
    rsc_mock = mocker.Mock()
    gmail_api.send_message(rsc_mock, user_id, message=message)
    send_mock = rsc_mock.users().messages().send
    send_mock.assert_called_once_with(
        userId=user_id,
        body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()},
    )
    send_mock.return_value.execute.assert_called_once_with()


@pytest.fixture()
def sendas_list() -> list[schemas.SendAs]:
    default_sendas: schemas.SendAs = {
        "sendAsEmail": "default@example.com",
        "displayName": "dafault user",
        "signature": "default user",
        "isDefault": True,
    }
    sendas_list = [default_sendas] + [
        {
            "sendAsEmail": f"foo{i}@example.com",
            "displayName": "foo",
            "signature": f"foo{i} bar",
            "isDefault": False,
        }
        for i in range(3)
    ]
    return sendas_list


def test_get_sendas_returns(
    sendas_list: list[schemas.SendAs],
    mocker: pytest_mock.MockerFixture,
) -> None:
    default_sendas = [sendas for sendas in sendas_list if sendas["isDefault"]].pop()
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().settings().sendAs().list
    list_mock.return_value.execute.return_value = {"sendAs": sendas_list}
    sendas = gmail_api.get_sendas(rsc_mock)
    assert sendas == default_sendas


@pytest.mark.parametrize("idx", list(range(3)))
def test_get_signature_returns_address(
    idx: int,
    sendas_list: list[schemas.SendAs],
    mocker: pytest_mock.MockerFixture,
) -> None:
    sendas = sendas_list[idx]
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().settings().sendAs().list
    list_mock.return_value.execute.return_value = {"sendAs": sendas_list}
    assert gmail_api.get_sendas(rsc_mock, address=sendas["sendAsEmail"]) == sendas


def test_get_signature_address_not_found(
    sendas_list: list[schemas.SendAs],
    mocker: pytest_mock.MockerFixture,
) -> None:
    address_list = [sendas["sendAsEmail"] for sendas in sendas_list]
    address = "unexist_in_address_list@example.com"
    assert address not in address_list
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().settings().sendAs().list
    list_mock.return_value.execute.return_value = {"sendAs": sendas_list}
    with pytest.raises(ValueError):
        gmail_api.get_sendas(rsc_mock, address=address)


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("address", [None, "default@example.com"])
def test_get_sendas_api_call(
    user_id: str,
    address: str | None,
    sendas_list: list[dict[str, t.Any]],
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().settings().sendAs().list
    list_mock.return_value.execute.return_value = {"sendAs": sendas_list}
    gmail_api.get_sendas(rsc_mock, user_id, address=address)
    list_mock.assert_called_once_with(userId=user_id)
    list_mock.return_value.execute.assert_called_once_with()
