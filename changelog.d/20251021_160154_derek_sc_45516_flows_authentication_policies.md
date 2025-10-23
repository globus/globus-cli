
### Enhancements

* Added a new keyword `authentication-policy-id` to the `globus flows create ...` and
  `globus flows update ...` commands to allow creation of high assurance flows.

    * Note that a policy must be set at flow creation time in order to create a high
      assurance flow**.**
      A policy cannot be added to an existing non-high assurance flow.
      A policy can, however, be replaced with a different high assurance policy if one
      was already associated with the flow.
