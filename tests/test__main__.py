import itertools
import os

import pytest
import pytest_mock
from click import exceptions, testing

from labmail import SubjectUsedError, __main__, text_utils


def test_main_success(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("labmail.send")
    runner = testing.CliRunner()
    result = runner.invoke(__main__.main, ["foo@example.com"], input="")
    assert result.exit_code == 0


@pytest.mark.parametrize("exception", [ValueError(), SubjectUsedError()])
def test_main_fail(exception: Exception, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("labmail.send", side_effect=exception)
    runner = testing.CliRunner()
    result = runner.invoke(__main__.main, ["foo@example.com"], input="")
    assert result.exit_code == exceptions.ClickException.exit_code


def test_main_no_recipients(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("labmail.send")
    runner = testing.CliRunner()
    result = runner.invoke(__main__.main, [""], input="")
    assert result.exit_code == exceptions.BadArgumentUsage.exit_code


@pytest.mark.parametrize(
    "address", ["foo@example.com", "foo@example.com,bar@abc.example.com"]
)
@pytest.mark.parametrize("filename", ["-", "test.txt"])
@pytest.mark.parametrize("subject", ["", "Test"])
@pytest.mark.parametrize(
    "headers",
    [
        tuple(),
        ("CC: hoge@example.com",),
        ("CC: hoge@example.com", "BCC: fuga@example.com"),
    ],
)
@pytest.mark.parametrize("text_type", list(text_utils.TextType))
@pytest.mark.parametrize("disallow_same_subjects", [True, False])
@pytest.mark.parametrize("sendas_address", [None, "foo@example.com"])
@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize(
    "credentials_filepath", ["credentials.json", "/tmp/gmail_credentials.json"]
)
def test_main_options(
    address: str,
    filename: str,
    subject: str,
    headers: tuple[str],
    text_type: text_utils.TextType,
    disallow_same_subjects: bool,
    sendas_address: str | None,
    dry_run: bool,
    credentials_filepath: str,
    tmpdir: str,
    mocker: pytest_mock.MockerFixture,
) -> None:
    body = "This is a test message."
    if filename != "-":
        filename = os.path.join(tmpdir, filename)
        with open(filename, "w") as f:
            f.write(body)
    args = [
        address,
        filename,
        "-s",
        subject,
        "-t",
        text_type.value,
        "-c",
        credentials_filepath,
    ]
    args.extend(
        itertools.chain.from_iterable(
            zip(itertools.repeat("-a", len(headers)), headers)
        )
    )
    if disallow_same_subjects:
        args.append("--disallow-same-subjects")
    if sendas_address:
        args.extend(["--sendas", sendas_address])
    if dry_run:
        args.append("--dry-run")
    send_mock = mocker.patch("labmail.send")
    runner = testing.CliRunner()
    result = runner.invoke(__main__.main, args, input=body if filename == "-" else None)
    assert result.exit_code == 0
    send_mock.assert_called_once_with(
        recipient=address,
        body=body,
        text_type=text_type,
        subject=subject,
        headers=dict(header.split(": ") for header in headers),
        disallow_same_subjects=disallow_same_subjects,
        sendas_address=sendas_address,
        dry_run=dry_run,
        credentials_filepath=credentials_filepath,
    )
