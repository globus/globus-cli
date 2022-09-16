### Enhancements

* New commands for creating Globus Connect Personal endpoints and collections
** `globus gcp create mapped` creates a GCP Mapped Collection
** `globus gcp create guest` creates a GCP Guest Collection

In GCP, the Mapped Collection and Endpoint are synonymous. Therefore,
`globus gcp create mapped` replaces the functionality previously only available
via `globus endpoint create --personal`.

NOTE: Neither of the `globus gcp create` commands automatically installs Globus
Connect Personal on the local machine. These commands complement and interact with
an existing installation.

### Other

* `globus endpoint create` is now documented as deprecated. Users are
  encouraged to use `globus gcp create` for Globus Connect Personal,
  and the Globus Connect Server CLI for Globus Connect Server
* `globus endpoint create` no longer accepts `--no-default-directory` as an
  option. It previously did nothing when used.
