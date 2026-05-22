import pytest

from spindlet.keyword.arguments import MissingArgumentProviderError
from spindlet.keyword.runner.context import Context


class DataFactory:
    def get_data(self, key, *, ctx):
        return {
            "user.name": "panfeng",
            "user.profile": '{"level": 3}',
        }[key]


class DataDict:
    def get_value(self, key):
        return {
            "region.city": "Shanghai",
        }[key]


class Functions:
    def call(self, name, args, *, ctx):
        if name == "join":
            return "-".join(args)
        if name == "case_count":
            return len(ctx.variables["cases"])
        raise KeyError(name)


def build_context():
    context = Context()
    context.variables.update(
        {
            "user": {"id": 1001, "profile": '{"enabled": true}'},
            "cases": ["case-1", "case-2"],
        }
    )
    context.arg_providers.update(
        {
            "DF": DataFactory(),
            "DD": DataDict(),
            "FN": Functions(),
        }
    )
    return context


def test_parse_args_resolves_context_variables_and_enhanced_arguments():
    context = build_context()

    result = context.parse_args(
        {
            "user_id": "${user.id}",
            "factory_name": "${DF.user.name}",
            "city": "${DD.region.city}",
            "joined": "${FN.join('a', 'b')}",
            "count": "${FN.case_count()}",
            "profile": "${DF.user.profile.json()}",
            "user_profile": "${user.profile.json()}",
            "as_text": "${user.id.str()}",
            "plain": "hello ${user.id}",
            "nested": ["${DF.user.name}", ("${DD.region.city}",)],
        }
    )

    assert result == {
        "user_id": 1001,
        "factory_name": "panfeng",
        "city": "Shanghai",
        "joined": "a-b",
        "count": 2,
        "profile": {"level": 3},
        "user_profile": {"enabled": True},
        "as_text": "1001",
        "plain": "hello ${user.id}",
        "nested": ["panfeng", ("Shanghai",)],
    }


def test_parse_args_raises_when_enhanced_provider_is_missing():
    context = Context()

    with pytest.raises(MissingArgumentProviderError, match="Missing DF argument provider"):
        context.parse_args({"name": "${DF.user.name}"})
