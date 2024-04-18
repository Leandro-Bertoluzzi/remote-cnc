<h1 align="center">CNC manager</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/Leandro-Bertoluzzi/cnc-local-app?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/Leandro-Bertoluzzi/cnc-local-app?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/Leandro-Bertoluzzi/cnc-local-app?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/Leandro-Bertoluzzi/cnc-local-app?color=56BEB8">
</p>

<!-- Status -->

<h4 align="center">
	🚧 CNC manager 🚀 Under construction...  🚧
</h4>

<hr>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#wrench-tests">Tests</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-deployment">Deployment</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Authors</a>
</p>

<br>

## :dart: About

Desktop application to monitor and manage an Arduino-based CNC machine connected to the local machine.

## :sparkles: Features

:heavy_check_mark: GUI\
:heavy_check_mark: MySQL database management\
:heavy_check_mark: G-code files management\
:heavy_check_mark: Real time monitoring of CNC status\
:heavy_check_mark: Communication with GRBL-compatible CNC machine via USB\
:heavy_check_mark: Long-running process delegation via message broker

## :rocket: Technologies

The following tools were used in this project:

-   [Python](https://www.python.org/)
-   [PyQt](https://wiki.python.org/moin/PyQt)
-   [Mysql](https://www.mysql.com/)
-   [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/)
-   [Celery](https://docs.celeryq.dev/en/stable/)
-   [Redis](https://redis.io/)
-   [Docker](https://www.docker.com/)

## :white_check_mark: Requirements

Before starting :checkered_flag:, you need to have [Python](https://www.python.org/) installed.

## :checkered_flag: Starting

See [Development](./docs/development.md) docs.

## :wrench: Tests

### Unit tests

```bash
$ pytest -s
```

The coverage report is available in the folder `/htmlcov`.

### Code style linter

```bash
$ flake8
```

### Type check

```bash
$ mypy .
```

### All tests

You can also run all tests together, by using the following command:

```bash
$ make tests
```

## :checkered_flag: Deployment

See [Deployment](./docs/deployment.md) docs.

## :memo: License

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.

## :writing_hand: Authors

Made with :heart: by <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Leandro Bertoluzzi</a> and Martín Sellart.

<a href="#top">Back to top</a>
