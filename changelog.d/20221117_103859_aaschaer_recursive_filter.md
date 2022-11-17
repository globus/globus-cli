### Enhancements

* `globus ls` has improved behavior when the `--filter` and `--recursive` options
   are used in combination

  * directory names are not matched against the filter, allowing the operation to
    traverse directories regardless of their names

  * the `--filter` is still applied to filenames in all directories traversed by
    the `ls` operation

  * directory names can be filtered out of the text output by eliminating
    lines which end in `/`

  * the behaviors of `globus ls` commands with `--recursive` or `--filter`, but not
    both, are unchanged
