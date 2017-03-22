import logging.config
import os
from configobj import ConfigObj

import globus_sdk

from globus_cli import version

__all__ = [
    # option name constants
    'OUTPUT_FORMAT_OPTNAME',
    'AUTH_RT_OPTNAME',
    'AUTH_AT_OPTNAME',
    'AUTH_AT_EXPIRES_OPTNAME',
    'TRANSFER_RT_OPTNAME',
    'TRANSFER_AT_OPTNAME',
    'AUTH_AT_EXPIRES_OPTNAME',
    'WHOAMI_ID_OPTNAME',
    'WHOAMI_USERNAME_OPTNAME',
    'WHOAMI_EMAIL_OPTNAME',
    'WHOAMI_NAME_OPTNAME',

    'GLOBUS_ENV',

    'internal_auth_client',

    'get_output_format',
    'get_auth_tokens',
    'get_transfer_tokens',

    'get_config_obj',
    'write_option',
    'remove_option',
    'lookup_option',
]


# constant for use throughout the SDK whenever we need to do things using the
# CLI Native App definition
# accessed via `internal_auth_client()` -- not exported
CLIENT_ID = '95fdeba8-fac2-42bd-a357-e068d82ff78e'
# an extra option (not exported) for using the CLI against other Globus
# Environments (like the future beta environment)
ENV_CLIENT_ID_OPTNAME = 'cli_client_id'

# constants for global use
OUTPUT_FORMAT_OPTNAME = 'output_format'
AUTH_RT_OPTNAME = 'auth_refresh_token'
AUTH_AT_OPTNAME = 'auth_access_token'
AUTH_AT_EXPIRES_OPTNAME = 'auth_access_token_expires'
TRANSFER_RT_OPTNAME = 'transfer_refresh_token'
TRANSFER_AT_OPTNAME = 'transfer_access_token'
TRANSFER_AT_EXPIRES_OPTNAME = 'transfer_access_token_expires'
WHOAMI_ID_OPTNAME = 'whoami_identity_id'
WHOAMI_USERNAME_OPTNAME = 'whoami_identity_username'
WHOAMI_EMAIL_OPTNAME = 'whoami_identity_email'
WHOAMI_NAME_OPTNAME = 'whoami_identity_display_name'

# get the environment from env var (not exported)
GLOBUS_ENV = os.environ.get('GLOBUS_SDK_ENVIRONMENT')

# if the env is set, rewrite the refresh token option names to have it as a
# prefix
if GLOBUS_ENV:
    AUTH_RT_OPTNAME = '{0}_auth_refresh_token'.format(GLOBUS_ENV)
    AUTH_AT_OPTNAME = '{0}_auth_access_token'.format(GLOBUS_ENV)
    AUTH_AT_EXPIRES_OPTNAME = '{0}_auth_access_token_expires'.format(
        GLOBUS_ENV)
    TRANSFER_RT_OPTNAME = '{0}_transfer_refresh_token'.format(GLOBUS_ENV)
    TRANSFER_AT_OPTNAME = '{0}_transfer_access_token'.format(GLOBUS_ENV)
    TRANSFER_AT_EXPIRES_OPTNAME = '{0}_transfer_access_token_expires'.format(
        GLOBUS_ENV)
    WHOAMI_ID_OPTNAME = '{0}_whoami_identity_id'.format(GLOBUS_ENV)
    WHOAMI_USERNAME_OPTNAME = '{0}_whoami_identity_username'.format(GLOBUS_ENV)
    WHOAMI_EMAIL_OPTNAME = '{0}_whoami_identity_email'.format(GLOBUS_ENV)
    WHOAMI_NAME_OPTNAME = '{0}_whoami_identity_display_name'.format(GLOBUS_ENV)


def get_config_obj(system=False):
    if system:
        path = '/etc/globus.cfg'
    else:
        path = os.path.expanduser("~/.globus.cfg")

    return ConfigObj(path)


def lookup_option(option, section='cli', environment=None):
    conf = get_config_obj()
    try:
        if environment:
            return conf["environment " + environment][option]
        else:
            return conf[section][option]
    except KeyError:
        return None


def remove_option(option, section='cli', system=False):
    conf = get_config_obj(system=system)

    # if there's no section for the option we're removing, just return None
    try:
        section = conf[section]
    except KeyError:
        return None

    try:
        opt_val = section[option]

        # remove value and flush to disk
        del section[option]
        conf.write()
    except KeyError:
        opt_val = None

    # return the just-deleted value
    return opt_val


def write_option(option, value, section='cli', system=False):
    """
    Write an option to disk -- doesn't handle config reloading
    """
    # deny rwx to Group and World -- don't bother storing the returned old mask
    # value, since we'll never restore it in the CLI anyway
    # do this on every call to ensure that we're always consistent about it
    os.umask(0o077)

    # FIXME: DRY violation with config_commands.helpers
    conf = get_config_obj(system=system)

    # add the section if absent
    if section not in conf:
        conf[section] = {}

    conf[section][option] = value
    conf.write()


def get_output_format():
    return lookup_option(OUTPUT_FORMAT_OPTNAME)


def get_auth_tokens():
    expires = lookup_option(AUTH_AT_EXPIRES_OPTNAME)
    if expires is not None:
        expires = int(expires)

    return {
        'refresh_token': lookup_option(AUTH_RT_OPTNAME),
        'access_token': lookup_option(AUTH_AT_OPTNAME),
        'access_token_expires': expires
    }


def set_auth_access_token(token, expires_at):
    write_option(AUTH_AT_OPTNAME, token)
    write_option(AUTH_AT_EXPIRES_OPTNAME, expires_at)


def get_transfer_tokens():
    expires = lookup_option(TRANSFER_AT_EXPIRES_OPTNAME)
    if expires is not None:
        expires = int(expires)

    return {
        'refresh_token': lookup_option(TRANSFER_RT_OPTNAME),
        'access_token': lookup_option(TRANSFER_AT_OPTNAME),
        'access_token_expires': expires
    }


def set_transfer_access_token(token, expires_at):
    write_option(TRANSFER_AT_OPTNAME, token)
    write_option(TRANSFER_AT_EXPIRES_OPTNAME, expires_at)


def internal_auth_client():
    # check to see if an alternate client ID has been specified by the
    # environment
    client_id = lookup_option(ENV_CLIENT_ID_OPTNAME,
                              environment=GLOBUS_ENV) or CLIENT_ID

    return globus_sdk.NativeAppAuthClient(client_id, app_name=version.app_name)


def setup_logging(level="DEBUG"):
    conf = {
        'version': 1,
        'formatters': {
            'basic': {
                'format':
                '[%(levelname)s] %(name)s::%(funcName)s() %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'basic'
            }
        },
        'loggers': {
            'globus_sdk': {
                'level': level,
                'handlers': ['console']
            }
        }
    }

    logging.config.dictConfig(conf)
