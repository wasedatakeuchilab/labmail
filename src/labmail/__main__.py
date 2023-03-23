from __future__ import annotations

import logging
import pathlib
import pprint
import typing as t

import click

import labmail
from labmail import text_utils

logger = logging.getLogger(__name__)

APPNAME = pathlib.Path(__file__).parent.name
APPDIR = pathlib.Path(click.get_app_dir(APPNAME, roaming=False))
CREDENTIALS_FILEPATH = APPDIR / "credentials.json"


@click.command(
    help="""\b
  _          _                     _ _
 | |    __ _| |__  _ __ ___   __ _(_) |
 | |   / _` | '_ \\| '_ ` _ \\ / _` | | |
 | |__| (_| | |_) | | | | | | (_| | | |
 |_____\\__,_|_.__/|_| |_| |_|\\__,_|_|_|

Send a message of FILE with signature via Gmail to ADDRESS.

\b
ADDRESS     Email addresses(seperated with comma) of recipients
FILE        Filepath or stdin(default) for the message to send
"""
)
@click.argument("address", type=str)
@click.argument("file", type=click.File("r"), default="-")
@click.option(
    "-s",
    "--subject",
    type=str,
    default="",
    help="Subject of the message",
    show_default=True,
)
@click.option(
    "-a",
    "--append",
    "headers",
    type=str,
    multiple=True,
    metavar="NAME: VALUE",
    help="Append a header to the message",
)
@click.option(
    "-t",
    "--text-type",
    type=click.Choice(
        ["auto"] + [text_type.value for text_type in text_utils.TextType]
    ),
    default="auto",
    callback=lambda ctx, _, value: text_utils.determine_text_type(
        ctx.params["file"].name
    )
    if value == "auto"
    else text_utils.TextType(value),
    help="Text type of the body",
    show_default=True,
)
@click.option(
    "--disallow-same-subjects",
    is_flag=True,
    default=False,
    help="Exit without sending the message if the subject has been already used",
)
@click.option(
    "--sendas",
    "sendas_address",
    type=str,
    metavar="ADDRESS",
    help="Address of the signature",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run the program without sending message",
)
@click.option(
    "-c",
    "--creds",
    "credentials_filepath",
    type=click.Path(dir_okay=False),
    default=str(CREDENTIALS_FILEPATH),
    help="Path to credentials for Gmail API",
    show_default=True,
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="Increase verbosity (can be used additively)",
)
@click.version_option()
def main(
    address: str,
    file: t.IO[str],
    subject: str,
    headers: tuple[str],
    text_type: text_utils.TextType,
    disallow_same_subjects: bool,
    sendas_address: str | None,
    dry_run: bool,
    credentials_filepath: str,
    verbose: int,
) -> None:
    logging.basicConfig(
        format="%(levelname)-8s: %(message)s",
        level=40 - 20 * verbose,
    )
    logger.debug("The given parameters are:\n" + pprint.pformat(locals()))

    if not address:
        raise click.BadArgumentUsage("ADDRESS must not be an empty string")
    try:
        labmail.send(
            recipient=address,
            body=file.read(),
            subject=subject,
            headers=dict(header.split(": ") for header in headers),
            text_type=text_type,
            disallow_same_subjects=disallow_same_subjects,
            sendas_address=sendas_address,
            dry_run=dry_run,
            credentials_filepath=credentials_filepath,
        )
    except labmail.SubjectUsedError as err:
        raise click.ClickException(str(err))
    except Exception as err:
        raise click.ClickException(f"Internal Error: {err}")


if __name__ == "__main__":  # pragma: no cover
    main()
