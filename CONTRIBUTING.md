# Contributing

---

## Code Formatting

Please make sure to format your code following [PEP8](https://www.python.org/dev/peps/pep-0008/) and
[PEP257](https://www.python.org/dev/peps/pep-0257/).

### Configuration files

We provide a configuration file for `flake8` in the root of the repository: `tox.ini` with some shared formatting rules,
see [flake8 configuration](https://flake8.pycqa.org/en/latest/user/configuration.html)
and this [guide](https://www.jetbrains.com/help/pycharm/tox-support.html) for PyCharm users for details.

### Pre-commit hook

Consider installing the pre-commit hook as described in the README.md.

### Formatting tools

Before committing or pushing code to the remote, be sure to run:
`mypy --strict --package flex_package`
