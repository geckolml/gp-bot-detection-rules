"""Simulador basado en agentes de actividad de una plataforma social con chat
y geolocalización.

Genera tres tablas (users, messages, locations) con etiqueta conocida de bot.
Ver openspec/changes/add-behavior-simulator/ para la especificación.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Ciudades genéricas (lat, lon) usadas como "hogar" de los usuarios.
CITIES = np.array([
    (-12.05, -77.04), (-33.45, -70.67), (-34.60, -58.38), (4.71, -74.07),
    (19.43, -99.13), (40.42, -3.70), (41.39, 2.17), (48.86, 2.35),
    (51.51, -0.13), (52.52, 13.40), (40.71, -74.01), (34.05, -118.24),
    (25.76, -80.19), (-23.55, -46.63), (35.68, 139.69), (1.35, 103.82),
    (-33.87, 151.21), (55.76, 37.62), (30.04, 31.24), (6.52, 3.38),
])

BOT_SUFFIX = "_bot"

# Las frases comunes ("hola", "ok", "jaja") comparten template_id entre todos
# los usuarios. Rango separado del texto libre y de las plantillas de bots.
COMMON_PHRASE_BASE = 2_000_000_000


@dataclass
class Scenario:
    name: str
    seed: int
    counts: dict


def _users(counts: dict, params: dict, start: pd.Timestamp, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    uid = 0
    for agent_type, n in counts.items():
        p = params[agent_type]
        age_days = rng.exponential(p["account_age_days"], size=n)
        created = start - pd.to_timedelta(age_days * 86400, unit="s")
        for i in range(n):
            rows.append((uid, agent_type, agent_type.endswith(BOT_SUFFIX), created[i]))
            uid += 1
    users = pd.DataFrame(rows, columns=["user_id", "agent_type", "is_bot", "created_at"])
    users["created_at"] = users["created_at"].dt.floor("s")
    return users


def _sessions(p: dict, horizon_s: float, rng: np.random.Generator) -> np.ndarray:
    """Instantes de inicio de sesión (segundos desde el inicio) de un usuario."""
    shape = p["activity_gamma_shape"]
    multiplier = rng.gamma(shape, 1.0 / shape)  # media 1
    lam = p["sessions_per_day"] * (horizon_s / 86400) * multiplier
    n = rng.poisson(lam)
    return np.sort(rng.uniform(0, horizon_s, size=n))


def _text(uid: int, p: dict, n: int, n_common: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """template_id y longitud de n mensajes de un agente.

    Texto propio: libre (casi único) o plantillas del bot. Además, con
    probabilidad `common_phrase_prob`, el mensaje es una frase común de un
    vocabulario compartido con popularidad tipo Zipf, por lo que también los
    usuarios reales repiten mensajes.
    """
    if p["n_templates"] is None:
        template = rng.integers(10**7, 10**9, size=n)       # texto libre: casi único
        msg_len = np.maximum(1, rng.lognormal(np.log(p["msg_len_mean"]), 0.6, size=n)).astype(int)
    else:
        template = uid * 1000 + rng.integers(0, p["n_templates"], size=n)
        # La longitud depende de la plantilla (mensajes copiados tienen la misma longitud).
        msg_len = (p["msg_len_mean"] * 0.5 + (template * 7919) % p["msg_len_mean"]).astype(int)
    p_common = float(p.get("common_phrase_prob", 0.0))
    if p_common > 0 and n_common > 0:
        weights = 1.0 / np.arange(1, n_common + 1)
        phrase = rng.choice(n_common, size=n, p=weights / weights.sum())
        is_common = rng.random(n) < p_common
        template = np.where(is_common, COMMON_PHRASE_BASE + phrase, template)
        msg_len = np.where(is_common, 2 + (phrase * 7) % 14, msg_len)   # frases cortas
    return template, msg_len


def _messages_for_user(uid: int, p: dict, contacts: np.ndarray, horizon_s: float,
                       n_common: int, rng: np.random.Generator) -> tuple[list, np.ndarray]:
    starts = _sessions(p, horizon_s, rng)
    times, recips = [], []
    for s in starts:
        k = 1 + rng.poisson(max(p["msgs_per_session"] - 1, 0))
        t = s + np.cumsum(rng.exponential(p["gap_seconds"], size=k))
        t = t[t < horizon_s]
        times.append(t)
        recips.append(rng.choice(contacts, size=len(t)))
    if not times:
        return [], starts
    t = np.concatenate(times)
    r = np.concatenate(recips)
    n = len(t)
    has_link = rng.random(n) < p["link_prob"]
    template, msg_len = _text(uid, p, n, n_common, rng)
    rows = list(zip([uid] * n, r, t, has_link, msg_len, template))
    return rows, starts


def _locations_for_user(uid: int, p: dict, home: np.ndarray, session_starts: np.ndarray,
                        rng: np.random.Generator) -> list:
    rows = []
    for t in session_starts:
        if rng.random() < p["geo_jump_prob"]:
            lat, lon = CITIES[rng.integers(len(CITIES))]
        else:
            lat, lon = home
        lat += rng.normal(0, 0.02)
        lon += rng.normal(0, 0.02)
        rows.append((uid, t, lat, lon))
    return rows


def simulate(scenario: Scenario, config: dict) -> dict[str, pd.DataFrame]:
    """Genera las tablas users, messages y locations para un escenario."""
    rng = np.random.default_rng(scenario.seed)
    params = config["agent_types"]
    start = pd.Timestamp(config["start"])
    horizon_s = float(config["horizon_hours"]) * 3600
    n_common = int(config.get("n_common_phrases", 0))

    users = _users(scenario.counts, params, start, rng)
    legit_ids = users.loc[users.agent_type == "legit", "user_id"].to_numpy()
    if len(legit_ids) < 2:
        raise ValueError("Se necesitan al menos 2 usuarios legit como destinatarios.")

    msg_rows, loc_rows = [], []
    for uid, agent_type in zip(users.user_id, users.agent_type):
        p = params[agent_type]
        n_contacts = max(1, rng.poisson(p["contacts"]))
        pool = legit_ids[legit_ids != uid]
        contacts = rng.choice(pool, size=min(n_contacts, len(pool)), replace=False)
        rows, starts = _messages_for_user(uid, p, contacts, horizon_s, n_common, rng)
        msg_rows.extend(rows)
        home = CITIES[rng.integers(len(CITIES))]
        loc_rows.extend(_locations_for_user(uid, p, home, starts, rng))

    msgs = pd.DataFrame(msg_rows, columns=["sender_id", "recipient_id", "t", "has_link", "msg_len", "template_id"])
    msgs = pd.concat([msgs, _replies(msgs, users, config, horizon_s, rng)], ignore_index=True)

    msgs = msgs.sort_values(["t", "sender_id"], kind="stable").reset_index(drop=True)
    msgs.insert(0, "message_id", np.arange(len(msgs), dtype=np.int64))
    msgs["sent_at"] = (start + pd.to_timedelta(msgs.pop("t"), unit="s")).dt.floor("s")
    msgs = msgs[["message_id", "sender_id", "recipient_id", "sent_at", "has_link", "msg_len", "template_id"]]
    msgs = msgs.astype({"sender_id": "int64", "recipient_id": "int64", "has_link": "bool",
                        "msg_len": "int64", "template_id": "int64"})

    locs = pd.DataFrame(loc_rows, columns=["user_id", "t", "lat", "lon"])
    locs["recorded_at"] = (start + pd.to_timedelta(locs.pop("t"), unit="s")).dt.floor("s")
    locs = locs[["user_id", "recorded_at", "lat", "lon"]].astype({"user_id": "int64"})

    return {"users": users, "messages": msgs, "locations": locs}


def _replies(msgs: pd.DataFrame, users: pd.DataFrame, config: dict, horizon_s: float,
             rng: np.random.Generator) -> pd.DataFrame:
    """Usuarios reales responden al primer mensaje de cada remitente con una
    probabilidad que depende del tipo de remitente."""
    cols = ["sender_id", "recipient_id", "t", "has_link", "msg_len", "template_id"]
    if msgs.empty:
        return pd.DataFrame(columns=cols)
    params = config["agent_types"]
    first = msgs.sort_values("t").drop_duplicates(["sender_id", "recipient_id"])
    sender_type = users.set_index("user_id").loc[first.sender_id, "agent_type"].to_numpy()
    p_reply = np.array([params[a]["reply_prob_received"] for a in sender_type])
    first = first[rng.random(len(first)) < p_reply]

    legit = params["legit"]
    n_rep = 1 + rng.poisson(config["reply_msgs_mean"], size=len(first))
    idx = np.repeat(np.arange(len(first)), n_rep)
    base = first.t.to_numpy()[idx]
    delay = rng.exponential(config["reply_delay_minutes"] * 60, size=len(idx))
    t = base + delay
    keep = t < horizon_s
    template, msg_len = _text(-1, legit, len(idx), int(config.get("n_common_phrases", 0)), rng)
    out = pd.DataFrame({
        "sender_id": first.recipient_id.to_numpy()[idx],
        "recipient_id": first.sender_id.to_numpy()[idx],
        "t": t,
        "has_link": rng.random(len(idx)) < legit["link_prob"],
        "msg_len": msg_len,
        "template_id": template,
    })[keep]
    return out
