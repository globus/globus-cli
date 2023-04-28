### Enhancements

* JSON file parsing throughout the CLI has been made more uniform and robust.
  Commands which required files to be specified with the `file:` prefix now
  allow for filenames without the prefix, improving tab-completion. All
  commands which accept JSON data as inputs now allow for files or
  JSON-formatted arguments.
