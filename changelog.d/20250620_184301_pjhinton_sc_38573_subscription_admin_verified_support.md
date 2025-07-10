### Enhancements

* The `globus gcp set-subscription-admin-verified` command may be used by a
  subscription group administrator to grant and revoke verification on a
  GCP collection. This command does not require that the user have a role
  on the collection receiving the verification. Supplying a value of `true`
  grants the verification, and a value of `false` revokes the verification.

* The `globus gcp update mapped` and `globus gcp update guest` commands now
  accept the option `--subscription-admin-verified`. An administrator on a
  GCP collection can set the option to `true` to grant verification, provided
  that the identity also is an administrator in the subscription group. The
  verification status may be revoked by setting the option to `false`. Revocation
  does not require an administrator role in the subscription group.
