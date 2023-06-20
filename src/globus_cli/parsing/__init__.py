from .commands import command, group, main_group
from .mutex_group import MutexInfo, mutex_option_group
from .param_classes import AnnotatedOption, one_use_option
from .param_types import (
    ENDPOINT_PLUS_OPTPATH,
    ENDPOINT_PLUS_REQPATH,
    AnnotatedParamType,
    CommaDelimitedList,
    IdentityType,
    JSONStringOrFile,
    LocationType,
    ParsedIdentity,
    ParsedJSONData,
    StringOrNull,
    TaskPath,
    TimedeltaType,
    UrlOrNull,
    nullable_multi_callback,
)
from .shared_options import (
    delete_and_rm_options,
    local_user_option,
    no_local_server_option,
    security_principal_opts,
    synchronous_task_wait_options,
    task_notify_option,
    task_submission_options,
)
from .shared_options.endpointish import endpointish_params
from .shared_options.id_args import (
    collection_id_arg,
    endpoint_id_arg,
    flow_id_arg,
    run_id_arg,
)
from .shared_options.transfer_task_options import (
    encrypt_data_option,
    fail_on_quota_errors_option,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)

__all__ = [
    # replacement decorators
    "command",
    "group",
    "main_group",
    "one_use_option",
    # param classes
    "AnnotatedOption",
    # param types
    "ENDPOINT_PLUS_OPTPATH",
    "ENDPOINT_PLUS_REQPATH",
    "AnnotatedParamType",
    "CommaDelimitedList",
    "IdentityType",
    "JSONStringOrFile",
    "LocationType",
    "MutexInfo",
    "ParsedIdentity",
    "ParsedJSONData",
    "StringOrNull",
    "TaskPath",
    "TimedeltaType",
    "UrlOrNull",
    "mutex_option_group",
    "nullable_multi_callback",
    "one_use_option",
    # shared options
    "collection_id_arg",
    "endpoint_id_arg",
    "flow_id_arg",
    "run_id_arg",
    "task_submission_options",
    "delete_and_rm_options",
    "synchronous_task_wait_options",
    "security_principal_opts",
    "no_local_server_option",
    "transfer_recursive_option",
    "transfer_batch_option",
    "sync_level_option",
    "task_notify_option",
    "fail_on_quota_errors_option",
    "encrypt_data_option",
    "preserve_timestamp_option",
    "skip_source_errors_option",
    "verify_checksum_option",
    "endpointish_params",
    "local_user_option",
]
