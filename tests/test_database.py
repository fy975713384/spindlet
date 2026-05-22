import pytest
from pydantic import ValidationError
from spindlet.database.engine import _DBOptions


@pytest.mark.parametrize('host,port,user,username,password,database', [
    # host is required
    (None, 3306, 'user', None, 'password', 'db'),
    ('', 3306, 'user', None, 'password', 'db'),
    # one of user/username must be provided
    ('1.1.1.1', 3306, '', None, 'password', 'db'),
    ('1.1.1.1', 3306, None, None, 'password', 'db'),
    # others
    (None, None, None, None, None, None),
    ('1.1.1.1', None, '', None, None, None),
    ('1.1.1.1', None, None, None, None, None),
    ('1.1.1.1', None, 'user', None, None, None),
])
def test_db_options_failure(host, port, user, username, password, database):
    try:
        _DBOptions(host=host, port=port, user=user, username=username,
                   password=password, database=database)
    except ValidationError:
        assert True
    else:
        assert False


@pytest.mark.parametrize('host,port,user,username,password,database', [
    ("1.1.1.1", 3306, 'user', None, 'password', None),
    ("1.1.1.1", 3306, None, 'user', 'password', None),
    ("1.1.1.1", 3306, None, 'user', 'password', 'db'),
    ("db.example.com", 3306, 'user', None, 'password', 'db'),
])
def test_db_options_success(host, port, user, username, password, database):
    try:
        _DBOptions(host=host, port=port, user=user, username=username,
                   password=password, database=database)
    except ValidationError:
        assert False
    else:
        assert True
