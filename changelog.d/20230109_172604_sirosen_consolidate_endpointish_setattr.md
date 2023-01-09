### Other

* Improve the uniformity of endpoint and collection option parsing.
** The `--sharing-restrict-paths` option to `globus collection update` now
   checks for invalid types (non-dict, non-null data)
** `globus endpoint update` now treats the empty string as null for the
   following options: `--contact-email`, `--contact-info`,
   `--default-directory`, `--department`, `--description`, `--info-link`,
   and `--organization`. This behavior matches `globus collection update`.
   `--no-default-directory` is still supported, but is equivalent to
   `--default-directory ""`
** `globus gcp create guest` and `globus gcp create mapped` now accept
   `--verify [force|disable|default]` for verification options. This replaces
   `--disable-verify/--no-disable-verify`, which is now deprecated
