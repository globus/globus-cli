# type: ignore
"""
A Flake8 Plugin for use in globus-cli
"""

import ast

CODEMAP = {
    "CLI001": "CLI001 import from globus_sdk module, defeats lazy importer",
    "CLI002": "CLI002 names in `requires_login` were out of sorted order",
}


class Plugin:
    name = "globus-cli-flake8"
    version = "0.0.1"

    # args to init determine plugin behavior. see:
    # https://flake8.pycqa.org/en/latest/internal/utils.html#flake8.utils.parameters_for
    def __init__(self, tree):
        self.tree = tree

    # Plugin.run() is how checks will run. For detail, see implementation of:
    # https://flake8.pycqa.org/en/latest/internal/checker.html#flake8.checker.FileChecker.run_ast_checks
    def run(self):
        visitor = CLIVisitor()
        visitor.visit(self.tree)
        for lineno, col, code in visitor.collect:
            yield lineno, col, CODEMAP[code], type(self)


class ErrorRecordingVisitor(ast.NodeVisitor):
    def __init__(self):
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
        if not node.decorator_list:
            return

        for decorator_call in node.decorator_list:
            if not isinstance(decorator_call, ast.Call):
                continue  # e.g. a Name node, for a decorator w/ no args
            if not isinstance(decorator_call.func, ast.Attribute):
                # a decorator which is not accessed as an attr
                # unlike `LoginManager.requires_login`
                continue
            if decorator_call.func.attr != "requires_login":
                continue  # wrong name
            self._check_requires_login_decorator(decorator_call)

    # a function call already identified as a decorator named "X.requires_login"
    def _check_requires_login_decorator(self, node):
        args = node.args
        if not all(isinstance(arg, ast.Constant) for arg in node.args):
            return
        arg_values = [x.value for x in args]
        if sorted(arg_values) != arg_values:
            self._record(node, "CLI002")
