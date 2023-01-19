### Other

*   Cache downloaded PyPI packages, Python virtual environments, and tox environments in CI.

    Performance numbers:

    ```
                    +-------------------+-----------+
                    | Total duration    | CI usage  |
    +---------------+-------------------+-----------+
    | No caching    | 2m 39s            | 11m 52s   |
    | Cache miss    | 2m 05s            | 14m 53s   |
    | Cache hit     | 1m 45s            |  8m 25s   |
    +---------------+-------------------+-----------+
    ```

    Note that, after this change is merged, cache misses are expected to be infrequent.
    This is because CI runs in branches have access to caches created in the `main` branch,
    and CI runs against the `main` branch every Monday at 4 A.M UTC.
    Therefore, it is expected that cache hits will be common.
