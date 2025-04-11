import click
from click.shell_completion import CompletionItem

from globus_cli.constants import ExplicitNullType


class GCSManagerGuestActivityNotificationParamType(click.ParamType):

    VALID_STATUSES = {
        "succeeded",
        "failed",
    }

    VALID_TRANSFER_USES = {
        "source",
        "destination",
    }

    VALID_NOTIFICATION_VALUES = VALID_TRANSFER_USES.copy()
    VALID_NOTIFICATION_VALUES |= VALID_STATUSES

    def get_metavar(self, param: click.Parameter) -> str:
        return "{all,succeeded,failed,source,destination}"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> dict[str, list[str]] | ExplicitNullType:

        if value == "":
            return {
                "status": [],
                "transfer_use": [],
            }

        if value.lower() == "all":
            return {
                "status": sorted(self.VALID_STATUSES),
                "transfer_use": sorted(self.VALID_TRANSFER_USES),
            }

        policy: dict[str, list[str]] = {
            "status": [],
            "transfer_use": [],
        }

        # ignore white space, parse input sans case-sensitivity
        lowercase_vals: set[str] = {s.strip().lower() for s in value.split(",")}

        if "all" in lowercase_vals:
            raise click.UsageError(
                '--activity-notifications cannot accept "all" with other values'
            )

        val: str
        if lowercase_vals <= self.VALID_NOTIFICATION_VALUES:
            for val in lowercase_vals:
                if val in self.VALID_TRANSFER_USES:
                    policy["transfer_use"].append(val)
                else:
                    policy["status"].append(val)
        else:
            invalid_values = sorted(lowercase_vals - self.VALID_NOTIFICATION_VALUES)
            raise click.UsageError(
                "--activity-notifications received these invalid values: "
                f"{invalid_values}"
            )

        # Fill in implied values.
        k: str
        v: list[str]
        for k, v in policy.items():
            if k == "transfer_use" and not v:
                v = list(self.VALID_TRANSFER_USES)
            elif k == "status" and not v:
                v = list(self.VALID_STATUSES)
            # Ensure deterministic ordering for testability.
            policy[k] = sorted(v)

        return policy

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> list[CompletionItem]:
        all_compoundable_options = ["destination", "failed", "source", "succeeded"]

        all_options = ["all"] + all_compoundable_options

        # if the caller used `--activity_notifications <TAB>`, show all options
        # if the caller used `--activity_notifications <TAB>`, show `source` and
        # `succeeded` the logic below assumes there were commas
        if "," not in incomplete:
            return [CompletionItem(o) for o in all_options if o.startswith(incomplete)]

        # grab the last partial name from the list
        # e.g. if the caller used `--activity-notifications source,succ<TAB>`, then
        #      collect `succ` as the last incomplete fragment
        #
        # also collect the valid completed parts for comparisons
        *already_contains, last_incomplete_fragment = incomplete.split(",")

        # trim out empty strings; this will be reassembled later into the completed
        # option and this removal will help result in translating `failed,,source`
        # into `failed,source`
        already_contains = [s for s in already_contains if s != ""]

        # for possible options to complete, remove the set of already completed values
        #
        # e.g. `--acrivity-notifications failed,f<TAB>` will offer no completion, since
        # `failed` was already used
        # this also means that `--activity-notifications source,<TAB>` will offer
        # `destination`, `failed`, and `succeeded` but not `source`.
        #
        # convert to a sorted list in case completion behavior is order-sensitive
        possible_options = sorted(set(all_compoundable_options) - set(already_contains))

        # now limit those options to those which start with the last fragment
        #
        # if the option was complete, it may be considered the only possible option
        # i.e. `--activity-notifiations failed,succeeded,source,destination<TAB>`
        # indicates valid usage
        #
        # if the option was blank, as in `--activity-notifications source,<TAB>`, then
        # last_incomplete_fragment is "" and this filter won't remove anything
        possible_options = [
            o for o in possible_options if o.startswith(last_incomplete_fragment)
        ]

        # if the list became empty, we trust that the user has input a value
        # which has some meaning unknown to the completer
        # e.g. `--activity-notifications succeeded,UNKNOWN`
        if possible_options == []:
            possible_options = [last_incomplete_fragment]

        # handle a corner case!
        #
        # all options were used with a trailing comma:
        #    --activity-notifications source,destination,failed,succeeded,
        if possible_options == [""]:
            return [CompletionItem(",".join(already_contains))]

        return [
            CompletionItem(",".join(already_contains + [o])) for o in possible_options
        ]


class TransferGuestActivityNotificationParamType(
    GCSManagerGuestActivityNotificationParamType
):

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> dict[str, list[str]] | ExplicitNullType:

        policy: dict[str, list[str]] | ExplicitNullType = super().convert(
            value, param, ctx
        )

        if isinstance(policy, dict):
            if not (policy["status"] and policy["transfer_use"]):
                return ExplicitNullType()
            policy["status"] = [x.upper() for x in policy["status"]]

        return policy
