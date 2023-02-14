### Other

* The CLI's handling of changes to its scope requirements over time has been
  improved. After CLI updates which change the required scopes, users will be
  prompted to login again, ensuring that the most up-to-date set of scopes are
  in use.

  ** Changes to the CLI which adjust scopes, and therefore force this
     re-login behavior, will note this in the changelog.

  ** This change, in itself, will not force re-login for any users.
