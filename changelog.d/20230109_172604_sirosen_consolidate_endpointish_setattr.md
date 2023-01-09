### Other

* Improve the uniformity of endpoint and collection option parsing.
** The `--sharing-restrict-paths` option to `globus collection update` now
   checks for invalid types (non-dict, non-null data)
** `globus endpoint update` can now null values which previously could not be
   unset by passing `""` for `--contact-email`, `--contact-info`,
   `--department`, `--description`, `--info-link`, and `--organization`. This
   behavior matches `globus collection update`. It also applies to
   `--default-directory`, although `--no-default-directory` is also still
   supported
** `globus gcp create guest` and `globus gcp create mapped` now accept
   `--verify [force|disable|default]` for verification options. This replaces
   `--disable-verify/--no-disable-verify`, which is now deprecated
