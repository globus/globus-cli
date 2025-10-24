
### Enhancements

* Raise flow scopes more frequently in `globus session update` remediation instructions.
   * Doing so helps ensure that resource-specific scopes are properly updated when
     users are put through session remediation logins to mitigate double-logins.
   * Impacted commands:
     * `globus flows ...`: `delete`, `show`, `start`, and `update`
     * `globus flows run ...`: `delete`, `resume`, `show`, `show-definition`,
       `show-logs`, and `update`
        * In these commands, a flow id isn't user-supplied, so it's queried from search.
