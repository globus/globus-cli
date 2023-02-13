### Bugfixes

* Fix the handling of multiple `-Q` parameters with the same name for
  the `globus api` commands. Such usages were only sending the last value
  used, but now correctly send all parameters.
