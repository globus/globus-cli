from __future__ import annotations

import os
import typing as t
from configparser import ConfigParser

import globus_sdk

GLOBUS_ENV = os.environ.get("GLOBUS_SDK_ENVIRONMENT")


def _get_old_conf_path() -> str:
    return os.path.expanduser("~/.globus.cfg")


def _old_conf_parser() -> ConfigParser:
    conf = ConfigParser()
    conf.read(_get_old_conf_path())
    return conf


def _token_conf_keys() -> t.Iterator[str]:
    for k in [
        "auth_refresh_token",
        "auth_access_token",
        "transfer_refresh_token",
        "transfer_access_token",
    ]:
        # if the env is set, rewrite the option names to have it as a prefix
        yield (f"{GLOBUS_ENV}_{k}" if GLOBUS_ENV else k)


def _old_tokens_to_revoke(conf: ConfigParser) -> t.Iterator[str]:
    for key in _token_conf_keys():
        tokenstr = conf.get("cli", key, fallback=None)
        if tokenstr:
            yield tokenstr


def _get_client_creds(conf: ConfigParser) -> tuple[str, str] | None:
    id_key, secret_key = ("client_id", "client_secret")
    if GLOBUS_ENV:
        id_key, secret_key = (f"{GLOBUS_ENV}_client_id", f"{GLOBUS_ENV}_client_secret")
    client_id = conf.get("cli", id_key, fallback=None)
    client_secret = conf.get("cli", secret_key, fallback=None)
    if client_id and client_secret:
        return (client_id, client_secret)
    return None


def invalidate_old_config(auth_client: globus_sdk.AuthClient) -> None:
    # revoke any old config-stored tokens (logout)
    # and delete old client creds
    conf = _old_conf_parser()
    if not conf.has_section("cli"):
        return

    # Revoke any tokens found in ~/.globus.cfg
    for token in _old_tokens_to_revoke(conf=conf):
        auth_client.oauth2_revoke_token(token)

    # Delete a templated client found configured in ~/.globus.cfg
    creds = _get_client_creds(conf)
    if creds:
        client_id, client_secret = creds
        old_client = globus_sdk.ConfidentialAppAuthClient(client_id, client_secret)
        try:
            old_client.delete(f"/v2/api/clients/{client_id}")
        # if the client secret has been invalidated or the client has
        # already been deleted, continue
        except globus_sdk.AuthAPIError:
            pass
