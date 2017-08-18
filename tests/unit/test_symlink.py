from random import getrandbits

from globus_sdk import DeleteData

from tests.framework.constants import GO_EP3_ID
from tests.framework.cli_testcase import CliTestCase


class SymlinkTests(CliTestCase):
    """
    Tests `globus symlink` command
    """

    def test_symlink(self):
        """
        Uses `globus symlink` to create a symlink, validates results and
        confirms symlink's existence.
        """
        # run symlink
        link_target = "/share/godata/"
        link_name = "link" + str(getrandbits(128))
        link_path = "~/" + link_name
        output = self.run_line("globus symlink {0}:{1} {0}:{2}".format(
            GO_EP3_ID, link_target, link_path))
        self.assertEqual("Symbolic link created successfully\n", output)

        # confirm symlink created
        ls_res = self.tc.operation_ls(GO_EP3_ID, filter="name:" + link_name)
        self.assertEqual(ls_res["DATA"][0]["link_target"], link_target)

        # cleanup
        ddata = DeleteData(self.tc, GO_EP3_ID)
        ddata.add_item(link_path)
        self.tc.submit_delete(ddata)
