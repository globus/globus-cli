### Bugfixes

* Fixed a bug in which terminal device (TTY) detection ran even when
  `GLOBUS_CLI_FOLD_TABLES=1` is set.
  Setting the variable to true now forces use of folded tables.
  Non-TTY output devices will be detected as having a fixed width of 80
  characters.
