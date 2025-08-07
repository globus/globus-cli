import pytest

from .get_identities import GetIdentitiesMocker
from .userinfo import UserinfoMocker


@pytest.fixture
def get_identities_mocker():
    return GetIdentitiesMocker()


@pytest.fixture
def userinfo_mocker():
    return UserinfoMocker()
