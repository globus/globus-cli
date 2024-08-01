
### Enhancements

* Added a `--delete` flag to `globus timer create transfer` to mirror
  `globus transfer --delete` functionality.

  This option will delete files, directories, and symlinks on the destination endpoint
  which don’t exist on the source endpoint or are a different type. Only applies for
  recursive directory transfers.
