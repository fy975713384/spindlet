import pytest
from pydantic import ValidationError
from spindlet.database.engine import _DBOptions


@pytest.mark.parametrize('ip,host,port,user,username,password,database', [
    # one of ip/host must be provided
    ("", None, 3306, 'user', None, 'password', 'db'),
    # one of user/username must be provided
    ("1.1.1.1", None, 3306, '', None, 'password', 'db'),
    # ip valid
    ('1.1.1.1.1', None, None, None, None, None, None),
    ("1.1.1", None, 3306, 'user', None, 'password', None),
    # others
    (None, None, None, None, None, None, None),
    (None, '1.1.1.1', '', None, None, None, None),
    (None, '1.1.1.1', None, '', None, None, None),
    (None, '1.1.1.1', None, 'user', None, None, None),
])
def test_db_options_failure(ip, host, port, user, username, password, database):
    try:
        _DBOptions(ip=ip, host=host, port=port, user=user, username=username,
                   password=password, database=database)
    except ValidationError:
        assert True
    else:
        assert False


@pytest.mark.parametrize('ip,host,port,user,username,password,database', [
    ("1.1.1.1", None, 3306, 'user', None, 'password', None),
    (None, "1.1.1.1", 3306, None, 'user', 'password', None),
    (None, "1.1.1.1", 3306, None, 'user', 'password', 'db'),
])
def test_db_options_success(ip, host, port, user, username, password, database):
    try:
        _DBOptions(ip=ip, host=host, port=port, user=user, username=username,
                   password=password, database=database)
    except ValidationError:
        assert False
    else:
        assert True
