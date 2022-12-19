import click


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

        In code, produces True, False, or a set
        """
        # if no value was set, don't set any explicit options
        # the API default is "everything on"
        if value is None:
            return {}

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
