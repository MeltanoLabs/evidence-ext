# evidence-ext

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MeltanoLabs/evidence-ext/main.svg)](https://results.pre-commit.ci/latest/github/MeltanoLabs/evidence-ext/main)

`evidence-ext` is A Meltano utility extension for [Evidence.dev](https://evidence.dev) 📊

## Testing with Meltano

This extension includes a sample Evidence project, along with a `meltano.yml` project file, allowing you to test Evidence with Meltano.

```shell
# install the Meltano project locally
meltano install
# run evidence in dev mode
meltano invoke evidence dev
# build the example evidence project
meltano invoke evidence build
```

## Installing this extension for local development

1. Install the project dependencies with `poetry install`:

```shell
cd path/to/your/project
poetry install
```

2. Verify that you can invoke the extension:

```shell
poetry run evidence_extension --help
poetry run evidence_extension describe --format=yaml
poetry run evidence_invoker --help # if you have are wrapping another tool
```

## Template updates

This project was generated with [copier](https://copier.readthedocs.io/en/stable/) from the [Meltano EDK template](https://github.com/meltano/edk).
Answers to the questions asked during the generation process are stored in the `.copier_answers.yml` file.

Removing this file can potentially cause unwanted changes to the project if the supplied answers differ from the original when using `copier update`.
