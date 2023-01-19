### Other

*   Configure tox to build a platform-independent wheel and share it among all test environments.

    This requires a change to the code coverage `fail-under` value,
    because coverage now sees three files that are untested:

    *   `src/globus_cli/globus_cli_flake8.py`
    *   `src/globus_cli/login_manager/_old_config.py`
    *   `src/globus_cli/login_manager/local_server.py`

    This change does not result in any performance improvements during local testing.
