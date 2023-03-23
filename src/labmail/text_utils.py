import enum

import markdown


class TextType(enum.Enum):
    PLAIN = "plain"
    HTML = "html"
    MARKDOWN = "markdown"


def determine_text_type(filename: str) -> TextType:
    """
    Determines the text type of the filename.

    Parameters
    ----------
    filename : str
        The filename to determine the text type from.

    Returns
    -------
    labmail.text_utils.TextType
        The determined text type.
    """
    if filename.endswith((".htm", ".html")):
        return TextType.HTML
    elif filename.endswith(".md"):
        return TextType.MARKDOWN
    else:
        return TextType.PLAIN


def convert_text_to_html(text: str, text_type: TextType) -> str:
    """
    Converts any text to HTML.

    Parameters
    ----------
    text : str
        The text to convert.
    text_type : TextType
        The text type of the text.

    Returns
    -------
    str
        The converted HTML text.
    """
    match text_type:
        case TextType.PLAIN:
            return (
                "<p>"
                + "".join(
                    [
                        f"{line}<br>" if line.strip() != "" else "</p><p>"
                        for line in text.splitlines()
                    ]
                )
                + "</p>"
            )
        case TextType.HTML:
            return text
        case TextType.MARKDOWN:
            return markdown.markdown(text)
        case _:  # pragma: no cover
            raise NotImplementedError(
                f"The code for {text_type} is not implemented yet."
            )
