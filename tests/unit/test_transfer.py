import json
import uuid

from tests.framework.constants import GO_EP1_ID, GO_EP2_ID
from tests.framework.cli_testcase import CliTestCase


class TransferTests(CliTestCase):
    """
    Tests --dry-runs of `globus transfer` to make sure the SDK is getting
    expected values. Relies on SDK to test live transfers to avoid fairly
    time intensive tests.
    """

    def check_option(self, option_string, key, expected,
                     data_key=False, batch_input=None):
        """
        Helper that runs `globus transfer --dry-run -F json` with the given
        option string appended, then checks that the given index of the
        output json has the given expected value.
        If data_key, key is assumed to be in the first DATA item.
        """
        line = ("globus transfer --dry-run -F json {} {}:/ {}:/"
                .format(option_string, GO_EP1_ID, GO_EP2_ID))
        output = self.run_line(line, batch_input=batch_input)
        json_output = json.loads(output)
        if data_key:
            self.assertEqual(json_output["DATA"][0][key], expected)
        else:
            self.assertEqual(json_output[key], expected)

    def check_error(self, option_string, batch_input=None):
        line = ("globus transfer --dry-run -F json {} "
                "{}:/source/path {}:/dest/path"
                .format(option_string, GO_EP1_ID, GO_EP2_ID))
        self.run_line(line, assert_exit_code=2, batch_input=batch_input)

    def test_deadline(self):
        """
        Confirms the --deadline option is being passed correctly
        Confirms invalid times and invalid formats are caught by the CLI
        """
        self.check_option("--deadline 0001-01-01", "deadline", "0001-01-01")
        self.check_error("--deadline tomorrow")
        self.check_error("--deadline 0000-00-00")

    def test_submission_id(self):
        """
        Confirms the --submission-id option is being passed correctly
        """
        sub_id = str(uuid.uuid1())
        self.check_option("--submission-id " + sub_id, "submission_id", sub_id)

    def test_recursive(self):
        """
        Confirms the --recursive option is being passed correctly,
        Confirms error if --recursive and --batch are both given
        """
        self.check_option("", "recursive", False, data_key=True)
        self.check_option("--recursive", "recursive", True, data_key=True)
        self.check_error("--recursive --batch")

    def test_batch_recursive(self):
        """
        Confirms --recursive usable per line of batch input
        """
        self.check_option("--batch", "recursive", False,
                          batch_input="/ /", data_key=True)
        self.check_option("--batch", "recursive", True,
                          batch_input="/ / --recursive", data_key=True)

    def test_symlink(self):
        """
        Confirms --symlink option is being passed correctly
        Confirms error if --batch and --symlink are both given
        Confirms error if --recursive and --symlink are both given
        """
        self.check_option("", "DATA_TYPE", "transfer_item", data_key=True)
        self.check_option(
            "--symlink", "DATA_TYPE", "transfer_symlink_item", data_key=True)
        self.check_error("--batch --symlink")
        self.check_error("--recursive --symlink")

    def test_batch_symlink(self):
        """
        Confirms --symlink usable per line of batch input
        Confirms error if --recursive and --symlink are both given
        """
        self.check_option("--batch", "DATA_TYPE", "transfer_item",
                          batch_input="/ /", data_key=True)
        self.check_option("--batch", "DATA_TYPE", "transfer_symlink_item",
                          batch_input="/ / --symlink", data_key=True)
        self.check_error("--batch", batch_input="/ / --symlink --recursive")

    def test_sync_level(self):
        """
        Confirms --sync-level option is being passed correctly
        Confirms choice limited to [exists|size|mtime|checksum]
        """
        for pair in [("exists", 0), ("size", 1),
                     ("mtime", 2), ("checksum", 3)]:
            self.check_option("--sync-level " + pair[0], "sync_level", pair[1])
        self.check_error("--sync-level invalid")

    def test_preserve_mtime(self):
        """
        Confirms --preserve-mtime option is being passed correctly
        """
        self.check_option("", "preserve_timestamp", False)
        self.check_option("--preserve-mtime", "preserve_timestamp", True)

    def test_verify_checksum(self):
        """
        Confirms --verify-checksum / --no-verify-checksum options are
        being passed correctly
        """
        self.check_option("", "verify_checksum", True)
        self.check_option("--verify-checksum", "verify_checksum", True)
        self.check_option("--no-verify-checksum", "verify_checksum", False)

    def test_encrypt(self):
        """
        Confirms --encrypt option is being passed correctly
        """
        self.check_option("", "encrypt_data", False)
        self.check_option("--encrypt", "encrypt_data", True)

    def test_delete(self):
        """
        Confirms --delete option is being passed correctly
        """
        self.check_option("", "delete_destination_extra", False)
        self.check_option("--delete", "delete_destination_extra", True)

    def test_recursive_symlinks(self):
        """
        Confirms the --recursive-symlinks option is passed correctly
        """
        for choice in ["ignore", "keep", "copy"]:
            self.check_option("--recursive-symlinks " + choice,
                              "recursive_symlinks", choice)

        self.check_option("", "recursive_symlinks", "ignore")
        self.check_error("--recursive-symlinks invalid")
