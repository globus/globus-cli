from globus_cli.parsing.custom_group import globus_group
from globus_cli.parsing.main_command_decorator import globus_main_func

from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.task_path import TaskPath
from globus_cli.parsing.endpoint_plus_path import (
    ENDPOINT_PLUS_OPTPATH, ENDPOINT_PLUS_REQPATH)

from globus_cli.parsing.hidden_option import HiddenOption

from globus_cli.parsing.shared_options import (
    common_options,
    endpoint_id_arg, task_id_arg, submission_id_option,
    endpoint_create_and_update_params,
    endpoint_create_and_update_validate_params,
    role_id_arg, server_id_arg, server_add_and_update_opts,
    security_principal_opts)

from globus_cli.parsing.process_stdin import shlex_process_stdin


__all__ = [
    'globus_group',
    'globus_main_func',

    'CaseInsensitiveChoice',
    'ENDPOINT_PLUS_OPTPATH', 'ENDPOINT_PLUS_REQPATH',
    'TaskPath',

    'HiddenOption',

    'common_options',
    # Transfer options
    'endpoint_id_arg', 'task_id_arg', 'submission_id_option',
    'endpoint_create_and_update_params',
    'endpoint_create_and_update_validate_params',
    'role_id_arg', 'server_id_arg', 'server_add_and_update_opts',
    'security_principal_opts',

    'shlex_process_stdin',
]
