from __future__ import annotations

import base64
import contextlib
import email.mime.base as mime_base
import os
import pathlib
import typing as t
from collections import abc

from google.auth.transport import requests
from google.oauth2 import credentials as _credentials
from google_auth_oauthlib import flow
from googleapiclient import discovery

from labmail import _env

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.gmail.v1 import resources, schemas


def get_default_config() -> dict[str, t.Any]:
    """
    Gets the default config of Google OAuth flow.

    Returns
    -------
    dict[str, typing.Any]
        The default config.
    """
    return {
        "installed": {
            "client_id": "416316022973-k055mip7ifo52nrdkie3afrlao0cente.apps.googleusercontent.com",
            "client_secret": "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",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_default_scopes() -> list[str]:
    """
    Gets the default scopes of Google API.

    Returns
    -------
    list[str]
        The list of scopes.
    """
    return [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]


def new_credentials(
    client_config: dict[str, t.Any] | None = None,
    scopes: list[str] | None = None,
) -> _credentials.Credentials:
    """
    Creates a new Credentials object for Google API.

    Parameters
    ----------
    client_config : dict[str, typing.Any]
        The client configuration in the Google client_secrets format.
        If None, the default client configuration will be used.
    scopes : list[str]
        The list of scopes to request during the flow.
        If None, the default scopes will be used.

    Returns
    -------
    google.oauth2.credentials.Credentials
        A new OAuth 2.0 credentials.
    """
    if client_config is None:
        client_config = get_default_config()
    if scopes is None:
        scopes = get_default_scopes()
    app_flow = flow.InstalledAppFlow.from_client_config(client_config, scopes)
    creds = app_flow.run_local_server(
        host=_env.GOOGLE_OAUTH_FLOW_HOST,
        bind_addr=_env.GOOGLE_OAUTH_FLOW_BIND,
        port=_env.GOOGLE_OAUTH_FLOW_PORT,
    )
    return creds


def load_credentials(
    filepath: str | os.PathLike[str], scopes: list[str] | None = None
) -> _credentials.Credentials:
    """
    Creates a Credentials object for Google API from an authorized user json file.

    Parameters
    ----------
    filepath : str | os.PathLike[str]
        The path to the authorized user json file.
    scopes : list[str] | None
        The list of scopes to include in the credentials.

    Returns
    -------
    google.oauth2.credentials.Credentials
        The constructed OAuth 2.0 credentials.

    Raises
    ------
    ValueError
        If the constructed credentials is invalid.
    """
    creds = _credentials.Credentials.from_authorized_user_file(filepath, scopes)
    if not creds.valid:
        if creds.refresh_token:
            creds.refresh(requests.Request())
        else:
            raise ValueError("The credentials is not valid and has no refresh token")
    return creds


def save_credentials(
    creds: _credentials.Credentials, filepath: str | os.PathLike[str]
) -> None:
    """
    Saves the Credentials object to the file.

    Parameters
    ----------
    creds : google.oauth2.credentials.Credentials
        The credentials to save.
    filepath : str | os.PathLike[str]
        The path to save the credentials.
    """
    filepath = pathlib.Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w") as f:
        f.write(creds.to_json())


@contextlib.contextmanager
def credentials(
    filepath: str | os.PathLike[str] = "credentials.json",
    scopes: list[str] | None = None,
) -> abc.Iterator[_credentials.Credentials]:
    """
    Loads or creates a Credentials object for this library
    to request to Gmail API, and saves it to `filepath`.

    Parameters
    ----------
    filepath : str | os.PathLike[str]
        The path to the authorized user json file.
    scopes : list[str] | None
        The list of scopes for the credentials.

    Yeilds
    ------
    google.oauth2.credentials.Credentials
        The Credentials object for interacting with Gmail API.

    Examples
    --------
    >>> with credentials() as creds:
    ...     rsc = build(creds)

    The credentials will be saved to `filepath` when exiting the `with` context.

    Notes
    -----
    The credentials won't be saved if any exception happens in the `with` context.
    """
    try:
        creds = load_credentials(filepath, scopes)
    except (ValueError, FileNotFoundError):
        creds = new_credentials(scopes=scopes)
    yield creds
    save_credentials(creds, filepath)


def build(creds: _credentials.Credentials) -> resources.GmailResource:
    """
    Constructs a new GmailResource object to request to Gmail API.

    Parameters
    ----------
    creds : google.oauth2.credentials.Credentials
        The credentials for Gmail API.

    Returns
    -------
    GmailResource
        The Resource object for interacting with Gmail API.
    """
    return discovery.build(serviceName="gmail", version="v1", credentials=creds)


def list_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    query: str = "",
    max_results: int = 100,
    page_token: str | None = None,
    label_ids: list[str] | None = None,
    include_spam_trash: bool = False,
) -> tuple[list[schemas.Message], str, int]:
    """
    Gets a list of messages in the user's mailbox of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    query : str
        The same query format as that of the Gmail search box.
    max_results : int
        The maximum number of messages to return.
    page_token : str | None
        The page token to retrieve a specific page of results in the list.
    label_ids : list[str] | None
        The list of label IDs of messages to retrieve.
    include_spam_trash : bool
        If true, messages from SPAM and TRASH are included in the results.

    Returns
    -------
    messages : list[Message]
        A list of Message objects.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.
    next_page_token : str
        The token to retrieve the next page.
    result_size_estimate : int
        The estimated total number of results.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
    """
    response = (
        rsc.users()
        .messages()
        .list(
            userId=user_id,
            q=query,
            maxResults=max_results,
            pageToken=page_token or "",
            labelIds=label_ids or [],
            includeSpamTrash=include_spam_trash,
        )
        .execute()
    )
    return (
        response.get("messages", list()),
        response.get("nextPageToken", ""),
        response.get("resultSizeEstimate", 0),
    )


def get_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    id: str,
    format: t.Literal["minimal", "full", "raw", "metadata"] = "full",
) -> schemas.Message:
    """
    Gets a message in the mailbox of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    id : str
        The ID of the message to retrieve.
    format : Literal["minimal", "full", "raw", "metadata"]
        The format to return the message in.
        See also https://developers.google.com/gmail/api/reference/rest/v1/Format.

    Returns
    -------
    Message
        The retrieved Message object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get
    """
    response = (
        rsc.users().messages().get(userId=user_id, id=id, format=format).execute()
    )
    return response


def send_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    message: mime_base.MIMEBase,
) -> schemas.Message:
    """
    Sends a message via Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    message : email.mime.base.MIMEBase
        The message to send.

    Returns
    -------
    Message
        The sent Message object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send
    """
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    response = (
        rsc.users().messages().send(userId=user_id, body={"raw": raw_message}).execute()
    )
    return response


def get_sendas(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    address: str | None = None,
) -> schemas.SendAs:
    """
    Gets a sendas registered on Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    address : str | None
        The send-as alias address to be retrieved.
        If None, the default send-as alias is retrieved.

    Returns
    -------
    SendAs
        The retrieved SendAs object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.settings.sendAs#SendAs.

    Raises
    ------
    ValueError
        If any sendas for the address is not found.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.settings.sendAs/list
    """
    response = (
        rsc.users()
        .settings()
        .sendAs()
        .list(
            userId=user_id,
        )
        .execute()
    )
    addr_to_sendas = {sendas["sendAsEmail"]: sendas for sendas in response["sendAs"]}
    if address is None:
        # Get the default send-as alias
        sendas = [
            sendas for sendas in addr_to_sendas.values() if sendas["isDefault"]
        ].pop()
    else:
        if address not in addr_to_sendas.keys():
            raise ValueError(f"Signatures of {address} not found")
        sendas = addr_to_sendas[address]
    return sendas
