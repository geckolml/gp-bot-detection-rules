"""Specs: openspec/changes/add-behavior-simulator/specs/behavior-simulator/spec.md"""
import copy

import numpy as np
import pandas as pd
import pytest

from simulator.agents import Scenario, simulate
from simulator.simulate import get_scenario, load_config

CONFIG = load_config("simulator/config.yaml")


def small(name: str, factor: float = 0.1) -> Scenario:
    s = get_scenario(CONFIG, name)
    counts = {k: max(5, int(v * factor)) for k, v in s.counts.items()}
    return Scenario(name, s.seed, counts)


@pytest.fixture(scope="module")
def train():
    return simulate(small("train"), CONFIG)


@pytest.fixture(scope="module")
def test_tables():
    return simulate(small("test"), CONFIG)


def test_counts_and_labels(train):
    users = train["users"]
    expected = small("train").counts
    assert users.agent_type.value_counts().to_dict() == expected
    assert (users.is_bot == users.agent_type.str.endswith("_bot")).all()


def test_stealth_only_in_test(train, test_tables):
    assert "stealth_bot" not in set(train["users"].agent_type)
    assert "stealth_bot" in set(test_tables["users"].agent_type)


def test_reproducible():
    a = simulate(small("train", 0.05), CONFIG)
    b = simulate(small("train", 0.05), CONFIG)
    for k in a:
        pd.testing.assert_frame_equal(a[k], b[k])


def test_referential_integrity_and_time_order(train):
    users, msgs = train["users"], train["messages"]
    ids = set(users.user_id)
    assert set(msgs.sender_id) <= ids and set(msgs.recipient_id) <= ids
    assert (msgs.sender_id != msgs.recipient_id).all()
    created = users.set_index("user_id").created_at
    assert (msgs.sent_at.to_numpy() >= created.loc[msgs.sender_id].to_numpy()).all()


def test_message_rate_overlap():
    tables = simulate(get_scenario(CONFIG, "train"), CONFIG)
    users, msgs = tables["users"], tables["messages"]
    per_user = msgs.groupby("sender_id").size().reindex(users.user_id, fill_value=0).to_numpy()
    def iqr(t):
        v = per_user[(users.agent_type == t).to_numpy()]
        return np.percentile(v, 25), np.percentile(v, 75)
    (l1, h1), (l2, h2) = iqr("legit"), iqr("adaptive_bot")
    assert l1 <= h2 and l2 <= h1, "los rangos intercuartílicos deben intersectarse"


def test_parquet_roundtrip(tmp_path, train):
    pytest.importorskip("pyarrow")
    from simulator.simulate import write_scenario
    write_scenario(train, tmp_path)
    for name in ("users", "messages", "locations"):
        assert (tmp_path / f"{name}.parquet").exists()


def test_legit_users_repeat_messages(train):
    """Spec: Mensajes repetidos en todos los tipos de agente. Si los usuarios
    reales nunca repitieran, `dup_template_ratio > 0` separaría las clases sin
    falsos positivos y el problema sería trivial."""
    users, msgs = train["users"], train["messages"]
    legit = set(users.loc[users.agent_type == "legit", "user_id"])
    m = msgs[msgs.sender_id.isin(legit)]
    windows = m.groupby(["sender_id", m.sent_at.dt.floor("h")]).template_id.agg(["size", "nunique"])
    repeated = (windows["nunique"] < windows["size"]).mean()
    assert repeated > 0.02, f"solo {repeated:.2%} de las ventanas de legit tiene mensajes repetidos"


def test_common_phrases_follow_agent_probability(train):
    from simulator.agents import COMMON_PHRASE_BASE
    users, msgs = train["users"], train["messages"]
    agent = users.set_index("user_id").agent_type
    assert CONFIG["agent_types"]["naive_bot"]["common_phrase_prob"] == 0
    is_common = msgs.template_id >= COMMON_PHRASE_BASE
    by_type = is_common.groupby(agent.loc[msgs.sender_id].to_numpy()).mean()
    assert by_type["naive_bot"] == 0
    assert by_type["legit"] == pytest.approx(CONFIG["agent_types"]["legit"]["common_phrase_prob"], abs=0.03)
