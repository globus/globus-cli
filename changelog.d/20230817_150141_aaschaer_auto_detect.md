### Bugfixes

* When the `--recursive` option is not given when using `globus transfer` the
  `recursive` flag will be omitted from the transfer item rather than being sent as
  `False`. If there is a need to explicitly use `False` to enforce the item is not a
  directory, use the `--no-recursive` option.
