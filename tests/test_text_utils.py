import pathlib

import pytest

from labmail import text_utils
from tests import get_testcase_dir

TESTCASE_DIR = get_testcase_dir(__file__)


@pytest.mark.parametrize("filename", ["foo.txt", "bar.csv", "stdin"])
def test_determine_text_type_plain(filename: str) -> None:
    assert text_utils.determine_text_type(filename) is text_utils.TextType.PLAIN


@pytest.mark.parametrize("filename", ["foo.html", "bar.htm"])
def test_determine_text_type_html(filename: str) -> None:
    assert text_utils.determine_text_type(filename) is text_utils.TextType.HTML


@pytest.mark.parametrize("filename", ["foo.md", "bar.md"])
def test_determine_text_type_markdown(filename: str) -> None:
    assert text_utils.determine_text_type(filename) is text_utils.TextType.MARKDOWN


def _list_testcases(pattern: str) -> list[pathlib.Path]:
    return list(TESTCASE_DIR.glob(pattern))


def _save_result(filepath: pathlib.Path, html_text: str) -> None:
    resultdir = filepath.parent / "results"
    resultdir.mkdir(exist_ok=True)
    gitignore = resultdir / ".gitignore"
    if not gitignore.exists():
        with open(gitignore, "w") as f:
            f.write("# Created by pytest automatically.\n*\n")
    with open(resultdir / (filepath.name + ".html"), "w") as f:
        f.write(html_text)


@pytest.mark.parametrize(
    "filepath", _list_testcases(text_utils.convert_text_to_html.__name__ + "/*.txt")
)
def test_convert_text_to_html_plain(filepath: pathlib.Path) -> None:
    with open(filepath, "r") as f:
        text = f.read()
    html_text = text_utils.convert_text_to_html(text, text_utils.TextType.PLAIN)
    assert html_text != ""
    _save_result(filepath, html_text)


@pytest.mark.parametrize(
    "filepath", _list_testcases(text_utils.convert_text_to_html.__name__ + "/*.html")
)
def test_convert_text_to_html_html(filepath: pathlib.Path) -> None:
    with open(filepath, "r") as f:
        text = f.read()
    html_text = text_utils.convert_text_to_html(text, text_utils.TextType.HTML)
    assert html_text != ""
    _save_result(filepath, html_text)


@pytest.mark.parametrize(
    "filepath", _list_testcases(text_utils.convert_text_to_html.__name__ + "/*.md")
)
def test_convert_text_to_html_markdown(filepath: pathlib.Path) -> None:
    with open(filepath, "r") as f:
        text = f.read()
    html_text = text_utils.convert_text_to_html(text, text_utils.TextType.MARKDOWN)
    assert html_text != ""
    _save_result(filepath, html_text)
