import click
from click.shell_completion import CompletionItem


class NotificationParamType(click.ParamType):
    def get_metavar(self, param) -> str:
        return "{on,off,succeeded,failed,inactive}"

    def convert(self, value, param, ctx):
        """
        Parse --notify
        - "" is the same as "off"
        - parse by lowercase, comma-split, strip spaces
        - "off,x" is invalid for any x
        - "on,x" is valid for any valid x (other than "off")
        - "failed", "succeeded", "inactive" are normal vals

        The converted value is always a dictionary which is expected to be
        '**'-expanded into arguments to TransferData or DeleteData, containing
        0-or-more of the following keys:

          - notify_on_failed
          - notify_on_inactive
          - notify_on_succeeded
        """
        value = value.lower()
        value = [x.strip() for x in value.split(",")]
        # [""] is what you'll get if value is "" to start with
        # special-case it into "off", which helps avoid surprising scripts
        # which take a notification settings as inputs and build --notify
        if value == [""]:
            value = ["off"]

        off = "off" in value
        on = "on" in value
        # set-ize it -- duplicates are fine
        vals = {x for x in value if x not in ("off", "on")}

        if (vals or on) and off:
            raise click.UsageError('--notify cannot accept "off" and another value')

        allowed_vals = {"on", "succeeded", "failed", "inactive"}
        if not vals <= allowed_vals:
            raise click.UsageError(
                "--notify received at least one invalid value among {}".format(
                    list(vals)
                )
            )

        # return the notification options to send!
        # on means don't set anything (default)
        if on:
            return {}
        # off means turn off everything
        if off:
            return {
                "notify_on_succeeded": False,
                "notify_on_failed": False,
                "notify_on_inactive": False,
            }
        # otherwise, return the exact set of values seen
        else:
            return {
                "notify_on_succeeded": "succeeded" in vals,
                "notify_on_failed": "failed" in vals,
                "notify_on_inactive": "inactive" in vals,
            }

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> list[CompletionItem]:
        all_compoundable_options = ["failed", "inactive", "succeeded"]
        all_options = ["on", "off"] + all_compoundable_options

        # if the caller used `--notify <TAB>`, show all options
        # if the caller used `--notify o<TAB>`, show `on` and `off`
        # the logic below assumes there were commas
        if "," not in incomplete:
            return [CompletionItem(o) for o in all_options if o.startswith(incomplete)]

        # grab the last partial name from the list
        # e.g. if the caller used `--notify inactive,succ<TAB>`, then
        #      collect `succ` as the last incomplete fragment
        #
        # also collect the valid completed parts into a set for comparisons
        last_incomplete_fragment = incomplete.split(",")[-1]
        already_contains = set(incomplete.split(",")[:-1])

        # if the option was complete, do not offer a further completion
        # `--notify failed,inactive<TAB>` indicates valid  usage
        if last_incomplete_fragment in all_options:
            return [CompletionItem(incomplete)]

        # for possible options to complete, remove the set of already completed values
        #
        # e.g. `--notify succeeded,s<TAB>` will offer no completion, since `succeeded`
        # was already used
        # this also means that `--notify failed,<TAB>` will offer `failed` and
        # `inactive` but not `succeeded`
        #
        # convert to a sorted list in case completion behavior is order-sensitive
        possible_options = sorted(set(all_compoundable_options) - already_contains)

        # if the last fragment is empty, usage was like `--notify failed,<TAB>`
        if last_incomplete_fragment == "":
            with_trailing_comma = incomplete.rstrip(",") + ","
            return [CompletionItem(with_trailing_comma + o) for o in possible_options]

        # if the last fragment is nonempty, trim it and replace it with the valid
        # completions
        without_last_incomplete = incomplete[: -len(last_incomplete_fragment)]
        return [
            CompletionItem(without_last_incomplete + o)
            for o in possible_options
            if o.startswith(last_incomplete_fragment)
        ]
