### Enhancements

* Add `--policy` option to `globus session update` which takes a Globus
  Auth policy uuid and starts an auth flow to meet the session's policies.

* Whenever an error is hit due to not meeting a Globus Auth policy, helptext
  is displayed with a `globus session update` command to resolve the error.
