from random import getrandbits
import json

from tests.framework.cli_testcase import CliTestCase
from tests.framework.constants import GO_EP1_ID


class RMTests(CliTestCase):

    def test_recursive(self):
        """
        Makes a dir on ep1, then --recursive rm's it.
        Confirms delete task was successful.
        """
        # name randomized to prevent collision
        path = "/~/rm_dir-{}".format(str(getrandbits(128)))
        self.tc.operation_mkdir(GO_EP1_ID, path)

        output = self.run_line(
            "globus rm -r -F json {}:{}".format(GO_EP1_ID, path))
        res = json.loads(output)
        self.assertEqual(res["status"], "SUCCEEDED")

    def test_no_file(self):
        """
        Attempts to remove a non-existant file. Confirms exit code 1
        """
        path = "/~/nofilehere.txt"
        self.run_line(
            "globus rm {}:{}".format(GO_EP1_ID, path), assert_exit_code=1)

    def test_ignore_missing(self):
        """
        Attempts to remove a non-existant file path, with --ignore-missing.
        Confirms exit code 0 and silent output.
        """
        path = "/~/nofilehere.txt"
        output = self.run_line("globus rm -f {}:{}".format(GO_EP1_ID, path))
        self.assertEqual(output, "")

    def test_pattern_globbing(self):
        """
        Makes 3 dirs with the same prefix, and uses * globbing to rm them all.
        Confirms delete task was successful and removed 3 dirs.
        """
        # mark all dirs with a random generated prefix to prevent collision
        rand = str(getrandbits(128))
        for i in range(3):
            path = "/~/rm_dir{}-{}".format(rand, i)
            self.tc.operation_mkdir(GO_EP1_ID, path)

        # remove all dirs with the prefix
        glob = "rm_dir{}*".format(rand)
        output = self.run_line(
            "globus rm -r -F json {}:{}".format(GO_EP1_ID, glob))
        res = json.loads(output)
        self.assertEqual(res["status"], "SUCCEEDED")

        # confirm no dirs with the prefix exist on the endpoint
        filter_string = "name:~rm_dir{}*".format(rand)
        ls_doc = self.tc.operation_ls(GO_EP1_ID, filter=filter_string)
        for item in ls_doc:
            self.assertTrue(False)

    def test_wild_globbing(self):
        """
        Makes 3 dirs with the same prefix, and uses ? globbing to rm them all.
        Confirms delete task was successful and removed 3 dirs.
        """
        # mark all dirs with a random generated prefix to prevent collision
        rand = str(getrandbits(128))
        for i in range(3):
            path = "/~/rm_dir{}-{}".format(rand, i)
            self.tc.operation_mkdir(GO_EP1_ID, path)

        # remove all dirs with the prefix
        glob = "rm_dir{}-?".format(rand)
        output = self.run_line(
            "globus rm -r -F json {}:{}".format(GO_EP1_ID, glob))
        res = json.loads(output)
        self.assertEqual(res["status"], "SUCCEEDED")

        # confirm no dirs with the prefix exist on the endpoint
        filter_string = "name:~rm_dir{}*".format(rand)
        ls_doc = self.tc.operation_ls(GO_EP1_ID, filter=filter_string)
        for item in ls_doc:
            self.assertTrue(False)

    def test_bracket_globbing(self):
        """
        Makes 3 dirs with the same prefix, and uses [] globbing to rm them all.
        Confirms delete task was successful and removed 3 dirs.
        """
        # mark all dirs with a random generated prefix to prevent collision
        rand = str(getrandbits(128))
        for i in range(3):
            path = "/~/rm_dir{}-{}".format(rand, i)
            self.tc.operation_mkdir(GO_EP1_ID, path)

        # remove all dirs with the prefix
        glob = "rm_dir{}-[012]".format(rand)
        output = self.run_line(
            "globus rm -r -F json {}:{}".format(GO_EP1_ID, glob))
        res = json.loads(output)
        self.assertEqual(res["status"], "SUCCEEDED")

        # confirm no dirs with the prefix exist on the endpoint
        filter_string = "name:~rm_dir{}*".format(rand)
        ls_doc = self.tc.operation_ls(GO_EP1_ID, filter=filter_string)
        for item in ls_doc:
            print item["name"]
            self.assertTrue(False)

    def test_timeout(self):
        """
        Attempts to remove a path we are not allowed to remove,
        confirms rm times out and exits 1 after given timeout.
        """
        timeout = 2
        path = "/share/godata/file1.txt"
        output = self.run_line(
            "globus rm -r --timeout {} {}:{}".format(timeout, GO_EP1_ID, path),
            assert_exit_code=1)
        self.assertIn(("Task has yet to complete "
                       "after {} seconds.".format(timeout)), output)

    def test_unsafe(self):
        """
        Attempts to remove an unsafe path, confirms API Error is raised
        """
        path = "/"
        output = self.run_line("globus rm -r {}:{}".format(GO_EP1_ID, path),
                               assert_exit_code=1)
        self.assertIn("Unsafe delete path", output)
