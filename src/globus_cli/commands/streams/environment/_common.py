from __future__ import annotations

import logging
import os
import random
import shutil
import tempfile
import time
import typing as t
import uuid

import globus_sdk
import globus_sdk.exc as exc
import globus_sdk.response as response
import globus_sdk.scopes as globus_scopes

import globus_cli.login_manager as globus_lm
from globus_cli.services.gcs import CustomGCSClient
from globus_cli.services.transfer.client import CustomTransferClient


class TunnelConf:
    file_key_values = {
        "lankey": str,
        "lankey_id": str,
        "connector_contact_string": str,
        "update_time": int,
        "connector_contact_string_ttl": int,
        "endpoint_id": str,
        "fake_port": str,
        "tunnel_expiration_time": int,
    }

    def __init__(
        self,
        tunnel_id: uuid.UUID,
        basepath: str | globus_sdk.MissingType = globus_sdk.MISSING,
    ) -> None:
        self.lankey: str | None = None
        self.lankey_id: str | None = None
        self.connector_contact_string: str | None = None
        self.update_time: int | None = None
        self.connector_contact_string_ttl: int | None = None
        self.endpoint_id: str | None = None
        self.fake_port: int | None = None
        self.tunnel_expiration_time: int | None = None

        self._normalize_key_file(basepath, tunnel_id)

        for v in self.file_key_values:
            setattr(self, v, None)
        self.file_existed = False
        self._load_values()
        if self.fake_port is None:
            self.fake_port = random.randint(1000, 5000)

    def _normalize_key_file(
        self, basepath: str | globus_sdk.MissingType, tunnel_id: uuid.UUID
    ) -> None:
        if basepath == globus_sdk.MISSING:
            basepath = "~/.globus/tunnels/"
        basepath = os.path.expanduser(basepath)
        os.makedirs(basepath, exist_ok=True)
        os.chmod(basepath, 0o700)

        self.keyfile = os.path.join(basepath, f"{tunnel_id}.conf")
        self.key_file_base_dir = basepath

    def _load_values(self) -> None:
        if not os.path.exists(self.keyfile):
            return

        try:
            with open(self.keyfile) as fptr:
                for line in fptr.readlines():
                    la = line.split("=")
                    try:
                        if la[0] in self.file_key_values:
                            t = self.file_key_values[la[0]]
                            v: str | None = la[1].strip()
                            if v:
                                v = t(v)
                            else:
                                v = None
                            setattr(self, la[0], v)
                    except IndexError:
                        logging.info(f"Found an odd line in key file {self.keyfile}")
            self.file_existed = True
        except Exception as ex:
            logging.warn(f"cannot read the file {self.keyfile}: {str(ex)}")

    def update_keyfile(self) -> None:
        self.update_time = int(time.time())
        tmp = tempfile.NamedTemporaryFile(delete=False, mode="w")
        for k in self.file_key_values:
            v = getattr(self, k, None)
            if v is None:
                v = ""
            tmp.write(f"{k}={v}\n")

        tmp.close()
        shutil.move(tmp.name, self.keyfile)
        os.chmod(self.keyfile, 0o600)
        logging.info("A new tunnel file has been created")

    def dumps(self) -> str:
        out = ""
        for k in self.file_key_values:
            v = getattr(self, k, None)
            if v is None:
                v = ""
            out = f"{k}={v}\n{out}"
        return out


class LoginMgr:
    def __init__(self, endpoint_id: uuid.UUID | None = None) -> None:
        self.login_manager = globus_lm.LoginManager()
        self.endpoint_id = endpoint_id
        if endpoint_id is not None:
            scope = globus_scopes.GCSEndpointScopes(
                str(self.endpoint_id)
            ).manage_collections
            self.login_manager.add_requirement(str(self.endpoint_id), [scope])

        if not self.login_manager.is_logged_in():
            self.login_manager.run_login_flow(
                no_local_server=True,
                epilog="Successful login",
            )

    def get_gcs_client(self) -> CustomGCSClient:
        if self.endpoint_id is None:
            raise Exception("Not configured for GSC")
        return self.login_manager.get_gcs_client(endpoint_id=self.endpoint_id)

    def get_transfer_client(self) -> CustomTransferClient:
        return self.login_manager.get_transfer_client()


class TransferMgr:
    def __init__(
        self, tunnel_id: uuid.UUID, transfer_client: CustomTransferClient
    ) -> None:
        self.tunnel_id = tunnel_id
        self.stream_id = None
        self.contact_string = None
        self.transfer_client = transfer_client
        self.tunnel_doc = self.transfer_client.get_tunnel(tunnel_id)

    def update_listener(self, cs: str) -> None:
        host, _, port = cs.rpartition(":")
        attributes = {
            "listener_ip_address": host,
            "listener_port": port,
        }
        data = {
            "data": {
                "type": "Tunnel",
                "attributes": attributes,
            }
        }
        self.transfer_client.update_tunnel(self.tunnel_id, data)

    def get_listener_stream_id(self) -> t.Any:
        try:
            stream_id = self.tunnel_doc["data"]["relationships"]["listener"]["data"][
                "id"
            ]
            return stream_id
        except KeyError as e:
            raise exc.GlobusSDKUsageError(
                "The listener access point id is not available"
            ) from e

    def get_initiator_stream_id(self) -> t.Any:
        try:
            stream_id = self.tunnel_doc["data"]["relationships"]["initiator"]["data"][
                "id"
            ]
            return stream_id
        except KeyError as e:
            raise exc.GlobusSDKUsageError(
                "The initiator access point id is not available"
            ) from e

    def get_contact_string(self) -> t.Any:
        try:
            host = self.tunnel_doc["data"]["attributes"]["initiator_ip_address"]
            port = self.tunnel_doc["data"]["attributes"]["initiator_port"]
            return f"{host}:{port}"
        except KeyError as e:
            raise exc.GlobusSDKUsageError(
                "The initiator contact string is not available"
            ) from e

    def get_tunnel_lifetime(self) -> t.Any:
        try:
            lifetime_mins = self.tunnel_doc["data"]["attributes"]["lifetime_mins"]
            return lifetime_mins
        except KeyError as e:
            raise exc.GlobusSDKUsageError("The tunnel lifetime is not available") from e

    def get_tunnel_doc(self) -> response.GlobusHTTPResponse:
        return self.tunnel_doc


class GCSMgr:
    def __init__(
        self, stream_id: uuid.UUID, tunnel_id: uuid.UUID, gcs_client: CustomGCSClient
    ) -> None:
        self.gcs_client = gcs_client
        self.stream_id = stream_id
        self.tunnel_id = tunnel_id

    def gcs_get_lankey(self, stream_id: uuid.UUID) -> tuple[str, str]:
        data = {
            "DATA_TYPE": "lan_secret_create#1.0.0",
            "tunnel_id": self.tunnel_id,
            "stream_access_point_id": stream_id,
        }
        res = self.gcs_client.post("/lan_secrets", data=data)
        secret = res["data"][0]["secret"]
        lankey_id = res["data"][0]["id"]
        return secret, lankey_id

    def gcs_delete_lankey(self, lankey_id: uuid.UUID) -> None:
        res = self.gcs_client.delete(f"/lan_secrets/{lankey_id}")
        if res["http_response_code"] != 200:
            raise Exception(res["message"])
