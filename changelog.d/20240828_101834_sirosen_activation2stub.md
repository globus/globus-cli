### Other

* The CLI has removed remaining support for activation.

  * Activation commands such as `globus endpoint is-activated` are already
    hidden, but now act as no-ops when invoked and emit warnings to stderr
    about their upcoming removal.

  * The `--skip-activation-check` option for Transfer task submission has
    been deprecated.

  * `Activated` is no longer a field in `globus endpoint show` output.
