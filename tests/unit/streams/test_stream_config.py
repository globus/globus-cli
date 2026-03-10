import os
import tempfile
import uuid

import globus_cli.commands.streams.environment._common as gtutils


def test_default_values_config():
    with tempfile.TemporaryDirectory() as tmp_path:
        tunnel_id = uuid.uuid4()
        conf = gtutils.TunnelConf(tunnel_id, tmp_path)
        assert not conf.file_existed

        for f in conf.file_key_values:
            if f != "fake_port":
                assert getattr(conf, f) is None


def test_set_values_config():
    lankey = "XXXXX"
    lankey_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as tmp_path:
        tunnel_id = uuid.uuid4()
        conf = gtutils.TunnelConf(tunnel_id, tmp_path)

        conf.lankey = lankey
        conf.lankey_id = lankey_id

        conf.update_keyfile()

        assert os.path.exists(conf.keyfile)

        conf2 = gtutils.TunnelConf(tunnel_id, tmp_path)

        assert conf2.file_existed
        assert conf2.lankey == lankey
        assert conf2.lankey_id == lankey_id
        assert conf2.connector_contact_string is None
