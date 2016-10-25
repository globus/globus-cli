import click


class AliasCommand(click.Command):
    def __init__(self, alias_name, target_command):
        self.target_command = target_command
        super(AliasCommand, self).__init__(
            name=alias_name,
            params=target_command.params,
            help=target_command.help,
            epilog=target_command.epilog,
            short_help=target_command.short_help,
            add_help_option=target_command.add_help_option,
            callback=target_command.callback,
            context_settings=target_command.context_settings)

    def invoke(self, ctx):
        ctx.forward(self.target_command)
