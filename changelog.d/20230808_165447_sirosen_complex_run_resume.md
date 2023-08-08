### Enhancements

* Improve `globus flows run resume` to be capable of detecting missing consents and prompt
  for reauthentication via `globus session consent`. The consent check can also
  be skipped with `--skip-inactive-reason-check`.
