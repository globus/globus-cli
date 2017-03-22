import unittest
from click.testing import CliRunner
import shlex

from globus_cli import main
from globus_cli.config import (
    AUTH_RT_OPTNAME, AUTH_AT_OPTNAME, AUTH_AT_EXPIRES_OPTNAME,
    TRANSFER_RT_OPTNAME, TRANSFER_AT_OPTNAME, TRANSFER_AT_EXPIRES_OPTNAME,
    WHOAMI_ID_OPTNAME, WHOAMI_USERNAME_OPTNAME, WHOAMI_NAME_OPTNAME,
    WHOAMI_EMAIL_OPTNAME, get_config_obj)

from tests.framework.constants import (CLITESTER1A_TRANSFER_RT,
                                       CLITESTER1A_AUTH_RT)
from tests.framework.tools import get_user_data


def write_test_config(conf):
    """
    Writes known constants and refresh tokens into config for testing
    """
    user_data = get_user_data()["clitester1a"]
    testing_constants = {
        AUTH_RT_OPTNAME: CLITESTER1A_AUTH_RT,
        AUTH_AT_OPTNAME: "",
        AUTH_AT_EXPIRES_OPTNAME: 0,
        TRANSFER_RT_OPTNAME: CLITESTER1A_TRANSFER_RT,
        TRANSFER_AT_OPTNAME: "",
        TRANSFER_AT_EXPIRES_OPTNAME: 0,
        WHOAMI_ID_OPTNAME: user_data["id"],
        WHOAMI_USERNAME_OPTNAME: user_data["username"],
        WHOAMI_NAME_OPTNAME: user_data["name"],
        WHOAMI_EMAIL_OPTNAME: user_data["email"]
    }
    conf["cli"] = testing_constants
    conf.write()


class CliTestCase(unittest.TestCase):
    """
    A class of TestCases which test the CLI by making direct calls to the CLI
    and then testing the results. Uses testing refresh tokens to authorize
    calls, and wraps a click CliRunner for running commands.
    """
    def __init__(self, desc):
        unittest.TestCase.__init__(self, desc)
        self._runner = CliRunner()

    @classmethod
    def setUpClass(self):
        """
        Stores any existing config data in the cli environment of .globus.cfg
        Then replaces that data with known values for testing
        """
        self.conf = get_config_obj()
        try:
            self.stored_config = self.conf["cli"]
        except KeyError:
            self.stored_config = {}
        write_test_config(self.conf)

    @classmethod
    def tearDownClass(self):
        """
        Restores original values of the cli environment of .globus.cfg
        """
        self.conf["cli"] = self.stored_config
        self.conf.write()

    def run_line(self, line, assert_exit_code=0, batch_input=None):
        """
        Uses the CliRunner to run the given command line,
        Asserts that the exit_code is equal to the given value
        """
        # split line into args and confirm line starts with "globus"
        args = shlex.split(line)
        self.assertEqual(args[0], "globus")
        # run the line. globus_cli.main is the "globus" part of the line
        result = self._runner.invoke(main, args[1:], input=batch_input)
        # confirm expected exit_code and exception
        self.assertEqual(result.exit_code, assert_exit_code)
        # return the output for further testing
        return result.output

    def run_line_no_auth(self, line, assert_exit_code=0, batch_input=None):
        """
        Wrapper around run_line that wipes the cli environment of .globus.cfg
        Before running, then restores test values after run is complete.
        """
        # wipe cli environment
        self.conf["cli"] = {}
        self.conf.write()
        # run the line in blank environment
        ret = self.run_line(line, assert_exit_code=assert_exit_code,
                            batch_input=batch_input)
        # reset the test environment and return the result
        write_test_config(self.conf)
        return ret
