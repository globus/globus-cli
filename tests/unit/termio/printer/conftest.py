import click
import pytest


@pytest.fixture
def click_context():
    def func(command: str = "cmd") -> click.Context:
        ctx = click.Context(click.Command(command), obj={"jmespath": "a.b."})
        return ctx

    return func
