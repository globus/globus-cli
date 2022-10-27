import click

from globus_cli.termio import formatters


class RolePrincipalFormatter(formatters.PrincipalDictFormatter):
    def render_group_id(self, group_id: str) -> str:
        return f"https://app.globus.org/groups/{group_id}"


def role_id_arg(f):
    return click.argument("role_id")(f)
