import glob
import os
import tempfile
import time
import unittest.mock as mock
import uuid

from globus_sdk.testing import load_response_set

import globus_cli.commands.streams.environment._common as gtutils
import globus_cli.login_manager

_g_xfer_mgr = "gtutils.TransferMgr"
_g_login_mgr = "gtutils.LoginMgr"
_g_gcs_mgr = "gtutils.GCSMgr"
#
#
# @pytest.mark.parametrize("output_format", ["json", "text"])
# def test_help(run_line, output_format):
#     result = run_line(["globus", "streams", "environment", "--help"])
#     assert result.exit_code == 0


def test_initialize_happy(run_line, add_gcs_login):
    meta = load_response_set("cli.streams_environment").metadata

    lankey = meta["lankey"]
    lankey_id = meta["lankey_id"]
    tunnel_id = meta["tunnel_id"]
    cs = "localhost:9999"
    cs_ttl = 99
    endpoint_id = meta["endpoint_id"]

    add_gcs_login(endpoint_id)

    with (
        tempfile.TemporaryDirectory() as tmp_path,
        mock.patch(
            "globus_cli.login_manager.LoginManager.is_logged_in", return_value=True
        ),
    ):

        # lm.is_logged_in.return_value = True
        result = run_line(
            [
                "globus",
                "streams",
                "environment",
                "initialize",
                "--base-dir",
                tmp_path,
                "--cs-ttl",
                cs_ttl,
                str(tunnel_id),
                endpoint_id,
            ],
        )
        assert result.exit_code == 0

        conf = gtutils.TunnelConf(tunnel_id, tmp_path)
        assert conf.endpoint_id == endpoint_id
        assert conf.connector_contact_string == cs
        assert conf.connector_contact_string_ttl == cs_ttl
        assert conf.lankey == lankey
        assert conf.lankey_id == lankey_id
