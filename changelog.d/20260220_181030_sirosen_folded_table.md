### Enhancements

* When using table output on narrow terminals, the Globus CLI will now stack
  table elements in a new "folded table" layout. This behavior is only used
  when the output device is a TTY. To disable the new output altogether, users
  can set `GLOBUS_CLI_FOLD_TABLES=0`.
