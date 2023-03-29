### Enhancements

* Add `--include` option to `globus transfer` allowing ordered overrides of `--exclude` rules.

### Breaking Changes

* The `--exclude` option for `globus transfer` now only applies to files to better
  support excluding files within a directory structure
