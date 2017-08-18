from tests.framework.cli_testcase import CliTestCase
from tests.framework.constants import GO_EP1_ID, GO_EP3_ID


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
        Confirms --recursive ls on EP1:/share/ finds file1.txt
        """
        output = self.run_line("globus ls -r {}:/share/".format(GO_EP1_ID))
        self.assertIn("file1.txt", output)

    def test_depth(self):
        """
        Confirms setting depth to 1 on a --recursive ls of EP1:/
        finds godata but not file1.txt
        """
        output = self.run_line(("globus ls -r --recursive-depth-limit 1 {}:/"
                                .format(GO_EP1_ID)))
        self.assertNotIn("file1.txt", output)

    def test_recursive_json(self):
        """
        Confirms -F json works with the RecursiveLsResponse
        """
        output = self.run_line(
            "globus ls -r -F json {}:/share".format(GO_EP1_ID))
        self.assertIn('"DATA":', output)
        self.assertIn('"name": "godata/file1.txt"', output)

    def test_long_symlink_formatting(self):
        """
        Confirms --long output of `globus ls` displays correct symlink info
        """
        # valid symlinks
        output = self.run_line(
            "globus ls -l {}:/share/symlinks/good".format(GO_EP3_ID))
        self.assertIn("file (symlink)", output)
        self.assertIn(u"file1.txt link \u2764 -> /share/godata/file1.txt",
                      output)

        # invalid symlinks
        output = self.run_line(
            "globus ls -l {}:/share/symlinks/bad".format(GO_EP3_ID))
        self.assertNotIn("file (symlink)", output)
        self.assertIn("link to nowhere -> /nowhere", output)

    def test_ignore_symlinks(self):
        """
        Confirms default behavior of `globus ls -r` does not follow symlinks
        """
        output = self.run_line(("globus ls -r {}:/share/symlinks/good"
                                .format(GO_EP3_ID)))
        self.assertNotIn(u"godata dir link \u265e/file1.txt", output)

    def test_follow_symlinks(self):
        """
        Confirms using `--follow-symlinks` correctly follows dir symlinks
        """
        output = self.run_line(("globus ls -r --follow-symlinks "
                                "{}:/share/symlinks/good".format(GO_EP3_ID)))
        self.assertIn(u"godata dir link \u265e/file1.txt", output)
