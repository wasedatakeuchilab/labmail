# Labmail <!-- omit in toc -->

<p align="center">
<a href="https://github.com/wasedatakeuchilab/labmail/actions?query=workflow%3ATest" target="_blank">
  <img src="https://github.com/wasedatakeuchilab/labmail/workflows/Test/badge.svg" alt="Test">
</a>
<a href="https://codecov.io/gh/wasedatakeuchilab/labmail" >
  <img src="https://codecov.io/gh/wasedatakeuchilab/labmail/graph/badge.svg?token=tkOaTJOYOR" alt="Coverage"/>
</a>
</p>

_Labmail_ is a command line tool that sends a message **with your signature** via Gmail.

You can easily automate your daily tasks of sending messages such as:

- sending a weekly report at a certain time in the week
- notifying the lab members of some events
- monitoring the state of computers

_Labmail_ also provides helpful APIs to interact with Gmail API.
If you want to create your own scripts that calls Gmail API, you can use _Labmail_ as a Python library.

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Options](#options)
    - [Set subject](#set-subject)
    - [Add headers](#add-headers)
    - [Specify text type](#specify-text-type)
    - [Take a dry run](#take-a-dry-run)
  - [Show help](#show-help)
- [API](#api)
  - [gmail\_api](#gmail_api)
- [License](#license)

## Requirements

- Python 3.10 or above
- Waseda email address (that ends with `.waseda.jp`)

## Installation

You can install it with `pip` + `git`.

```console
$ pip install git+https://github.com/wasedatakeuchilab/labmail
```

We also provide the Docker image.

```console
$ docker pull ghcr.io/wasedatakeuchilab/labmail
```

## Usage

The simplest way is to input body of the message from `stdin`.

```console
$ labmail foo@example.com << EOF
Hello!
I'm Taro Waseda.

Have a nice weekend!
EOF
```

If you run `labmail` for the first time, you will be asked whether you authorize the app by Google.

> Note: The authorization flow will fail if your Google account is not Waseda one.

You can also input body from a file.

```console
$ cat - << EOF > body.txt
Hello!
I'm Taro Waseda.

Have a nice weekend!
EOF
$ labmail foo@example.com body.txt
```

> Note: HTML(`.html`) and Markdown(`.md`) files are also supported as an input file. See also [here](#specify-text-type)

If you want to send the message to two or more recipients, seperate email addresses with comma.

```console
$ labmail foo@example.com,bar@example.com body.txt
```

### Options

#### Set subject

You can set the subject to the message with `-s` option.

```console
$ echo "Hello" | labmail foo@example.com -s "Greeting"
```

#### Add headers

You can add any header to the message with `-a` option (can be used multiple times).

```console
$ echo "Hello" | labmail foo@example.com -a "CC: bar@example.com"
```

#### Specify text type

_Labmail_ supports the following text type for the body text.
By default, _Labmail_ specify it automatically according to the filename.

- plain text
- HTML text
- Markdown text

If you want to specify the text type explicitly, use `-t` option.

```console
$ cat - << EOF > body.md
Hello!
I'm Taro Waseda.

I like **fruits**.

- Apple
- Banana
- Orange
EOF
$ labmail foo@example.com body.md -t markdown
```

#### Take a dry run

If you just want to check the content of the message without sending it, add `--dry-run` and `-vv` options.

```console
$ echo "Hello" | labmail foo@example.com --dry-run -vv
# Logging messages will be shown here
```

### Show help

Run `labmail --help` for help.

```console
$ labmail --help
Usage: labmail [OPTIONS] ADDRESS [FILE]

    _          _                     _ _
   | |    __ _| |__  _ __ ___   __ _(_) |
   | |   / _` | '_ \| '_ ` _ \ / _` | | |
   | |__| (_| | |_) | | | | | | (_| | | |
   |_____\__,_|_.__/|_| |_| |_|\__,_|_|_|

  Send a message of FILE with signature via Gmail to ADDRESS.

  ADDRESS     Email addresses(seperated with comma) of recipients
  FILE        Filepath or stdin(default) for the message to send

Options:
  -s, --subject TEXT              Subject of the message
  -a, --append NAME: VALUE        Append a header to the message
  -t, --text-type [auto|plain|html|markdown]
                                  Text type of the body  [default: auto]
  --disallow-same-subjects        Exit without sending the message if the
                                  subject has been already used
  --sendas ADDRESS                Address of the signature
  --dry-run                       Run the program without sending message
  -c, --creds FILE                Path to credentials for Gmail API
  -v, --verbose                   Increase verbosity (can be used additively)
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

## API

`labmail.send()` sends a message with signature via Gmail.
The simplest usage is:

```python
>>> import labmail
>>> labmail.send("foo@example.com", "Body text here", "Subject here")
```

### gmail_api

`gmail_api` module allows to interact with Gmail API.

```python
>>> from labmail import gmail_api
# Build a GmailResource instance first
>>> with gmail_api.credentials() as creds:
...   rsc = gmail_api.build(creds)

# List messages in the mailbox
>>> gmail_api.list_message(rsc, max_results=1)
([{'id': '000000000000001', 'threadId': 'aaabbbcccdddeee'}], '192837465', 100)

# Get the detail of the message
>>> msg = gmail_api.get_message(rsc, id="000000000000001")
>>> msg["payload"]["mimeType"]
'text/html'
```

Available APIs

- build(): Constructs a new GmailResource object to request to Gmail API.
- list_message(): Gets a list of messages in the user's mailbox of Gmail.
- get_message(): Gets a message in the mailbox of Gmail.
- send_message(): Sends a message via Gmail.
- and others

## License

[MIT License](./LICENSE)

Copyright (c) 2023 Shuhei Nitta
