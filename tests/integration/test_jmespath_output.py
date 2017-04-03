import json
import logging

from tests.framework.constants import GO_EP1_ID, GO_EP2_ID
from tests.framework.cli_testcase import CliTestCase

log = logging.getLogger(__name__)


class JMESPathTests(CliTestCase):
    """
    Tests bookmark commands
    """
    def test_jmespath_noop(self):
        """
        Runs some simple fetch operations and confirms that `--jmespath '@'`
        doesn't change the output (but also that it overrides --format TEXT)
        """
        output = self.run_line(
            "globus endpoint show {} -Fjson".format(GO_EP1_ID))
        jmespathoutput = self.run_line(
            "globus endpoint show {} -Ftext --jmespath '@'".format(GO_EP1_ID))
        self.assertEquals(output, jmespathoutput)

    def test_jmespath_extract_from_list(self):
        """
        Uses jmespath to extract a value from a list result using a filter.
        Confirms that the result is identical to a direct fetch of that
        resource.
        """
        self.maxDiff = None
        # list tutorial endpoints with a search, but extract go#ep2
        output = self.run_line(
            ("globus endpoint search 'Tutorial' "
             "--filter-owner-id go@globusid.org "
             "--jmespath 'DATA[?id==`{}`] | [0]'").format(GO_EP2_ID))
        outputdict = json.loads(output)

        show_output = self.run_line(
            "globus endpoint show {} -Fjson".format(GO_EP2_ID))
        showdict = json.loads(show_output)

        # check specific keys because search includes `_rank` and doesn't
        # include the server list
        # just a random selection of "probably stable" values for this test
        for k in ('id', 'display_name', 'owner_id', 'subscription_id'):
            self.assertEquals(outputdict[k], showdict[k])

    def test_jmespath_no_expression_error(self):
        """
        Intentionally misuse `--jmespath` with no provided expression. Confirm
        that it gives a usage error.
        """
        output = self.run_line("globus endpoint search 'Tutorial' --jmespath",
                               assert_exit_code=2)
        self.assertIn('Error: --jmespath option requires an argument', output)

        # and the error says `--jq` if you use the `--jq` form
        output = self.run_line("globus endpoint search 'Tutorial' --jq",
                               assert_exit_code=2)
        self.assertIn('Error: --jq option requires an argument', output)

    def test_jmespath_invalid_expression_error(self):
        """
        Intentionally misuse `--jmespath` with a malformed expression. Confirm
        that it gives a JMESPath ParseError.
        """
        output = self.run_line(("globus endpoint search 'Tutorial' "
                                "--jmespath '{}'"),
                               assert_exit_code=1)
        self.assertIn('ParseError:', output)
