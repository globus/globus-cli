
### Enhancements

* Added a new command for non-admins to create GCSv5 Guest Collections.

    ```
    globus collection create guest <mapped_collection_id> <root_path> <display_name>
    ```

* Updated the login-manager's "assert_logins" to verify that non-static dependent scopes
  are met before executing the command (by evaluating a user's current consents).
