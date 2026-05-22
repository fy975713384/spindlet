import pytest

from spindlet.keyword.core import CtxVarError, KeywordBase, KeywordDefinitionError, KeywordError, KeywordStore
from spindlet.keyword.core.exceptions import KeywordMethodError, KeywordNameError
from spindlet.keyword.core.meta import KeywordLibraryDuplicateError


class LibDemo(KeywordBase):
    def demo(self):
        """ demo keyword """

    def demo_echo(self, value):
        """ echo keyword """
        return value


class LibOther(KeywordBase):
    def other(self):
        """ other keyword """


class LibNested(KeywordBase):
    def __init__(self, env, logger=None, log_level="DEBUG", log_path=None):
        super(LibNested, self).__init__(env, logger, log_level, log_path)
        self.other = LibOther(env=env)

    def nested(self):
        """ nested keyword """


def test_keyword_base_uses_keyword_store():
    keyword = LibDemo(env="sit")

    assert isinstance(keyword.store, KeywordStore)

    keyword.store.save("user_id", 1001)

    assert keyword.store.variables["user_id"] == 1001


@pytest.mark.parametrize("env", [None, "", "  "])
def test_keyword_base_requires_non_empty_env(env):
    with pytest.raises(ValueError, match="env must be a non-empty string"):
        LibDemo(env=env)


def test_keyword_core_does_not_export_legacy_context():
    import spindlet.keyword.core as keyword_core

    assert not hasattr(keyword_core, "Context")


def test_keyword_core_errors_share_base_hierarchy():
    assert issubclass(CtxVarError, KeywordError)
    assert issubclass(KeywordLibraryDuplicateError, KeywordError)
    assert issubclass(KeywordNameError, KeywordMethodError)
    assert issubclass(KeywordMethodError, KeywordDefinitionError)


def test_keyword_libraries_can_be_instantiated_sequentially():
    demo = LibDemo(env="sit")
    other = LibOther(env="sit")

    assert isinstance(demo, LibDemo)
    assert isinstance(other, LibOther)
    assert demo is not other


def test_keyword_library_cannot_instantiate_another_library_during_construction():
    with pytest.raises(KeywordLibraryDuplicateError, match="nested keyword library instantiation is not allowed: <LibOther>"):
        LibNested(env="sit")


def test_keyword_method_parses_keyword_store_variables_in_kwargs():
    keyword = LibDemo(env="sit")
    keyword.store.save("user", {"name": "panfeng"})

    assert keyword.demo_echo(value="${user.name}") == "panfeng"
