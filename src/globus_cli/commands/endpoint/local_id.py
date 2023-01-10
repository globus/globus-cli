import click
import globus_sdk

from globus_cli.parsing import command, one_use_option


@command(
    "local-id",
    short_help="Display UUID of locally installed endpoint",
    disable_options=["format", "map_http_status"],
    adoc_examples="""Do a Globus ls command on the current local endpoint.

[source,bash]
----
$ globus ls "$(globus endpoint local-id)"':/~/'
----

On the assumption that the default directory for Globus Connect Personal is the
user's homedir, list files in the current working directory via Globus:

[source,bash]
----
#!/bin/bash
# NOTE: this script only works in subdirs of $HOME

if [[ $PWD/ != $HOME/* ]]; then
  echo "Only works in homedir" >&2
  exit 1
fi

# get the CWD as a path relative to the homedir
dir_to_ls=${PWD/#$HOME/'~'}

ep_id="$(globus endpoint local-id)"

globus ls "${ep_id}:/${dir_to_ls}"
----
""",
)
@one_use_option(
    "--personal",
    is_flag=True,
    default=True,
    type_annotation=bool,
    help="Use local Globus Connect Personal endpoint (default)",
)
def local_id(personal: bool) -> None:

    """
    Look for data referring to a local installation of Globus Connect Personal software
    and display the associated endpoint ID.

    This operates by looking for Globus Connect Personal data in the current user's
    home directory.
    """
    if personal:
        try:
            ep_id = globus_sdk.LocalGlobusConnectPersonal().endpoint_id
        except OSError as e:
            click.echo(e, err=True)
            click.get_current_context().exit(1)

        if ep_id is not None:
            click.echo(ep_id)
        else:
            click.echo("No Globus Connect Personal installation found.")
            click.get_current_context().exit(1)
