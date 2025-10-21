
### Enhancements

* Added a new keyword `authentication-policy-id` to the `globus flows create ...` and
  `globus flows update ...` commands to allow creation of high assurance flows.

    * Note that a policy must be set at flow creation time in order to create a high
      assurance flow; it cannot be added new via an update command (although it can
      be changed to a different policy via update).
