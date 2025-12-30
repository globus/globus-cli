# type: ignore
"""
A Flake8 Plugin for use in globus-cli
"""

import ast

# this is the limit used for the length of shorthelp text
# 60 is the limit we see in the live application derived from the helptext formatter
_SHORTHELP_LENGTH_LIMIT = 60

CODEMAP = {
    "CLI001": "CLI001 import from globus_sdk module, defeats lazy importer",
    "CLI002": "CLI002 names in `requires_login` were out of sorted order",
    # these rules ensure that helptext styling is uniform
    "CLI003": "CLI003 single-line function docstring did not end in '.'",
    "CLI004": "CLI004 short_help string did not end in '.'",
    "CLI005": "CLI005 command function short_help too long",
    "CLI006": "CLI006 command function implicit short_help does not end in '.'",
    "CLI007": "CLI007 command function missing expected docstring",
    "CLI008": "CLI008 static field list contains duplicate fieldname",
}


class Plugin:
    name = "globus-cli-flake8"
    version = "0.0.1"

    # args to init determine plugin behavior. see:
    # https://flake8.pycqa.org/en/latest/internal/utils.html#flake8.utils.parameters_for
    def __init__(self, tree) -> None:
        self.tree = tree

    # Plugin.run() is how checks will run. For detail, see implementation of:
    # https://flake8.pycqa.org/en/latest/internal/checker.html#flake8.checker.FileChecker.run_ast_checks
    def run(self):
        visitor = CLIVisitor()
        visitor.visit(self.tree)
        for lineno, col, code in visitor.collect:
            yield lineno, col, CODEMAP[code], type(self)


class ErrorRecordingVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.collect = []

    def _record(self, node, code):
        self.collect.append((node.lineno, node.col_offset, code))


class CLIVisitor(ErrorRecordingVisitor):
    def visit_ImportFrom(self, node):  # a `from globus_sdk import ...` clause
        if node.module == "globus_sdk":
            self._record(node, "CLI001")

    # you can check how a FunctionDef with decorators is shaped by running something
    # like...
    #
    # print(
    #     ast.dump(
    #         ast.parse('''@frob.foo("bar", "baz")\ndef muddle(): return 1'''),
    #         indent=4
    #     )
    # )
    #
    # outputs:
    #
    # Module(
    #     body=[
    #         FunctionDef(
    #             name='muddle',
    #             args=arguments(
    #                 posonlyargs=[],
    #                 args=[],
    #                 kwonlyargs=[],
    #                 kw_defaults=[],
    #                 defaults=[]),
    #             body=[
    #                 Return(
    #                     value=Constant(value=1))],
    #             decorator_list=[
    #                 Call(
    #                     func=Attribute(
    #                         value=Name(id='frob', ctx=Load()),
    #                         attr='foo',
    #                         ctx=Load()),
    #                     args=[
    #                         Constant(value='bar'),
    #                         Constant(value='baz')],
    #                     keywords=[])])],
    #     type_ignores=[])
    def visit_FunctionDef(self, node):  # a function definition
        self._check_docstring_cli003(node)

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "command":
                self._check_command_docstring_implicit_shorthelp(node)
            elif isinstance(decorator, ast.Call):
                # only Name nodes can match `@command(...)` usage
                if isinstance(decorator.func, ast.Name):
                    keyword_args = [kw.arg for kw in decorator.keywords]
                    # limit ourselves to commands where the short_help will be derived
                    # from the function docstring
                    if (
                        decorator.func.id == "command"
                        and "short_help" not in keyword_args
                        # technically, `help=...` could also be parsed for implicit
                        # short_help but since we never use this style, simply skip
                        # it for now
                        and "help" not in keyword_args
                        # do not check on hidden commands
                        and "hidden" not in keyword_args
                    ):
                        self._check_command_docstring_implicit_shorthelp(node)
                # a decorator which is accessed as an attr
                # like `LoginManager.requires_login`
                elif isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "requires_login":
                        self._check_requires_login_decorator(decorator)

        self.generic_visit(node)

    def visit_Call(self, node):
        for keyword in node.keywords:
            if keyword.arg == "short_help":
                self._check_stringnode_explicit_short_help(keyword.value)
                break

    # a function call already identified as a decorator named "X.requires_login"
    def _check_requires_login_decorator(self, node):
        args = node.args
        if not all(isinstance(arg, ast.Constant) for arg in node.args):
            return
        arg_values = [x.value for x in args]
        if sorted(arg_values) != arg_values:
            self._record(node, "CLI002")

    def _check_docstring_cli003(self, node):
        docstring = ast.get_docstring(node)
        if not docstring:
            return
        if docstring.count("\n") != 0:
            return
        if not docstring.endswith("."):
            self._record(node.body[0], "CLI003")

    def _check_stringnode_explicit_short_help(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                if not node.value.endswith("."):
                    self._record(node, "CLI004")
                if len(node.value) > _SHORTHELP_LENGTH_LIMIT:
                    self._record(node, "CLI005")
        elif isinstance(node, ast.JoinedStr):
            last = node.values[-1]
            if (
                isinstance(last, ast.Constant)
                and isinstance(last.value, str)
                and not last.value.endswith(".")
            ):
                self._record(node, "CLI004")

    def _check_command_docstring_implicit_shorthelp(self, node):
        docstring = ast.get_docstring(node)
        if not docstring:
            self._record(node, "CLI007")
            return

        # click uses a more sophisticated technique than the one below
        # for the original, see:
        #   https://github.com/pallets/click/blob/14f735cf59618941cf2930e633eb77651b1dc7cb/src/click/utils.py#L59
        #
        # for our purposes, just take the first line
        firstline = docstring.split("\n")[0]
        if len(firstline) > _SHORTHELP_LENGTH_LIMIT:
            self._record(node.body[0], "CLI005")
        else:
            if not firstline.endswith("."):
                self._record(node.body[0], "CLI006")

    def visit_List(self, node):
        if self._is_list_of_fields(node):
            fieldname_map = {}
            for subnode in node.elts:
                # pull the first arg, and if we can't, skip this field
                # it means something is odd, but most likely we're linting code
                # in-progress, so we're seeing a list like the following:
                #
                #     [
                #         Field(),               # <-- ignore this!
                #         Field("foo", "foo"),
                #         Field("bar", "bar"),
                #         Field("baz", "baz"),
                #         Field("foo", "uh-oh),  # <-- catch this!
                #     ]
                field_args = subnode.args
                if not field_args:
                    continue

                # get arg0 for the field, but if it's not a constant, skip this field
                # this means it's dynamically computed, so ignore it but check the rest
                # of the fields
                # e.g., Field(name_func(), "...")
                arg0 = field_args[0]
                if not isinstance(arg0, ast.Constant):
                    continue

                # if it's not a string but is constant, it's *probably* invalid
                # just ignore it and check other fields
                # e.g., Field(1, "...")
                if not isinstance(arg0.value, str):
                    continue

                # for each discovered name, track a list of matching nodes
                name = arg0.value
                fieldname_map.setdefault(name, [])
                fieldname_map[name].append(subnode)

            # any name with multiple nodes is a failure
            # if we have a failure, record that failure *on* the repeats, not on the
            # parent list node
            # doing it this way gets a diagnostic on the *first* node, not only the
            # repeats
            for subnode_list in fieldname_map.values():
                if len(subnode_list) <= 1:
                    continue
                for subnode in subnode_list:
                    self._record(subnode, "CLI008")
        self.generic_visit(node)

    def _is_list_of_fields(self, node):
        # if the list is empty, say "no"
        if not node.elts:
            return False

        # search for any disproving example
        for elem in node.elts:
            if not isinstance(elem, ast.Call):
                return False
            if not isinstance(elem.func, ast.Name):
                return False
            if elem.func.id != "Field":
                return False

        return True
