__version__ = "0.0.7"

import email.mime.text as mime_text
import logging
import os
import pprint

from . import gmail_api, text_utils
from .text_utils import TextType

logger = logging.getLogger(__name__)


def send(
    recipient: str | list[str],
    body: str = "",
    subject: str = "",
    *,
    text_type: TextType = TextType.PLAIN,
    headers: dict[str, str] | None = None,
    disallow_same_subjects: bool = False,
    sendas_address: str | None = None,
    dry_run: bool = False,
    credentials_filepath: str | os.PathLike[str] = "credentials.json",
) -> None:
    """
    Sends a message via Gmail.

    Parameters
    ----------
    recipient : str | list[str]
        The email address(es) of recipient.
    subject : str
        The subject of the message.
    body : str
        The body text of the message.
    text_type : labmail.TextType
        The text type of the body.
    headers : dict[str, str] | None
        The headers to be appended to the message such as CC or BCC.
    disallow_same_subjects : bool
        If true and the subject has been alreay used, raises SubjectAlreadyUsedError.
    sendas_address : str | None
        The address for the signature.
        If None, the default signature will be used.
    dry_run : bool
        If true, does not post the send request to Gmail API.
    credentials_filepath : str | os.PathLike[str]
        The path to the authorized user json file.

    Raises
    ------
    labmail.SubjectUsedError
        If the subject has been already used to send the message.

    Examples
    --------
    >>> import labmail
    >>> labmail.send("foo@example.com", "Body text here", "Subject here")
    """
    logger.info("Building a Gmail Resource object")
    with gmail_api.credentials(credentials_filepath) as creds:
        rsc = gmail_api.build(creds)
    logger.info("Successfully built the Gmail Resource")

    if disallow_same_subjects:
        logger.info("Checking whether the subject has been already used")
        _, _, size = gmail_api.list_message(rsc, query=f'in:sent subject:("{subject}")')
        if size > 0:
            raise SubjectUsedError(f"The subject has been already used: {subject}")
        logger.info("The subject is not used yet")

    logger.info("Retrieving the default sendas from Gmail")
    sendas = gmail_api.get_sendas(rsc, address=sendas_address)
    logger.info(f"Successfully retrieved the sendas of {sendas['sendAsEmail']}")
    logger.debug("The retrieved sendas is...\n" + pprint.pformat(sendas))

    logger.info("Building the HTML body")
    html_body = (
        text_utils.convert_text_to_html(body, text_type)
        + "<div>--</div>"
        + sendas["signature"]
    )
    logger.info("Successfully built the HTML body")
    logger.debug("The HTML body is...\n" + html_body)

    logger.info("Building the HTML message")
    message = mime_text.MIMEText(html_body, "html")
    message["subject"] = subject
    message["to"] = recipient if isinstance(recipient, str) else ",".join(recipient)
    for name, value in (headers or dict()).items():
        message.add_header(name, value)
    logger.info("Successfully built the HTML message")
    logger.debug("The message is...\n" + message.as_string())

    logger.info("Sending the message")
    if dry_run:
        logger.info("The message is not sent for dry-run mode")
    else:
        gmail_api.send_message(rsc, message=message)
        logger.info("Successfully sent the message")


class SubjectUsedError(ValueError):
    """If the subject has already been used."""
