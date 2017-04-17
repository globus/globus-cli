import json

from tests.framework.cli_testcase import CliTestCase
from tests.framework.constants import GO_EP1_ID


class LsTests(CliTestCase):
    """
    Tests globus ls command
    """

    def test_path(self):
        """
        Does an ls on EP1:/, confirms expected results.
        """
        path = "/"
        output = self.run_line("globus ls {}:{}".format(GO_EP1_ID, path))

        expected = ["home/", "mnt/", "not shareable/", "share/"]
        for item in expected:
            self.assertIn(item, output)

    def test_recursive(self):
        """
        Does a recursive ls on EP1:/share/, confirms expected results
        """
        path = "/share/"
        output = self.run_line("globus ls -r {}:{}".format(GO_EP1_ID, path))

        expected = ["godata/",
                    "godata/file1.txt", "godata/file2.txt", "godata/file3.txt"]
        for item in expected:
            self.assertIn(item, output)

    def test_orderby(self):
        """
        Uses the Size field from long output as an argument to --orderby,
        confirms results in ascending order by size json field
        """
        path = "/"
        output = json.loads(self.run_line(
            "globus ls -F json --orderby Size {}:{}".format(GO_EP1_ID, path)))

        prev_size = 0
        for item in output["DATA"]:
            self.assertTrue(item["size"] >= prev_size)
            prev_size = item["size"]

    def test_pattern_globbing(self):
        """
        Does an ls on EP1:/share/godata/file*, confirms all 3 files listed
        """
        path = "/share/godata/file*"
        output = self.run_line("globus ls {}:{}".format(GO_EP1_ID, path))

        expected = ["file1.txt", "file2.txt", "file3.txt"]
        for item in expected:
            self.assertIn(item, output)

    def test_wildcard_globbing(self):
        """
        Does an ls on EP1:/share/godata/file?.txt, confirms all 3 files listed
        """
        path = "/share/godata/file?.txt"
        output = self.run_line("globus ls {}:{}".format(GO_EP1_ID, path))

        expected = ["file1.txt", "file2.txt", "file3.txt"]
        for item in expected:
            self.assertIn(item, output)

    def test_no_globbing(self):
        """
        Does an ls on EP1:~/* with --no-globbing,
        confirms exit 1 on error as no * dir exists
        """
        path = "~/*"
        output = self.run_line(
            "globus ls --no-globbing {}:{}".format(GO_EP1_ID, path),
            assert_exit_code=1)

        self.assertIn("ClientError.NotFound", output)
        self.assertIn("Directory '/~/%2A' not found", output)
