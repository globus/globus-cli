from globus_cli.parsing.commands import command, group, main_group
from globus_cli.parsing.mutex_group import MutexInfo, mutex_option_group
from globus_cli.parsing.one_use_option import one_use_option
from globus_cli.parsing.shared_options import (
    collection_id_arg,
    delete_and_rm_options,
    endpoint_id_arg,
    no_local_server_option,
    security_principal_opts,
    sync_level_option,
    synchronous_task_wait_options,
    task_notify_option,
    task_submission_options,
    transfer_batch_option,
    transfer_recursive_option,
)

from .param_types import (
    ENDPOINT_PLUS_OPTPATH,
    ENDPOINT_PLUS_REQPATH,
    CommaDelimitedList,
    IdentityType,
    JSONStringOrFile,
    LocationType,
    ParsedIdentity,
    StringOrNull,
    TaskPath,
    TimedeltaType,
    UrlOrNull,
    nullable_multi_callback,
)

__all__ = [
    # replacement decorators
    "command",
    "group",
    "main_group",
    "one_use_option",
    # param types
    "ENDPOINT_PLUS_OPTPATH",
    "ENDPOINT_PLUS_REQPATH",
    "CommaDelimitedList",
    "IdentityType",
    "JSONStringOrFile",
    "LocationType",
    "MutexInfo",
    "ParsedIdentity",
    "StringOrNull",
    "TaskPath",
    "TimedeltaType",
    "UrlOrNull",
    "mutex_option_group",
    "nullable_multi_callback",
    "one_use_option",
    # Transfer options
    "collection_id_arg",
    "endpoint_id_arg",
    "task_submission_options",
    "delete_and_rm_options",
    "synchronous_task_wait_options",
    "security_principal_opts",
    "no_local_server_option",
    "transfer_recursive_option",
    "transfer_batch_option",
    "sync_level_option",
    "task_notify_option",
]
