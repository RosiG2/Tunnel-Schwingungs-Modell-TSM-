#!/usr/bin/env python3
"""TSM compact operations runner v7.2.

Standard-library-only reference runner for the active TSM corpus package.
It is a synthetic/numerical work runner, not empirical validation and not a
physical end model.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
import random
import re
import statistics
import sys
import unicodedata
from datetime import datetime, timezone
from collections import deque


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(*objects: Any) -> str:
    payload = "\n".join(
        json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for o in objects
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(d: dict, dotted_path: str):
    current = d
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Missing required operations field: {dotted_path}")
        current = current[part]
    return current


def parse_bool(value: str | bool | None) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def analyze_core(path: Path, profile: dict) -> dict:
    rows = read_rows(path)
    epsr = float(profile["numeric"]["epsilon_rad"])
    ids: set[str] = set()
    qeff_values: list[float] = []
    plv_values: list[float] = []
    signed_raw_values: list[float] = []
    max_f_error = 0.0
    max_qeff_error = 0.0
    max_plv_error = 0.0
    max_signed_raw_error = 0.0
    zone_counts_baseline: dict[str, int] = {}
    zone_counts_recommended: dict[str, int] = {}

    for row in rows:
        rid = row["record_id"]
        if rid in ids:
            raise ValueError(f"Duplicate record_id: {rid}")
        ids.add(rid)
        C = float(row["C"])
        tau = float(row["tau_eff"])
        dphi = float(row["dphi_rad"])
        calc_f = C * tau / max(abs(dphi), epsr)
        max_f_error = max(max_f_error, abs(calc_f - float(row["F_res"])))

        qeff = tau / max(abs(dphi), epsr)
        plv = abs(math.cos(dphi))
        signed_raw = qeff * math.cos(dphi)
        qeff_values.append(qeff)
        plv_values.append(plv)
        signed_raw_values.append(signed_raw)
        max_qeff_error = max(max_qeff_error, abs(qeff - float(row["R_Qeff_raw"])))
        max_plv_error = max(max_plv_error, abs(plv - float(row["R_PLV"])))
        max_signed_raw_error = max(
            max_signed_raw_error,
            abs(signed_raw - float(row["R_combo_signed_raw"])),
        )
        bz = row["baseline_zone3"]
        rz = row["recommended_zone3"]
        zone_counts_baseline[bz] = zone_counts_baseline.get(bz, 0) + 1
        zone_counts_recommended[rz] = zone_counts_recommended.get(rz, 0) + 1

    raw_values = [q * p for q, p in zip(qeff_values, plv_values)]
    raw_min = min(raw_values)
    raw_max = max(raw_values)
    signed_abs_max = max(abs(v) for v in signed_raw_values)
    max_norm_error = 0.0
    max_qc_error = 0.0
    max_signed_unit_error = 0.0

    for row, raw, signed_raw in zip(rows, raw_values, signed_raw_values):
        norm = 0.0 if raw_max == raw_min else (raw - raw_min) / (raw_max - raw_min)
        max_norm_error = max(max_norm_error, abs(norm - float(row["R_combo_norm"])))
        max_qc_error = max(max_qc_error, abs(clamp(norm, 0.0, 1.0) - float(row["Q_c"])))
        signed_unit = signed_raw / signed_abs_max
        max_signed_unit_error = max(
            max_signed_unit_error,
            abs(signed_unit - float(row["R_combo_signed_unit"])),
        )

    passed = (
        len(rows) == 10000
        and len(ids) == 10000
        and max_f_error < 1e-12
        and max_qeff_error < 1e-12
        and max_plv_error < 1e-12
        and max_norm_error < 1e-12
        and max_qc_error < 1e-12
        and max_signed_raw_error < 1e-12
        and max_signed_unit_error < 1e-12
    )
    return {
        "rows": len(rows),
        "unique_ids": len(ids),
        "max_abs_errors": {
            "F_res": max_f_error,
            "R_Qeff_raw": max_qeff_error,
            "R_PLV": max_plv_error,
            "R_combo_norm": max_norm_error,
            "Q_c": max_qc_error,
            "R_combo_signed_raw": max_signed_raw_error,
            "R_combo_signed_unit": max_signed_unit_error,
        },
        "zone_counts_baseline": zone_counts_baseline,
        "zone_counts_recommended": zone_counts_recommended,
        "passed": passed,
    }


def sigmoid(z: float) -> float:
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def wrap_angle(x: float) -> float:
    y = (x + math.pi) % (2 * math.pi) - math.pi
    return math.pi if y == -math.pi else y


@dataclass
class State:
    tau: float
    x: list[float]
    v: list[float]
    eps: float
    phi: float


class RegimeTracker:
    def __init__(self, cfg: dict):
        self.K_hi = float(cfg["K_hi"])
        self.F_lo = float(cfg["F_lo"])
        self.h = float(cfg["Kdot_hysteresis"])
        self.n = int(cfg["N_dwell"])
        self.current = None
        self.dwell = 0
        self.start = 0
        self.entries: list[dict] = []

    def propose(self, K: float, Kdot: float) -> str:
        if K >= self.K_hi and Kdot >= self.h:
            return "K+"
        if K >= self.K_hi:
            return "K"
        if K <= self.F_lo and Kdot <= -self.h:
            return "F+"
        if K <= self.F_lo:
            return "F"
        return "R↑" if Kdot > 0 else "R↓"

    def step(self, i: int, K: float, Kdot: float) -> str:
        proposed = self.propose(K, Kdot)
        if self.current is None:
            self.current = proposed
            self.dwell = 1
            self.start = i
        elif proposed == self.current:
            self.dwell += 1
        elif self.dwell >= self.n:
            self.entries.append({
                "sim_regime": self.current,
                "start_step": self.start,
                "end_step": i - 1,
                "dwell": self.dwell,
                "gate_id": "G-SIM-REGIME",
            })
            self.current = proposed
            self.dwell = 1
            self.start = i
        else:
            self.dwell += 1
        return self.current

    def finish(self, last: int):
        if self.current is not None:
            self.entries.append({
                "sim_regime": self.current,
                "start_step": self.start,
                "end_step": last,
                "dwell": self.dwell,
                "gate_id": "G-SIM-REGIME",
            })


def K_grad(x: list[float], phi: float, cfg: dict) -> tuple[float, list[float]]:
    z = (
        float(cfg["kappa"])
        * dot([x[i] - cfg["xi_center"][i] for i in range(3)], cfg["xi_k"])
        + float(cfg["gamma0"])
        + float(cfg["gamma1"]) * math.cos(phi)
    )
    K = sigmoid(z)
    factor = K * (1.0 - K) * float(cfg["kappa"])
    return K, [factor * q for q in cfg["xi_k"]]


def diagnostics(tau: float, phi: float, K: float, profile: dict) -> dict:
    epsr = float(profile["numeric"]["epsilon_rad"])
    qeff = tau / max(abs(phi), epsr)
    plv = abs(math.cos(phi))
    raw = qeff * plv
    unit = raw / (1.0 + raw)
    qc = clamp(unit, 0.0, 1.0)
    adaptive = profile["simulation"]["adaptive_lambda"]
    lam = float(profile["simulation"]["lambda_base"]) * (
        float(adaptive["min_rel"])
        + (float(adaptive["max_rel"]) - float(adaptive["min_rel"]))
        * (1.0 - unit)
        * plv
    )
    cycles = tau / (2.0 * math.pi) if tau >= 0 else 0.0
    qpre = (
        abs(phi) <= math.radians(3)
        and plv >= math.cos(math.radians(3))
        and cycles >= 3
    )
    q = K >= 0.9 and abs(phi) <= epsr and plv >= math.cos(epsr) and qc >= 0.8
    qplus = (
        K >= 0.92
        and abs(phi) <= math.radians(0.5)
        and plv >= math.cos(math.radians(0.5))
        and qc >= 0.85
    )
    anti = abs(phi) <= 0.1 and plv >= 0.6
    if anti:
        anti_type = "A1" if unit >= 0.66 else "A3" if unit >= 0.33 else "A4"
    else:
        anti_type = "A2"
    return {
        "Q_eff": qeff,
        "PLV_tau": plv,
        "R_combo_raw": raw,
        "R_combo_unit": unit,
        "Q_c": qc,
        "lambda_eff": lam,
        "Q_pre": qpre,
        "Q": q,
        "Qplus": qplus,
        "anti_gate": anti,
        "anti_type": anti_type,
        "anti_score": unit,
        "cosonance_detected": abs(phi) <= 0.15 and plv >= 0.6 and cycles >= 3,
        "cosonance_reportable": abs(phi) <= epsr,
        "F_phase_status": "not_evaluable_missing_independent_tau_lock",
    }


def deriv(state: State, profile: dict):
    cfg = profile["simulation"]
    K, grad = K_grad(state.x, state.phi, cfg)
    diag = diagnostics(state.tau, state.phi, K, profile)
    dx = list(state.v)
    dv = [
        -float(cfg["alpha"]) * grad[i] - float(cfg["delta"]) * state.v[i]
        for i in range(3)
    ]
    deps = -diag["lambda_eff"] * K * state.eps
    dphi = float(cfg["omega_phi"])
    return dx, dv, deps, dphi


def add_state(state: State, k, h: float) -> State:
    dx, dv, de, dp = k
    return State(
        state.tau + h,
        [state.x[i] + h * dx[i] for i in range(3)],
        [state.v[i] + h * dv[i] for i in range(3)],
        state.eps + h * de,
        wrap_angle(state.phi + h * dp),
    )


def rk4(state: State, h: float, profile: dict) -> State:
    k1 = deriv(state, profile)
    k2 = deriv(add_state(state, k1, h / 2.0), profile)
    k3 = deriv(add_state(state, k2, h / 2.0), profile)
    k4 = deriv(add_state(state, k3, h), profile)

    def combine(a, b, c, d):
        return (a + 2 * b + 2 * c + d) / 6.0

    dx = [combine(k1[0][i], k2[0][i], k3[0][i], k4[0][i]) for i in range(3)]
    dv = [combine(k1[1][i], k2[1][i], k3[1][i], k4[1][i]) for i in range(3)]
    de = combine(k1[2], k2[2], k3[2], k4[2])
    dp = combine(k1[3], k2[3], k3[3], k4[3])
    return State(
        state.tau + h,
        [state.x[i] + h * dx[i] for i in range(3)],
        [state.v[i] + h * dv[i] for i in range(3)],
        state.eps + h * de,
        wrap_angle(state.phi + h * dp),
    )


def simulate(profile: dict, out: Path, dt: float | None = None, steps: int | None = None):
    cfg = profile["simulation"]
    dt = float(dt if dt is not None else cfg["dtau"])
    steps = int(steps if steps is not None else cfg["steps"])
    random.seed(int(cfg["seed"]))
    x = [float(v) + (random.random() - 0.5) * 0.01 for v in cfg["x_star"]]
    state = State(0.0, x, [0.0, 0.0, 0.0], 1.0, 0.0)
    tracker = RegimeTracker(cfg["regime"])
    rows = []
    previous_K = None

    for i in range(steps):
        K, _ = K_grad(state.x, state.phi, cfg)
        Kdot = 0.0 if previous_K is None else (K - previous_K) / dt
        regime = tracker.step(i, K, Kdot)
        diag = diagnostics(state.tau, state.phi, K, profile)
        row = {
            "record_id": f"SIM-{i + 1:06d}",
            "record_type": "simulation_output",
            "step": i,
            "tau": state.tau,
            "x0": state.x[0],
            "x1": state.x[1],
            "x2": state.x[2],
            "v0": state.v[0],
            "v1": state.v[1],
            "v2": state.v[2],
            "K": K,
            "Kdot": Kdot,
            "eps": state.eps,
            "dphi_rad": state.phi,
            "sim_regime": regime,
            **diag,
        }
        rows.append(row)
        finite_values = [*state.x, *state.v, state.eps, state.phi, K]
        if not all(math.isfinite(float(v)) for v in finite_values):
            raise FloatingPointError(f"Non-finite state at step {i}")
        previous_K = K
        state = rk4(state, dt, profile)

    tracker.finish(steps - 1)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "trajectory.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (out / "regimes.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["sim_regime", "start_step", "end_step", "dwell", "gate_id"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(tracker.entries)
    summary = {
        "n": len(rows),
        "dtau": dt,
        "duration": dt * steps,
        "K_mean": statistics.fmean(float(r["K"]) for r in rows),
        "K_final": rows[-1]["K"],
        "eps_final": rows[-1]["eps"],
        "max_abs_Kdot": max(abs(float(r["Kdot"])) for r in rows),
    }
    return rows, summary


def stabcheck(profile: dict, out: Path) -> dict:
    cfg = profile["simulation"]
    base_dt = float(cfg["dtau"])
    duration = base_dt * int(cfg["steps"])
    runs = []
    for factor in [1.0, 0.5, 0.25]:
        dt = base_dt * factor
        steps = round(duration / dt)
        _, summary = simulate(profile, out / f"dt_{dt:g}", dt, steps)
        runs.append(summary)
    reference = runs[-1]
    comparisons = []
    for summary in runs[:-1]:
        comparisons.append({
            "dtau": summary["dtau"],
            "rel_K_final": abs(summary["K_final"] - reference["K_final"])
            / max(abs(reference["K_final"]), 1e-12),
            "rel_K_mean": abs(summary["K_mean"] - reference["K_mean"])
            / max(abs(reference["K_mean"]), 1e-12),
            "rel_eps_final": abs(summary["eps_final"] - reference["eps_final"])
            / max(abs(reference["eps_final"]), 1e-12),
        })
    passed = all(
        max(c["rel_K_final"], c["rel_K_mean"], c["rel_eps_final"]) <= 0.01
        for c in comparisons
    )
    report = {
        "method": "same physical duration; RK4; dt, dt/2, dt/4",
        "tolerance_relative": 0.01,
        "runs": runs,
        "comparisons_to_dt_quarter": comparisons,
        "passed": passed,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "stability_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report



def write_rows(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_float(row: dict, field: str) -> float | None:
    value = row.get(field)
    if value is None or str(value).strip() == "":
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def as_text(row: dict, field: str) -> str | None:
    value = row.get(field)
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def derive_rrr(
    rows: list[dict],
    profile: dict,
    dphi_field: str = "dphi_rad",
    tau_field: str = "tau",
) -> list[dict]:
    epsr = float(profile["numeric"]["epsilon_rad"])
    work = []
    raws = []
    signed_raws = []
    for source in rows:
        row = dict(source)
        dphi = as_float(row, dphi_field)
        tau = as_float(row, tau_field)
        if dphi is None or tau is None:
            row["RRR_status"] = "not_evaluable_missing_dphi_or_tau"
            work.append((row, None, None, None, None))
            continue
        qeff = tau / max(abs(dphi), epsr)
        plv = abs(math.cos(dphi))
        raw = qeff * plv
        signed_raw = qeff * math.cos(dphi)
        raws.append(raw)
        signed_raws.append(signed_raw)
        work.append((row, qeff, plv, raw, signed_raw))
    raw_min = min(raws) if raws else 0.0
    raw_max = max(raws) if raws else 0.0
    signed_scale = max((abs(v) for v in signed_raws), default=0.0)
    output = []
    for row, qeff, plv, raw, signed_raw in work:
        if raw is None:
            output.append(row)
            continue
        norm = 0.0 if raw_max == raw_min else (raw - raw_min) / (raw_max - raw_min)
        row.update({
            "R_Qeff_raw": qeff,
            "R_PLV": plv,
            "R_combo_raw": raw,
            "R_combo_norm": norm,
            "Q_c": clamp(norm, 0.0, 1.0),
            "R_PLV_signed": math.cos(as_float(row, dphi_field)),
            "R_combo_signed_raw": signed_raw,
            "R_combo_signed_unit": 0.0 if signed_scale == 0 else signed_raw / signed_scale,
            "RRR_status": "evaluated",
        })
        output.append(row)
    return output


def annotate_rows(
    rows: list[dict],
    profile: dict,
    c_field: str,
    dphi_field: str,
    tau_field: str,
    tau_lock_field: str,
) -> list[dict]:
    derived = derive_rrr(rows, profile, dphi_field=dphi_field, tau_field=tau_field)
    epsr = float(profile["numeric"]["epsilon_rad"])
    fcfg = profile["operations"]["f_phase"]
    previous_qhat = None
    output = []
    for row in derived:
        C = as_float(row, c_field)
        dphi = as_float(row, dphi_field)
        tau = as_float(row, tau_field)
        raw = as_float(row, "R_combo_raw")
        plv = as_float(row, "R_PLV")
        qc = as_float(row, "Q_c")
        cycles = as_float(row, "cycles")
        if cycles is None and tau is not None:
            cycles = tau / (2.0 * math.pi)
        qhat = None if raw is None else raw / (1.0 + raw)
        slope = None if qhat is None or previous_qhat is None else qhat - previous_qhat
        if qhat is not None:
            previous_qhat = qhat
        try:
            tau_lock = parse_bool(row.get(tau_lock_field))
        except ValueError:
            tau_lock = None
            row["tau_lock_parse_status"] = "invalid_boolean"
        row["Qhat"] = qhat
        row["Qhat_slope"] = slope
        row["PLV_tau"] = plv
        row["cycles"] = cycles
        row["tau_lock"] = tau_lock
        if dphi is None or plv is None or cycles is None:
            row["Q_pre_status"] = "not_evaluable"
            row["Q_pre"] = ""
        else:
            row["Q_pre"] = (
                abs(dphi) <= math.radians(3)
                and plv >= math.cos(math.radians(3))
                and cycles >= 3
            )
            row["Q_pre_status"] = "evaluated"
        if C is None or dphi is None or plv is None or qc is None:
            row["Q_status"] = "not_evaluable"
            row["Q"] = ""
            row["Qplus"] = ""
        else:
            row["Q"] = C >= 0.9 and abs(dphi) <= epsr and plv >= math.cos(epsr) and qc >= 0.8
            row["Qplus"] = (
                C >= 0.92
                and abs(dphi) <= math.radians(0.5)
                and plv >= math.cos(math.radians(0.5))
                and qc >= 0.85
            )
            row["Q_status"] = "evaluated"
        if dphi is None or plv is None:
            row["anti_status"] = "not_evaluable"
            row["anti_gate"] = ""
            row["cosonance_detected"] = ""
            row["cosonance_reportable"] = ""
        else:
            row["anti_gate"] = abs(dphi) <= 0.1 and plv >= 0.6
            row["anti_status"] = "evaluated"
            row["cosonance_detected"] = (
                abs(dphi) <= 0.15 and plv >= 0.6 and cycles is not None and cycles >= 3
            )
            row["cosonance_reportable"] = abs(dphi) <= epsr
        if tau_lock is None:
            row["F_event"] = ""
            row["F_phase_status"] = "not_evaluable_missing_tau_lock"
        elif None in (C, dphi, qhat, slope):
            row["F_event"] = ""
            row["F_phase_status"] = "not_evaluable_missing_numeric_inputs"
        else:
            event = (
                C < float(fcfg["C_max_exclusive"])
                and abs(dphi) >= float(fcfg["dphi_abs_min_rad"])
                and float(fcfg["Qhat_window"][0]) <= qhat <= float(fcfg["Qhat_window"][1])
                and slope < float(fcfg["Qhat_slope_max_exclusive"])
                and tau_lock is True
            )
            row["F_event"] = event
            row["F_phase_status"] = "event" if event else "no_event"
        pext = as_float(row, "P_ext_frac")
        if pext is None or dphi is None or tau_lock is None:
            row["autoresonance_ok"] = ""
            row["autoresonance_status"] = "not_evaluable_missing_inputs"
        else:
            ok = pext <= 0.01 and abs(dphi) <= epsr and tau_lock is True
            row["autoresonance_ok"] = ok
            row["autoresonance_status"] = "PASS" if ok else "FAIL"
        output.append(row)
    return output


def fphase_rows(
    rows: list[dict],
    profile: dict,
    c_field: str,
    dphi_field: str,
    qhat_field: str,
    tau_lock_field: str,
) -> list[dict]:
    cfg = profile["operations"]["f_phase"]
    output = []
    previous = None
    for source in rows:
        row = dict(source)
        C = as_float(row, c_field)
        dphi = as_float(row, dphi_field)
        qhat = as_float(row, qhat_field)
        slope = as_float(row, "Qhat_slope")
        if slope is None and qhat is not None and previous is not None:
            slope = qhat - previous
        if qhat is not None:
            previous = qhat
        try:
            lock = parse_bool(row.get(tau_lock_field))
        except ValueError:
            lock = None
        row["Qhat_slope"] = slope
        row["tau_lock"] = lock
        if lock is None:
            row["F_event"] = ""
            row["F_phase_status"] = "not_evaluable_missing_tau_lock"
        elif None in (C, dphi, qhat, slope):
            row["F_event"] = ""
            row["F_phase_status"] = "not_evaluable_missing_numeric_inputs"
        else:
            event = (
                C < float(cfg["C_max_exclusive"])
                and abs(dphi) >= float(cfg["dphi_abs_min_rad"])
                and float(cfg["Qhat_window"][0]) <= qhat <= float(cfg["Qhat_window"][1])
                and slope < float(cfg["Qhat_slope_max_exclusive"])
                and lock is True
            )
            row["F_event"] = event
            row["F_phase_status"] = "event" if event else "no_event"
        output.append(row)
    return output


def _zone_family(zone: str | None) -> str | None:
    if not zone:
        return None
    if zone in {"K", "K+", "kohärent"}:
        return "K+" if zone == "K+" else "K"
    if zone in {"R", "R↑", "R↓", "regulativ"}:
        return "R"
    if zone in {"F", "F+", "fragmentiert"}:
        return "F"
    return None


def cfdr_class(value: float, classes: list[dict]) -> str:
    for item in classes:
        lo = float(item["min"])
        hi = float(item["max"])
        if item["label"] == "A":
            if lo <= value <= hi:
                return item["label"]
        elif lo <= value < hi:
            return item["label"]
    return "E"


def kn_ceff_rows(rows: list[dict], beta_override: float | None = None) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        Kn = as_float(row, "Kn")
        if Kn is None:
            lam = as_float(row, "lambda_mfp")
            length = as_float(row, "L")
            if lam is not None and length is not None and length > 0:
                Kn = lam / length
        C_intr = as_float(row, "C_intr")
        beta = beta_override if beta_override is not None else as_float(row, "beta_Kn")
        context = as_text(row, "kn_context_level")
        C_hat = as_float(row, "C_hat")
        row["Kn"] = Kn if Kn is not None else ""
        row["beta_Kn"] = beta if beta is not None else ""
        if Kn is None or Kn < 0 or C_intr is None or not (0 <= C_intr <= 1) or beta is None or beta <= 0:
            row["kn_ceff_status"] = "not_evaluable_missing_or_invalid_inputs"
        else:
            ceff = C_intr * math.exp(-beta * Kn)
            row["C_eff"] = ceff
            if C_hat is not None:
                row["C_eff_residual"] = C_hat - ceff
            if context not in {"physical", "resonance_analogy"}:
                row["kn_ceff_status"] = "FLAG_missing_context_level"
            else:
                row["kn_ceff_status"] = "PASS"
            row["beta_fit_range_status"] = (
                "within_typical_range" if 0.5 <= beta <= 2.0 else "outside_typical_range"
            )
            row["Kn_zone_status"] = "not_assigned_without_explicit_domain_thresholds"
        output.append(row)
    return output


def sweep_simulation(profile: dict, out: Path, grid: dict | None = None) -> dict:
    cfg = profile["operations"]["sweep"]
    grid = grid or cfg["default_grid"]
    keys = list(grid)
    combinations = list(itertools.product(*(grid[k] for k in keys)))
    rows = []
    out.mkdir(parents=True, exist_ok=True)
    for number, values in enumerate(combinations, 1):
        p = copy.deepcopy(profile)
        settings = dict(zip(keys, values))
        for key, value in settings.items():
            if key not in p["simulation"]:
                raise ValueError(f"Unsupported sweep parameter: {key}")
            p["simulation"][key] = value
        _, summary = simulate(p, out / f"case_{number:04d}")
        rows.append({"case": number, **settings, **summary})
    write_rows(out / "sweep_summary.csv", rows)
    return {"cases": len(rows), "parameters": keys, "output": str(out / "sweep_summary.csv")}


def taucheck_operation(profile: dict, core_path: Path, out: Path) -> dict:
    cfg = profile["operations"]["taucheck"]
    sim_report = stabcheck(profile, out / "reparameterization")
    rows = read_rows(core_path)
    by_zone: dict[str, list[float]] = {}
    for row in rows:
        zone = row.get("recommended_zone3", "")
        K = as_float(row, "recommended_C_hat")
        tau = as_float(row, "tau_eff")
        if K is not None and tau is not None:
            by_zone.setdefault(zone, []).append(K * tau)
    invariance = {}
    for zone, values in by_zone.items():
        mean = statistics.fmean(values) if values else 0.0
        sd = statistics.pstdev(values) if len(values) > 1 else 0.0
        invariance[zone] = {
            "n": len(values),
            "mean_K_tau": mean,
            "sd_K_tau": sd,
            "cv_K_tau": None if mean == 0 else sd / abs(mean),
        }
    report = {
        "numerical_reparameterization": sim_report,
        "K_tau_invariance_diagnostic": invariance,
        "interpretation": (
            "K*tau is a testable working hypothesis; the diagnostic is not a universal proof."
        ),
        "passed": bool(sim_report["passed"]),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "taucheck_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def normalize_hyphens(text: str) -> str:
    for char in ("‑", "–", "—", "−"):
        text = text.replace(char, "-")
    return text


def load_records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        value = load_json(path)
        if isinstance(value, list):
            return [dict(x) for x in value]
        if isinstance(value, dict) and isinstance(value.get("records"), list):
            return [dict(x) for x in value["records"]]
        if isinstance(value, dict):
            return [dict(value)]
        raise ValueError("JSON input must be an object, list, or object with records.")
    return read_rows(path)


def write_records(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(
            json.dumps({"records": rows}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        write_rows(path, rows)


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return values[lo]
    weight = pos - lo
    return values[lo] * (1.0 - weight) + values[hi] * weight


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = rank
        i = j
    return ranks


def spearman_rho(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Spearman vectors must be same non-zero length.")
    ra = average_ranks(a)
    rb = average_ranks(b)
    ma = statistics.fmean(ra)
    mb = statistics.fmean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return 1.0 if da == 0 and db == 0 else 0.0 if da == 0 or db == 0 else num / (da * db)


def recursive_source_modules(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"source_modules", "modules", "PV", "SV", "mirror"}:
                if isinstance(value, list):
                    found.extend(str(x) for x in value)
                elif isinstance(value, str):
                    found.extend(
                        re.findall(r"\b(?:TSM-\d{3}D?|META-\d{2}|SM-\d{2}|TSM-LEX)\b",
                                   normalize_hyphens(value))
                    )
            found.extend(recursive_source_modules(value))
    elif isinstance(obj, list):
        for value in obj:
            found.extend(recursive_source_modules(value))
    return found


def validate_operations(bundle: dict) -> tuple[dict, dict]:
    if bundle.get("schema_id") not in {"tsm.operations.bundle.v2", "tsm.operations.bundle.v3", "tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"}:
        raise ValueError("Unsupported operations bundle schema.")
    profile = require(bundle, "profile")
    gates = require(bundle, "gates")
    for field in [
        "numeric.epsilon_rad",
        "numeric.B_hi",
        "numeric.S_lo",
        "simulation.alpha",
        "simulation.lambda_base",
        "simulation.dtau",
        "simulation.steps",
        "simulation.regime.N_dwell",
    ]:
        require(profile, field)
    if profile.get("fail_closed", {}).get("silent_defaults_when_profile_missing") is not False:
        raise ValueError("Operations profile must forbid silent defaults.")
    gate_ids = [g["gate_id"] for g in gates.get("gates", [])]
    if len(gate_ids) != len(set(gate_ids)):
        raise ValueError("Duplicate gate_id.")
    budget = require(bundle, "file_budget")
    if int(budget["active_files"]) > int(budget["custom_gpt_max_files"]):
        raise ValueError("CustomGPT file budget exceeded.")
    if int(budget["reserved_slots"]) < int(budget["minimum_reserved_slots_required"]):
        raise ValueError("Insufficient reserved CustomGPT file slots.")
    if bundle.get("schema_id") in {"tsm.operations.bundle.v3", "tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"}:
        registry = require(bundle, "module_registry")
        expected_entries = 209 if bundle.get("schema_id") in {"tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"} else 208
        if registry.get("entry_count") != expected_entries or len(registry.get("entries", [])) != expected_entries:
            raise ValueError(
                f"{bundle.get('schema_id')} module registry must contain exactly {expected_entries} entries."
            )
        rules = require(bundle, "meta04_rules")
        if rules.get("rule_count") != 24 or len(rules.get("rules", [])) != 24:
            raise ValueError("META-04 catalogue must contain 24 rules.")
        if not bundle.get("policies", {}).get("unqualified_Q_c_forbidden"):
            raise ValueError("Operations bundle must forbid unqualified Q_c.")
        if bundle.get("schema_id") in {"tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"}:
            if not bundle.get("policies", {}).get("TSM_000_is_semantic_root"):
                raise ValueError("v4 must declare TSM-000 as semantic root.")
            if bundle.get("policies", {}).get("canonical_axiom_count") != 2:
                raise ValueError("v4 must declare exactly two canonical axioms.")
    tf_profile = require(bundle, "tool_family_multiscale_profile")
    if tf_profile.get("is_fourth_tool") is not False or tf_profile.get("prefix") != "TF_":
        raise ValueError("The active corpus requires a non-fourth-tool TF multiscale profile.")
    if tf_profile.get("policies", {}).get("no_new_scoring_formula") is not True:
        raise ValueError("The TF profile must forbid a new scoring formula.")

    execution_profile = require(bundle, "canonical_execution_profile")
    if execution_profile.get("version") != "v7.2":
        raise ValueError("The active canonical execution profile must be v7.2.")

    ai_system = require(bundle, "ai_synthesis_system")
    if ai_system.get("joint_use_required") is not True:
        raise ValueError("Joint use of reading key and original AI synthesis is required.")
    if ai_system.get("execution_key_replaces_original_synthesis") is not False:
        raise ValueError("The reading key may not replace the original AI synthesis.")
    if ai_system.get("original_synthesis_replaces_execution_key") is not False:
        raise ValueError("The original AI synthesis may not replace the reading key.")

    dialog_policy = require(ai_system, "dialog_routing_policy")
    if dialog_policy.get("required_before_epistemic_goal") is not True:
        raise ValueError("Dialog status, material referent and route must precede epistemic-goal selection.")
    if dialog_policy.get("selected_referent_status") != "working_hypothesis_until_sufficiently_confirmed":
        raise ValueError("The selected referent must remain a working hypothesis until sufficiently confirmed.")
    if dialog_policy.get("forbid_invented_internal_reconstruction") is not True:
        raise ValueError("Invented internal reconstruction is forbidden.")
    if dialog_policy.get("compact_integrity_check_includes_route_fit") is not True:
        raise ValueError("The compact integrity check must include dialog-route fit.")

    expected_routes = {
        "normal_content_path",
        "parallel_reference_path",
        "targeted_clarification_path",
        "lightweight_context_target_scope_check",
        "dependency_scoped_correction_path",
    }
    if set(dialog_policy.get("route_values", [])) != expected_routes:
        raise ValueError("The active dialogue route catalogue is incomplete.")

    signal_rule = dialog_policy.get("correction_signal_rule", {})
    if not all(signal_rule.get(name) is True for name in [
        "irony_sarcasm_and_rhetorical_questions_are_signals_not_proof",
        "indirect_dissatisfaction_may_activate_lightweight_review",
        "do_not_force_correction_mode_from_ambiguous_signal",
        "do_not_ignore_material_indirect_critique",
    ]):
        raise ValueError("The correction-signal policy is incomplete.")

    correction_branch = dialog_policy.get("correction_branch", {})
    if correction_branch.get("full_review_only_on_correction_route") is not True:
        raise ValueError("Full correction review must only run on the correction route.")
    requirements = correction_branch.get("requirements", {})
    required_correction_flags = [
        "identify_critique_target",
        "correction_scope_must_match_evidence",
        "identify_affected_and_dependent_claims",
        "preserve_independent_claims",
        "allow_open_status",
        "forbid_global_invalidation_from_local_error",
        "forbid_harmony_driven_concession",
        "fully_supported_critique_must_be_fully_acknowledged",
        "forbid_blanket_defensiveness",
        "branch_local_repair_required",
        "forbid_invented_retrospective_motive",
    ]
    if not all(requirements.get(name) is True for name in required_correction_flags):
        raise ValueError("The active correction branch is incomplete.")
    return profile, gates


def validate_package(root: Path, bundle: dict) -> dict:
    profile, gates = validate_operations(bundle)
    active = bundle["manifest"]["active_files"]
    expected_count = int(bundle["file_budget"]["active_files"])
    if len(active) != expected_count:
        raise ValueError(f"Manifest contains {len(active)} active files, expected {expected_count}.")
    missing = []
    hash_failures = []
    for entry in active:
        path = root / entry["path"]
        if not path.exists():
            missing.append(entry["path"])
        elif entry["path"] != "TSM_Operations.json":
            actual = sha256_file(path)
            if actual != entry["sha256"]:
                hash_failures.append(entry["path"])
    if missing:
        raise FileNotFoundError(f"Missing active files: {missing}")
    if hash_failures:
        raise ValueError(f"Hash mismatch: {hash_failures}")

    core = read_rows(root / profile["paths"]["core_data"])
    studies = read_rows(root / profile["paths"]["studies_data"])
    sensitivity = read_rows(root / profile["paths"]["sensitivity_data"])
    core_ids = [r["record_id"] for r in core]
    study_ids = [r["record_id"] for r in studies]
    config_ids = [r["config_id"] for r in sensitivity]
    if len(core) != 10000 or len(core_ids) != len(set(core_ids)):
        raise ValueError("Core CSV must contain 10,000 unique record IDs.")
    if len(studies) != 66 or len(study_ids) != len(set(study_ids)):
        raise ValueError("Studies CSV must contain 66 unique record IDs.")
    if len(sensitivity) != 50 or len(config_ids) != len(set(config_ids)):
        raise ValueError("Sensitivity CSV must contain 50 unique config IDs.")

    group_counts: dict[str, int] = {}
    for row in studies:
        group = row.get("dataset_group", "")
        group_counts[group] = group_counts.get(group, 0) + 1
        if group in {"composite_anchor", "quarantine"}:
            if parse_bool(row.get("classification_allowed")) is not False:
                raise ValueError(f"{row['record_id']} must be classification-blocked.")
    expected_groups = {
        "material_physics": 44,
        "social_network_ews": 17,
        "composite_anchor": 4,
        "quarantine": 1,
    }
    if group_counts != expected_groups:
        raise ValueError(f"Unexpected studies group counts: {group_counts}")

    study_schema = study_schema_audit(root, bundle)
    if study_schema["status"] != "PASS":
        raise ValueError(f"Study schema audit failed: {study_schema}")
    tf_framework = tool_family_map_audit(root, bundle)
    if tf_framework["status"] != "PASS":
        raise ValueError(f"Tool-family multiscale profile audit failed: {tf_framework}")
    ai_framework = ai_execution_order_audit(root, bundle)
    if ai_framework["status"] != "PASS":
        raise ValueError(f"AI execution order audit failed: {ai_framework}")
    dialog_framework = dialog_routing_audit(root, bundle)
    if dialog_framework["status"] != "PASS":
        raise ValueError(f"Dialog-routing audit failed: {dialog_framework}")

    registry_ids = [x["id"] for x in bundle.get("module_registry", {}).get("entries", [])]
    if bundle.get("schema_id") in {"tsm.operations.bundle.v3", "tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"}:
        if len(registry_ids) != len(set(registry_ids)):
            raise ValueError("Duplicate module registry ID.")
        expected_entries = 209 if bundle.get("schema_id") in {"tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"} else 208
        if len(registry_ids) != expected_entries:
            raise ValueError("Module registry count mismatch.")
        if bundle.get("schema_id") in {"tsm.operations.bundle.v4", "tsm.operations.bundle.v5", "tsm.operations.bundle.v6"} and "TSM-000" not in registry_ids:
            raise ValueError("TSM-000 missing from v4 module registry.")
        command_specs = bundle.get("operation_specs", {})
        if len(command_specs) < 25:
            raise ValueError("Operation specification set is incomplete.")

    return {
        "status": "ok",
        "schema_id": bundle.get("schema_id"),
        "active_files": len(active),
        "reserved_slots": bundle["file_budget"]["reserved_slots"],
        "profile_id": profile["profile_id"],
        "config_hash": canonical_hash(profile, gates, bundle.get("operation_specs", {})),
        "rows": {"core": len(core), "studies": len(studies), "sensitivity": len(sensitivity)},
        "study_groups": group_counts,
        "module_registry_entries": len(registry_ids),
        "meta04_rules": len(bundle.get("meta04_rules", {}).get("rules", [])),
    }


def module_coverage_audit(bundle: dict, root: Path | None = None) -> dict:
    registry = bundle["module_registry"]["entries"]
    ids = [x["id"] for x in registry]
    known = set(ids)
    coverage: dict[str, int] = {}
    priorities: dict[str, int] = {}
    identity_blocks = []
    for entry in registry:
        current_coverage = entry.get("coverage_status", "unknown")
        coverage[current_coverage] = coverage.get(current_coverage, 0) + 1
        priorities[entry["priority"]] = priorities.get(entry["priority"], 0) + 1
        if entry["proposed_operation"] == "none_until_identity_resolved":
            identity_blocks.append(entry["id"])
    link_unknown = sorted(set(bundle["manifest"].get("module_links", {})) - known)
    stale = []
    for id_, link in bundle["manifest"].get("module_links", {}).items():
        text = json.dumps(link, ensure_ascii=False).lower()
        if "blocked" in text or "spec_only" in text:
            feature_text = json.dumps(bundle["profile"].get("features", {})).lower()
            if id_.lower() in feature_text or link.get("status") in {"active", "active_or_conditional"}:
                stale.append(id_)
    expected_entries = int(bundle.get("module_registry", {}).get("entry_count", len(ids)))
    critical_identity_failures = []
    by_id = {entry["id"]: entry for entry in registry}
    for assertion in bundle.get("module_registry", {}).get("critical_identity_assertions", []):
        module_id = assertion.get("id")
        expected_title = assertion.get("expected_title")
        entry = by_id.get(module_id)
        if entry is None or entry.get("index_title") != expected_title:
            critical_identity_failures.append({
                "id": module_id,
                "reason": "registry_title_mismatch",
                "expected": expected_title,
                "actual": None if entry is None else entry.get("index_title"),
            })
            continue
        if root is not None:
            canonical_file = entry.get("canonical_file")
            path = root / str(canonical_file)
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            heading_match = any(
                line.startswith("## ") and module_id in line and expected_title in line
                for line in text.splitlines()
            )
            if not heading_match:
                critical_identity_failures.append({
                    "id": module_id,
                    "reason": "canonical_heading_missing_or_mismatched",
                    "expected": expected_title,
                    "file": canonical_file,
                })
    status = "FAIL" if len(ids) != expected_entries or len(ids) != len(known) or link_unknown or critical_identity_failures else (
        "FLAG" if identity_blocks or stale else "PASS"
    )
    return {
        "status": status,
        "entry_count": len(ids),
        "unique_ids": len(known),
        "coverage": coverage,
        "priorities": priorities,
        "identity_blocks": identity_blocks,
        "unknown_module_links": link_unknown,
        "stale_module_links": stale,
        "critical_identity_failures": critical_identity_failures,
    }


def crosslink_lint(root: Path, bundle: dict) -> dict:
    registry = bundle["module_registry"]["entries"]
    known = {x["id"] for x in registry}
    known.update(r["id"] for r in bundle.get("meta04_rules", {}).get("rules", []))
    allowed = set(bundle["operation_specs"]["crosslink_lint"].get("allowed_external_ids", []))
    registry_unknown = []
    for entry in registry:
        links = entry.get("index_links", {})
        for family in ("PV", "SV", "mirror"):
            for ref in links.get(family, []):
                if ref not in known and ref not in allowed:
                    registry_unknown.append({"from": entry["id"], "family": family, "ref": ref})
    op_refs = recursive_source_modules({
        "specs": bundle.get("operation_specs", {}),
        "gates": bundle.get("gates", {}),
        "schema": bundle.get("field_schema", {}),
    })
    operation_unknown = sorted({
        x for x in op_refs
        if x not in known and x not in allowed
        and not (re.fullmatch(r"META-\d{2}-R\d+", x) and x.split("-R", 1)[0] in known)
    })

    corpus_text = "\n".join(
        normalize_hyphens((root / name).read_text(encoding="utf-8"))
        for name in bundle["semantic_authority"]["files"]
    )
    corpus_ids = set(re.findall(r"\b(?:TSM-\d{3}D?|META-\d{2}|SM-\d{2})\b", corpus_text))
    corpus_unknown = sorted(corpus_ids - known)
    registry_not_located = sorted(
        entry["id"] for entry in registry
        if entry["id"] not in corpus_ids and not entry.get("source_location")
    )
    status = "FAIL" if registry_unknown or operation_unknown or corpus_unknown else (
        "FLAG" if registry_not_located else "PASS"
    )
    return {
        "status": status,
        "known_ids": len(known),
        "registry_unknown": registry_unknown,
        "operation_unknown": operation_unknown,
        "corpus_unknown": corpus_unknown,
        "registry_not_located": registry_not_located,
    }



def axiom_audit(root: Path, bundle: dict) -> dict:
    spec = bundle.get("operation_specs", {}).get("axiom_audit")
    if not spec:
        return {
            "status": "FAIL",
            "reason": "axiom_audit_spec_missing",
        }

    root_info = bundle.get("semantic_authority", {}).get("axiomatic_root", {})
    file_name = root_info.get("file")
    if not file_name:
        return {
            "status": "FAIL",
            "reason": "axiomatic_root_file_missing",
        }

    path = root / file_name
    if not path.exists():
        return {
            "status": "FAIL",
            "reason": "axiomatic_root_file_not_found",
            "file": file_name,
        }

    raw_text = normalize_hyphens(path.read_text(encoding="utf-8"))
    text_lower = raw_text.lower()
    registry = bundle.get("module_registry", {}).get("entries", [])
    registry_ids = {entry.get("id") for entry in registry}

    axiom_i = bool(
        re.search(r"\baxiom\s*(?:1|i)\b", text_lower)
        and "resonanztriade" in text_lower
    )
    axiom_ii = bool(
        re.search(r"\baxiom\s*(?:2|ii)\b", text_lower)
        and "rückholspannung" in text_lower
    )
    triad_components = {
        "Real-Seite": "real-seite" in text_lower,
        "Anti-Seite": "anti-seite" in text_lower,
        "Tunnel": "tunnel" in text_lower,
    }
    null_line_hierarchy = bool(
        "kein eigenes drittes axiom" in text_lower
        or "kein eigenes drittes grundaxiom" in text_lower
    )
    recursive_relation = bool(
        "rekursive selbstbezüglichkeit" in text_lower
        and "resonanz ist der" in text_lower
        and "kohärenz ist der" in text_lower
    )
    level_markers = {
        "phys": bool(re.search(r"r(?:_|\\_|<sub>)?phys", text_lower)),
        "psy": bool(re.search(r"r(?:_|\\_|<sub>)?psy", text_lower)),
        "soc": bool(re.search(r"r(?:_|\\_|<sub>)?soc", text_lower)),
        "meta": bool(re.search(r"r(?:_|\\_|<sub>)?meta", text_lower)),
    }
    category_protection = bool(
        "funktionsanalog" in text_lower
        and "kategorial verschieden" in text_lower
    ) or bool(
        "gleichfunktion" in text_lower
        and "gleichartigkeit" in text_lower
    )

    checks = {
        "TSM_000_in_registry": "TSM-000" in registry_ids,
        "registry_count_ok": len(registry_ids) == bundle["module_registry"]["entry_count"] == 209,
        "canonical_axiom_count_ok": spec.get("canonical_axiom_count") == 2,
        "axiom_I_present": axiom_i,
        "axiom_II_present": axiom_ii,
        "triad_complete": all(triad_components.values()),
        "null_line_hierarchy_ok": null_line_hierarchy,
        "recursive_resonance_coherence_ok": recursive_relation,
        "level_index_complete": all(level_markers.values()),
        "category_protection_active": category_protection
            and bool(bundle.get("policies", {}).get(
                "resonance_levels_are_functionally_analogous_not_category_identical"
            )),
    }

    failed = sorted(key for key, value in checks.items() if not value)
    status = "PASS" if not failed else "FAIL"
    return {
        "status": status,
        "file": file_name,
        "module": "TSM-000",
        "checks": checks,
        "failed_checks": failed,
        "triad_components": triad_components,
        "level_markers": level_markers,
        "claim_scope": (
            "semantic_governance_and_level_protection_not_empirical_proof"
        ),
    }


def _rule_result(rule: dict, passed: bool, detail: Any, flag: bool = False) -> dict:
    status = "PASS" if passed and not flag else "FLAG" if passed and flag else rule["severity"]
    return {
        "rule": rule["rule"],
        "id": rule["id"],
        "title": rule["title"],
        "status": status,
        "detail": detail,
    }


def meta04_audit(root: Path, bundle: dict) -> dict:
    profile = bundle["profile"]
    rules = bundle["meta04_rules"]["rules"]
    rule_by_num = {r["rule"]: r for r in rules}
    results = []

    module_result = module_coverage_audit(bundle)
    cross_result = crosslink_lint(root, bundle)
    package_ok = True
    package_detail: Any
    try:
        package_detail = validate_package(root, bundle)
    except Exception as exc:
        package_ok = False
        package_detail = str(exc)

    title_conflicts = [
        x["id"] for x in bundle["module_registry"]["entries"]
        if x["title_match_status"] in {"abweichend", "Mehrfachbelegung"}
    ]
    translation_ok = (
        "translate_validate" in bundle["operation_specs"]
        and len(bundle.get("symbol_numeric_map", {})) >= 9
    )
    studies = read_rows(root / profile["paths"]["studies_data"])
    direct_records = [row for row in studies if row.get("record_type") != "composite_anchor"]
    composite_records = [row for row in studies if row.get("record_type") == "composite_anchor"]
    direct_source_blanks = sum(
        not (row.get("source_id") or row.get("citation") or row.get("doi"))
        for row in direct_records
    )
    composite_contract_violations = []
    composite_partial_blocked = []
    for row in composite_records:
        required_component_fields = ("source_id_C", "source_id_dphi", "source_id_tau")
        missing_fields = [field for field in required_component_fields if not row.get(field)]
        unresolved_fields = [
            field for field in required_component_fields
            if str(row.get(field) or "").startswith("UNRESOLVED")
        ]
        safely_blocked = (
            str(row.get("classification_allowed") or "").lower() == "false"
            and str(row.get("audit_status") or "").startswith("blocked_")
        )
        has_composite_id = bool(row.get("composite_source_id"))
        if missing_fields or not safely_blocked or not has_composite_id:
            composite_contract_violations.append({
                "record_id": row.get("record_id"),
                "missing_fields": missing_fields,
                "has_composite_id": has_composite_id,
                "safely_blocked": safely_blocked,
            })
        elif unresolved_fields:
            composite_partial_blocked.append({
                "record_id": row.get("record_id"),
                "unresolved_fields": unresolved_fields,
            })
    timestamp_blanks = sum(not row.get("timestamp") for row in studies)
    timestamp_semantics_invalid = sum(
        row.get("timestamp") and row.get("timestamp_type") != "record_normalization_utc"
        for row in studies
    )

    field_registry = bundle.get("field_schema", {}).get("x-tsm-field-registry", [])
    critical_fields = {"C", "dphi_rad", "tau_eff", "F_res", "B_rank", "S_rank"}
    field_names = {x.get("name") for x in field_registry}
    missing_critical = sorted(critical_fields - field_names)
    weak_fields = [
        x.get("name") for x in field_registry
        if x.get("name") in critical_fields
        and not (x.get("meaning") and x.get("evidence"))
    ]

    symbol_ok = all(k in bundle.get("symbol_numeric_map", {}) for k in
                    ["SM-01", "SM-02", "SM-03", "SM-04", "SM-05", "SM-06"])
    specs = bundle["operation_specs"]
    op_presence = {
        11: "q_formula_modes",
        12: "astro_resonator",
        13: "ccc_map",
        14: "anti_atlas_full",
        15: "cfdr_series",
        16: "threshold_events",
        17: "cosonance_full",
        18: "autoresonance_series",
        19: "overlap_audit",
        20: "dirac_regime",
        21: "resonance_birth_series",
        23: "urk_modes",
        24: "kappa_tau_full",
    }

    results.append(_rule_result(
        rule_by_num[1],
        module_result["entry_count"] == bundle["module_registry"]["entry_count"],
        module_result,
    ))
    results.append(_rule_result(rule_by_num[2],
                                cross_result["status"] != "FAIL",
                                cross_result,
                                flag=cross_result["status"] == "FLAG"))
    results.append(_rule_result(rule_by_num[3],
                                True,
                                {"title_conflicts": len(title_conflicts),
                                 "identity_blocks": module_result["identity_blocks"]},
                                flag=bool(title_conflicts)))
    results.append(_rule_result(rule_by_num[4], translation_ok,
                                {"translation_spec": translation_ok,
                                 "symbol_map_entries": len(bundle.get("symbol_numeric_map", {}))}))
    source_contract_ok = (
        direct_source_blanks == 0
        and not composite_contract_violations
        and timestamp_blanks == 0
        and timestamp_semantics_invalid == 0
    )
    results.append(_rule_result(
        rule_by_num[5],
        source_contract_ok,
        {
            "records": len(studies),
            "direct_records": len(direct_records),
            "direct_source_blanks": direct_source_blanks,
            "composite_records": len(composite_records),
            "composite_contract_violations": composite_contract_violations,
            "composite_partial_provenance_safely_blocked": composite_partial_blocked,
            "timestamp_blanks": timestamp_blanks,
            "timestamp_semantics_invalid": timestamp_semantics_invalid,
            "timestamp_semantics": "record_normalization_utc",
        },
    ))
    results.append(_rule_result(rule_by_num[6], package_ok, package_detail))
    results.append(_rule_result(rule_by_num[7],
                                not missing_critical and not weak_fields,
                                {"missing_critical": missing_critical, "weak_fields": weak_fields}))
    results.append(_rule_result(rule_by_num[8], symbol_ok,
                                {"core_symbols_present": symbol_ok}))
    results.append(_rule_result(rule_by_num[9], translation_ok,
                                {"META09_operation": "translate-validate"}))
    results.append(_rule_result(rule_by_num[10], package_ok,
                                {"manifest_hashes": package_ok,
                                 "seed": profile["simulation"].get("seed"),
                                 "profile_id": profile.get("profile_id")}))

    for number, spec_name in op_presence.items():
        exists = spec_name in specs
        results.append(_rule_result(rule_by_num[number], exists,
                                    {"operation_spec": spec_name, "present": exists}))

    results.append(_rule_result(rule_by_num[22],
                                bool(bundle.get("policies", {}).get("return_over_output_policy")),
                                {"return_over_output_policy":
                                 bundle.get("policies", {}).get("return_over_output_policy")}))

    results.sort(key=lambda x: x["rule"])
    overall = "FAIL" if any(x["status"] == "FAIL" for x in results) else (
        "FLAG" if any(x["status"] == "FLAG" for x in results) else "PASS"
    )
    return {
        "overall_status": overall,
        "rules_total": len(results),
        "PASS": sum(x["status"] == "PASS" for x in results),
        "FLAG": sum(x["status"] == "FLAG" for x in results),
        "FAIL": sum(x["status"] == "FAIL" for x in results),
        "results": results,
    }


def q_formula_rows(
    rows: list[dict],
    profile: dict,
    c_field: str = "C",
    dphi_field: str = "dphi_rad",
    tau_field: str = "tau",
) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    work = []
    raw_values = []
    for source in rows:
        row = dict(source)
        C = as_float(row, c_field)
        dphi = as_float(row, dphi_field)
        tau = as_float(row, tau_field)
        if dphi is None or tau is None:
            row["Q_formula_status"] = "not_evaluable_missing_dphi_or_tau"
            work.append((row, None, None, C))
            continue
        qeff = tau / max(abs(dphi), eps)
        plv = abs(math.cos(dphi))
        raw = qeff * plv
        raw_values.append(raw)
        work.append((row, qeff, plv, C))
    lo = min(raw_values) if raw_values else 0.0
    hi = max(raw_values) if raw_values else 0.0
    output = []
    raw_index = 0
    for row, qeff, plv, C in work:
        if qeff is None:
            output.append(row)
            continue
        raw = qeff * plv
        core = 0.0 if hi == lo else (raw - lo) / (hi - lo)
        row["Q_eff"] = qeff
        row["PLV_tau"] = plv
        row["Q_c_core"] = clamp(core, 0.0, 1.0)
        if C is None:
            row["Q_c_TSM153"] = ""
            row["Q_c_TSM153_status"] = "not_evaluable_missing_C"
        else:
            row["Q_c_TSM153"] = clamp(qeff * plv * C, 0.0, 1.0)
            row["Q_c_TSM153_status"] = "evaluated"
        row["Q_formula_status"] = "evaluated_named_modes"
        output.append(row)
        raw_index += 1
    return output


def master_formula_rows(
    rows: list[dict],
    profile: dict,
    c_field: str = "C",
    dphi_field: str = "dphi_rad",
    tau_field: str = "tau",
    r_field: str = "R",
) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    output = []
    for source in rows:
        row = dict(source)
        C = as_float(row, c_field)
        dphi = as_float(row, dphi_field)
        tau = as_float(row, tau_field)
        R = as_float(row, r_field)
        if C is None or dphi is None:
            row["formula_status"] = "not_evaluable_missing_C_or_dphi"
        else:
            denom = max(abs(dphi), eps)
            row["TSM136_master"] = "" if R is None else R * C / denom
            row["TSM136D_F_res"] = "" if tau is None else C * tau / denom
            row["formula_status"] = (
                "both_modes" if R is not None and tau is not None
                else "TSM136_only" if R is not None
                else "TSM136D_only" if tau is not None
                else "not_evaluable_missing_R_and_tau"
            )
        output.append(row)
    return output


def epsilon_symbol_audit(root: Path, bundle: dict, input_path: Path | None = None) -> dict:
    """Audit the epsilon floor in two distinct layers.

    1. The package core is inspected for actual epsilon exposure. A core whose
       smallest |dphi| lies above the largest tested epsilon is correctly
       reported as NOT_EXPOSED, not as a defect.
    2. A deterministic in-memory boundary fixture verifies that the epsilon
       floor is mathematically active and responsive around 0.5°, 1.0° and
       1.5° without altering or padding the canonical core dataset.
    """
    profile = bundle["profile"]
    specs = bundle["operation_specs"]["epsilon_zone_symbol_audit"]
    path = input_path or root / profile["paths"]["core_data"]
    rows = read_rows(path)

    dphi_values = []
    tau_values = []
    for row in rows:
        dphi = as_float(row, "dphi_rad")
        tau = as_float(row, "tau_eff") or as_float(row, "tau")
        if dphi is not None and tau is not None:
            dphi_values.append(dphi)
            tau_values.append(tau)

    epsilon_degrees = [float(x) for x in specs["epsilon_degrees"]]

    def evaluate(dphis: list[float], taus: list[float]) -> tuple[dict, dict]:
        results = {}
        vectors = {}
        for deg in epsilon_degrees:
            eps = math.radians(deg)
            scores = [
                tau / max(abs(dphi), eps) * abs(math.cos(dphi))
                for dphi, tau in zip(dphis, taus)
            ]
            key = str(deg)
            vectors[key] = scores
            results[key] = {
                "epsilon_rad": eps,
                "phase_gate_count": sum(abs(x) <= eps for x in dphis),
                "score_min": min(scores) if scores else None,
                "score_max": max(scores) if scores else None,
            }
        return results, vectors

    core_results, core_vectors = evaluate(dphi_values, tau_values)
    base_key = str(float(specs.get("baseline_epsilon_degrees", 1.0)))
    if base_key not in core_vectors:
        base_key = "1.0"
    core_base = core_vectors.get(base_key, [])
    core_correlations = {
        key: spearman_rho(core_base, values)
        for key, values in core_vectors.items()
    }
    max_epsilon_rad = math.radians(max(epsilon_degrees))
    core_exposed_count = sum(abs(x) <= max_epsilon_rad for x in dphi_values)
    core_exposed = core_exposed_count > 0
    core_rank_pass = (
        all(v >= float(specs["spearman_min"]) for v in core_correlations.values())
        if core_exposed else True
    )

    fixture_degrees = [
        float(x) for x in specs.get(
            "boundary_fixture_degrees",
            [0.0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75,
             1.0, -1.0, 1.25, -1.25, 1.5, -1.5, 2.0, -2.0, 3.0, -3.0],
        )
    ]
    fixture_dphi = [math.radians(x) for x in fixture_degrees]
    fixture_tau = [1.0 + i * 0.01 for i in range(len(fixture_dphi))]
    fixture_results, fixture_vectors = evaluate(fixture_dphi, fixture_tau)

    fixture_counts = [
        fixture_results[str(deg)]["phase_gate_count"]
        for deg in epsilon_degrees
    ]
    count_monotonic = all(
        left <= right for left, right in zip(fixture_counts, fixture_counts[1:])
    )
    count_responsive = len(set(fixture_counts)) > 1
    finite_scores = all(
        math.isfinite(value)
        for values in fixture_vectors.values()
        for value in values
    )
    changed_vs_baseline = {
        key: sum(
            not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
            for a, b in zip(fixture_vectors[base_key], values)
        )
        for key, values in fixture_vectors.items()
    }
    response_present = all(
        key == base_key or changed > 0
        for key, changed in changed_vs_baseline.items()
    )

    zero_index = fixture_degrees.index(0.0)
    floor_exact = all(
        math.isclose(
            fixture_vectors[str(deg)][zero_index],
            fixture_tau[zero_index] / math.radians(deg),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        for deg in epsilon_degrees
    )
    outside_indices = [
        i for i, deg in enumerate(fixture_degrees)
        if abs(deg) > max(epsilon_degrees)
    ]
    outside_invariant = all(
        all(
            math.isclose(
                fixture_vectors[str(epsilon_degrees[0])][i],
                fixture_vectors[str(deg)][i],
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
            for deg in epsilon_degrees[1:]
        )
        for i in outside_indices
    )

    boundary_pass = all([
        count_monotonic,
        count_responsive,
        finite_scores,
        response_present,
        floor_exact,
        outside_invariant,
    ])

    if not boundary_pass:
        status = "FAIL"
    elif core_exposed and not core_rank_pass:
        status = "FLAG"
    else:
        status = "PASS"

    min_abs_dphi = min((abs(x) for x in dphi_values), default=None)
    return {
        "status": status,
        "rows_evaluated": len(dphi_values),
        "core_coverage": {
            "status": "EXPOSED" if core_exposed else "NOT_EXPOSED",
            "epsilon_exposed_rows": core_exposed_count,
            "minimum_abs_dphi_rad": min_abs_dphi,
            "minimum_abs_dphi_deg": (
                math.degrees(min_abs_dphi) if min_abs_dphi is not None else None
            ),
            "maximum_tested_epsilon_deg": max(epsilon_degrees),
            "interpretation": (
                "The core contains epsilon-sensitive rows."
                if core_exposed else
                "The canonical core lies entirely above the tested epsilon range; "
                "this is a domain-coverage fact, not an audit defect."
            ),
        },
        "epsilon_results_core": core_results,
        "spearman_vs_baseline_core": core_correlations,
        "spearman_min_required_when_core_exposed": specs["spearman_min"],
        "core_rank_stability_status": (
            "PASS" if core_exposed and core_rank_pass else
            "FLAG" if core_exposed else
            "NOT_APPLICABLE_NO_EPSILON_EXPOSURE"
        ),
        "boundary_fixture": {
            "status": "PASS" if boundary_pass else "FAIL",
            "fixture_degrees": fixture_degrees,
            "epsilon_results": fixture_results,
            "changed_scores_vs_baseline": changed_vs_baseline,
            "checks": {
                "phase_gate_counts_monotonic": count_monotonic,
                "phase_gate_counts_responsive": count_responsive,
                "all_scores_finite": finite_scores,
                "scores_change_when_epsilon_changes": response_present,
                "zero_phase_uses_exact_epsilon_floor": floor_exact,
                "values_outside_epsilon_range_remain_invariant": outside_invariant,
            },
            "claim_scope": "deterministic_runner_regression_test_only",
        },
        "symbol_map_entries": len(bundle.get("symbol_numeric_map", {})),
        "review_flag": status == "FLAG",
        "vacuous_epsilon_sweep": not core_exposed,
        "vacuity_treatment": (
            "NOT_APPLICABLE_ON_CORE_AND_VERIFIED_BY_BOUNDARY_FIXTURE"
            if not core_exposed else "CORE_EXPOSED"
        ),
        "zone_hysteresis_note": (
            "Static core rows are not a chronological state series; hysteresis is evaluated "
            "by threshold-events/CFDR series commands when ordered input is supplied."
        ),
    }


def _get_zone(row: dict) -> str | None:
    return (
        as_text(row, "zone")
        or as_text(row, "zone3")
        or as_text(row, "recommended_zone3")
        or as_text(row, "sim_regime")
    )


def threshold_event_rows(rows: list[dict], profile: dict) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    B_hi = float(profile["numeric"]["B_hi"])
    S_lo = float(profile["numeric"]["S_lo"])
    N = int(profile["simulation"]["regime"]["N_dwell"])
    output = []
    previous_zone = None
    lock_run = 0
    sigma_run = 0
    for source in rows:
        row = dict(source)
        dphi = as_float(row, "dphi_rad")
        K = as_float(row, "K")
        if K is None:
            K = as_float(row, "C_hat")
        if K is None:
            K = as_float(row, "recommended_C_hat")
        B = as_float(row, "B_rank")
        if B is None:
            B = as_float(row, "recommended_B_rank")
        S = as_float(row, "S_rank")
        if S is None:
            S = as_float(row, "recommended_S_rank")
        try:
            tau_lock = parse_bool(row.get("tau_lock"))
        except ValueError:
            tau_lock = None
        zone = _get_zone(row)
        phase_ok = dphi is not None and abs(dphi) <= eps
        pi_event = bool(phase_ok and tau_lock is True and K is not None and K >= B_hi)
        delta_event = previous_zone is not None and zone is not None and zone != previous_zone
        sigma_candidate = B is not None and S is not None and B >= B_hi and S <= S_lo
        sigma_run = sigma_run + 1 if sigma_candidate else 0
        sigma_event = sigma_run == N
        theta_candidate = phase_ok and tau_lock is True
        lock_run = lock_run + 1 if theta_candidate else 0
        theta_event = lock_run == N
        row.update({
            "pi_event": pi_event,
            "delta_event": delta_event,
            "sigma_event": sigma_event,
            "theta_event": theta_event,
            "sigma_dwell": sigma_run,
            "theta_dwell": lock_run,
            "threshold_event_status": (
                "evaluated" if dphi is not None
                else "partial_missing_dphi"
            ),
        })
        output.append(row)
        if zone is not None:
            previous_zone = zone
    return output


def cosonance_full_rows(rows: list[dict], profile: dict, cascade_delta: float = 0.02) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    B_hi = float(profile["numeric"]["B_hi"])
    raw_c = [as_float(r, "C") for r in rows]
    finite_c = [x for x in raw_c if x is not None]
    cmin = min(finite_c) if finite_c else 0.0
    cmax = max(finite_c) if finite_c else 0.0
    previous_chat = None
    output = []
    for source in rows:
        row = dict(source)
        C = as_float(row, "C")
        dphi = as_float(row, "dphi_rad")
        Khat = as_float(row, "K_hat")
        if Khat is None:
            Khat = as_float(row, "C_hat")
        fallback = as_float(row, "R_combo_norm")
        if fallback is None:
            fallback = as_float(row, "Q_c_core")
        if fallback is None:
            fallback = as_float(row, "Q_c")
        try:
            tau_lock = parse_bool(row.get("tau_lock"))
        except ValueError:
            tau_lock = None
        if C is None or dphi is None or fallback is None:
            row["cosonance_status"] = "not_evaluable_missing_C_dphi_or_R"
            row["C_hat_canon"] = ""
        else:
            c_norm = 0.0 if cmax == cmin else (C - cmin) / (cmax - cmin)
            chat = clamp(c_norm * abs(math.cos(dphi)) * fallback, 0.0, 1.0)
            row["C_hat_canon"] = chat
            row["cosonance_window"] = chat >= 0.62
            row["cosonance_high"] = chat >= 0.95
            row["cosonance_max"] = chat >= 0.97
            row["cosonance_triple_lock"] = (
                Khat is not None and Khat >= B_hi
                and abs(dphi) <= eps
                and tau_lock is True
            )
            if previous_chat is None:
                row["cosonance_cascade"] = False
                row["cosonance_saturation"] = False
            else:
                row["cosonance_cascade"] = chat >= previous_chat + cascade_delta
                row["cosonance_saturation"] = abs(chat - previous_chat) < 1e-6
            row["cosonance_status"] = (
                "PASS" if row["cosonance_triple_lock"] and row["cosonance_high"]
                else "FLAG" if row["cosonance_window"]
                else "FAIL"
            )
            previous_chat = chat
        output.append(row)
    return output


def autoresonance_series_rows(
    rows: list[dict],
    profile: dict,
    alpha_default: float = 0.5,
    beta_default: float = 1.0,
) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    output = []
    previous_R = None
    for index, source in enumerate(rows):
        row = dict(source)
        R = as_float(row, "R")
        if R is None:
            R = as_float(row, "R_combo_norm")
        dphi = as_float(row, "dphi_rad")
        C = as_float(row, "C")
        Qhat = as_float(row, "Qhat")
        pext = as_float(row, "P_ext_frac")
        alpha = as_float(row, "alpha")
        beta = as_float(row, "beta")
        alpha = alpha_default if alpha is None else alpha
        beta = beta_default if beta is None else beta
        try:
            lock = parse_bool(row.get("tau_lock"))
        except ValueError:
            lock = None
        if R is None or dphi is None:
            row["autoresonance_status"] = "not_evaluable_missing_R_or_dphi"
            output.append(row)
            continue
        dR = alpha * R - beta * abs(dphi)
        stage1 = index == 0 or as_float(row, "I0") is not None
        stage2 = previous_R is not None and R >= previous_R
        stage3 = abs(dphi) <= eps and lock is True
        stage4 = C is not None and Qhat is not None
        internal_effort = as_float(row, "internal_control_effort")
        stage5 = stage3 and 0.0 <= alpha < 1.0 and (
            internal_effort is None or internal_effort >= 0.0
        )
        minimal_external = pext is not None and pext <= 0.01
        row.update({
            "dR_dtau_model": dR,
            "auto_stage_1_initialization": stage1,
            "auto_stage_2_self_coupling": stage2,
            "auto_stage_3_tau_lock": stage3,
            "auto_stage_4_self_description": stage4,
            "auto_stage_5_recalibration": stage5,
            "autoresonance_ok": stage2 and stage3 and stage4 and stage5 and minimal_external,
            "autoresonance_status": (
                "PASS" if stage2 and stage3 and stage4 and stage5 and minimal_external
                else "FLAG" if stage3 and minimal_external
                else "FAIL"
            ),
        })
        output.append(row)
        previous_R = R
    return output


def _variance(values: list[float]) -> float:
    return statistics.pvariance(values) if len(values) >= 2 else 0.0


def fai_rows(
    rows: list[dict],
    value_field: str,
    window: int = 100,
    baseline_multiplier: int = 20,
    z1: float = 2.0,
    z2: float = 3.0,
    persistence: int = 3,
) -> list[dict]:
    if window < 2 or baseline_multiplier < 2:
        raise ValueError("FAI window and baseline multiplier are too small.")
    values = [as_float(r, value_field) for r in rows]
    short_vars: list[float | None] = []
    for i in range(len(values)):
        segment = [x for x in values[max(0, i - window + 1):i + 1] if x is not None]
        short_vars.append(_variance(segment) if len(segment) >= window else None)
    output = []
    pre_run = 0
    alert_run = 0
    baseline_len = window * baseline_multiplier
    for i, source in enumerate(rows):
        row = dict(source)
        current = short_vars[i]
        history = [
            x for x in short_vars[max(0, i - baseline_len):i]
            if x is not None
        ]
        if current is None or len(history) < max(5, window):
            row["FAI"] = ""
            row["FAI_status"] = "not_evaluable_insufficient_baseline"
            pre_run = alert_run = 0
        else:
            mu = statistics.fmean(history)
            sd = statistics.pstdev(history)
            fai = 0.0 if sd == 0 else (current - mu) / sd
            pre_run = pre_run + 1 if fai > z1 else 0
            alert_run = alert_run + 1 if fai > z2 else 0
            row["FAI"] = fai
            row["FAI_short_variance"] = current
            row["FAI_baseline_mean"] = mu
            row["FAI_baseline_sd"] = sd
            row["FAI_prealert"] = pre_run >= persistence
            row["FAI_alert"] = alert_run >= persistence
            row["FAI_status"] = (
                "ALERT" if alert_run >= persistence
                else "PRE_ALERT" if pre_run >= persistence
                else "NORMAL"
            )
        output.append(row)
    return output


def avalanche_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        M = as_float(row, "M")
        Qhat = as_float(row, "Qhat")
        fai = as_float(row, "FAI")
        event_count = as_float(row, "event_count")
        if M is None or Qhat is None:
            row["avalanche_status"] = "not_evaluable_missing_M_or_Qhat"
        else:
            dominant = M >= 0.6
            unstable = Qhat < 0.7
            law_window = 0.2 <= Qhat <= 0.3
            volatility = fai is not None and fai >= 2.0
            row["avalanche_dominance"] = dominant
            row["avalanche_instability"] = unstable
            row["avalanche_window"] = law_window
            row["avalanche_event"] = dominant and law_window and (
                volatility or event_count is not None and event_count >= 1
            )
            row["avalanche_status"] = (
                "EVENT" if row["avalanche_event"]
                else "WARNING" if dominant and unstable
                else "NORMAL"
            )
        output.append(row)
    return output


def turbulence_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        M = as_float(row, "M")
        Qhat = as_float(row, "Qhat")
        fai = as_float(row, "FAI")
        drift = as_float(row, "drift_y")
        if M is None or Qhat is None or fai is None:
            row["turbulence_status"] = "not_evaluable_missing_M_Qhat_or_FAI"
        else:
            intervention = M >= 0.6 and Qhat < 0.7 and fai >= 2.0
            row["turbulence_intervention"] = intervention
            row["compass_structure"] = "increase" if M >= 0.6 else "observe"
            row["compass_rhythm"] = "pulse" if fai >= 2.0 else "stable"
            row["compass_pulse_reset"] = intervention or (drift is not None and drift != 0)
            row["compass_clarity"] = "filter" if Qhat < 0.7 else "maintain"
            row["turbulence_status"] = "INTERVENE" if intervention else "MONITOR"
        output.append(row)
    return output


def damage_alert_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        df1 = as_float(row, "df1_pct")
        df2 = as_float(row, "df2_pct")
        apeak = as_float(row, "a_peak_pct")
        mode = as_float(row, "mode_shape_pct")
        neighbor = as_float(row, "neighbor_pct")
        qhat = as_float(row, "Qhat")
        fai = as_float(row, "FAI")
        if all(x is None for x in [df1, df2, apeak, mode, neighbor, qhat, fai]):
            row["damage_status"] = "not_evaluable_missing_indicators"
            output.append(row)
            continue
        pre = [
            df1 is not None and df1 <= -5,
            df2 is not None and df2 <= -4,
            apeak is not None and apeak >= 30,
            mode is not None and mode >= 50,
            neighbor is not None and neighbor >= 10,
            qhat is not None and qhat < 0.90,
            fai is not None and fai >= 2.0,
        ]
        strong = [
            df1 is not None and df1 <= -9,
            df2 is not None and df2 <= -7,
            apeak is not None and apeak >= 50,
            neighbor is not None and neighbor >= 30,
            qhat is not None and qhat < 0.70 and fai is not None and fai >= 3.0,
        ]
        row["damage_prealert_count"] = sum(pre)
        row["damage_alert_count"] = sum(strong)
        row["damage_prealert"] = sum(pre) >= 2
        row["damage_alert"] = any(strong)
        row["damage_status"] = (
            "ALERT" if any(strong)
            else "PRE_ALERT" if sum(pre) >= 2
            else "NORMAL"
        )
        output.append(row)
    return output


def tunnel_evaluate_rows(rows: list[dict], profile: dict) -> list[dict]:
    weights = {
        "phase": 0.30,
        "r_tau": 0.20,
        "Q": 0.20,
        "NEI": 0.15,
        "gamma": 0.15,
    }
    output = []
    active_run = 0
    for source in rows:
        row = dict(source)
        dphi = as_float(row, "dphi_rad")
        r_tau = as_float(row, "r_tau")
        if r_tau is None:
            r_tau = as_float(row, "PLV_tau")
        Q_raw = as_float(row, "Q")
        Q_tilde = as_float(row, "Q_tilde")
        if Q_tilde is None and Q_raw is not None:
            Q_tilde = clamp(Q_raw / 30.0, 0.0, 1.0)
        NEI = as_float(row, "NEI")
        gamma_tilde = as_float(row, "gamma_tilde")
        tau_dec = as_float(row, "tau_dec")
        if gamma_tilde is None and tau_dec is not None and tau_dec > 0:
            gamma = 1.0 / tau_dec
            gamma_tilde = gamma / (gamma + 1.0 / 3.0)
        loss = as_float(row, "loss_ratio")
        if None in (dphi, r_tau, Q_tilde, NEI, gamma_tilde, loss):
            row["tunnel_status"] = "not_evaluable_missing_inputs"
            active_run = 0
            output.append(row)
            continue
        T = (
            weights["phase"] * math.cos(dphi)
            + weights["r_tau"] * clamp(r_tau, 0.0, 1.0)
            + weights["Q"] * clamp(Q_tilde, 0.0, 1.0)
            + weights["NEI"] * (1.0 - clamp(NEI, 0.0, 1.0))
            - weights["gamma"] * clamp(gamma_tilde, 0.0, 1.0)
        )
        gates = {
            "phase_gate": abs(dphi) <= 0.1 * math.pi,
            "r_tau_gate": r_tau >= 0.6,
            "Q_gate": Q_raw is not None and Q_raw >= 30,
            "NEI_gate": NEI <= 0.15,
            "tau_dec_gate": tau_dec is not None and tau_dec >= 3.0,
            "loss_gate": loss <= 0.001,
        }
        candidate = T >= 0.7 and all(gates.values())
        active_run = active_run + 1 if candidate else 0
        if candidate and abs(dphi) <= profile["numeric"]["epsilon_rad"] and loss < 1e-5:
            regime = "stehend"
        elif candidate:
            regime = "schwellennah"
        elif abs(dphi) > 0.1 * math.pi or r_tau < 0.6:
            regime = "kollabiert"
        else:
            regime = "pulsierend"
        row.update({
            "tunnel_T": clamp(T, 0.0, 1.0),
            **gates,
            "tunnel_active_candidate": candidate,
            "tunnel_active_dwell": active_run,
            "tunnel_active": candidate and active_run >= int(profile["simulation"]["regime"]["N_dwell"]),
            "tunnel_regime": regime,
            "tunnel_status": "PASS" if candidate else "FAIL",
        })
        output.append(row)
    return output


def astro_resonator_rows(rows: list[dict], ema_alpha: float = 0.2) -> list[dict]:
    output = []
    ema = None
    for source in rows:
        row = dict(source)
        dphi = as_float(row, "dphi_rad")
        plv = as_float(row, "plv_tau_at_flares")
        offset_kpc = as_float(row, "host_offset_kpc")
        offset_arcsec = as_float(row, "host_offset_arcsec")
        offset_sigma = as_float(row, "host_offset_sigma")
        flare1 = as_text(row, "t_radio_flare1_utc")
        flare2 = as_text(row, "t_radio_flare2_utc")
        doi = as_text(row, "doi_primary")
        instruments = as_text(row, "instruments")
        kappa = None if dphi is None else math.cos(dphi)
        if kappa is not None:
            ema = kappa if ema is None else ema_alpha * kappa + (1 - ema_alpha) * ema
        fact_complete = (
            as_text(row, "astro_event_id") is not None
            and (offset_kpc is not None or offset_arcsec is not None)
            and as_text(row, "discovery_date_utc") is not None
            and doi is not None
            and instruments is not None
        )
        off_nuclear = (offset_kpc is not None and offset_kpc > 0) or (
            offset_arcsec is not None and offset_arcsec > 0
        )
        double_outflow = bool(flare1 and flare2)
        tau_gate = plv is not None and plv >= 0.6 and ema is not None and ema >= math.cos(0.15)
        row.update({
            "kappa_phi": kappa if kappa is not None else "",
            "kappa_phi_ema": ema if ema is not None else "",
            "astro_factbox_complete": fact_complete,
            "off_nuclear_flag": off_nuclear,
            "double_outflow_flag": double_outflow,
            "tau_gating_ok": tau_gate,
            "astro_audit_status": (
                "PASS" if fact_complete and off_nuclear and tau_gate
                else "FLAG" if fact_complete and off_nuclear
                else "FAIL"
            ),
            "offset_uncertainty_status": (
                "PASS" if offset_sigma is not None else "FLAG_missing_uncertainty"
            ),
        })
        output.append(row)
    return output


def ccc_map_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        alpha = as_float(row, "alpha_value")
        A = as_float(row, "A_K")
        B = as_float(row, "B_lambda")
        Cc = as_float(row, "C_phi")
        K0 = as_float(row, "K")
        lam0 = as_float(row, "lambda_base")
        phi0 = as_float(row, "dphi_rad")
        if None in (alpha, A, B, Cc):
            row["CCC_status"] = "not_evaluable_missing_alpha_or_coefficients"
        elif min(A, B, Cc) <= 0:
            row["CCC_status"] = "FAIL_nonpositive_coefficient"
        else:
            dK = A * alpha
            dlam = B * alpha
            dphi = Cc * alpha
            row.update({
                "delta_K": dK,
                "delta_lambda": dlam,
                "delta_phi": dphi,
                "K_alpha_on": "" if K0 is None else K0 + dK,
                "lambda_alpha_on": "" if lam0 is None else lam0 + dlam,
                "dphi_alpha_on": "" if phi0 is None else wrap_angle(phi0 + dphi),
                "CCC_status": "evaluated_working_hypothesis",
                "CCC_claim_scope": "external_model_mapping_not_validated_constant_variation",
            })
        output.append(row)
    return output


def anti_atlas_full_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        dphi = as_float(row, "dphi_rad")
        plv = as_float(row, "PLV_tau")
        rcombo = as_float(row, "R_combo_norm")
        tau = as_float(row, "tau_eff")
        nei = as_float(row, "NEI")
        repeat = as_float(row, "repeatability")
        peak = as_float(row, "peak_PLV_tau")
        pre_score = as_float(row, "pre_score")
        post_score = as_float(row, "post_score")
        gate = dphi is not None and plv is not None and abs(dphi) <= 0.10 and plv >= 0.60
        if not gate:
            typ = "n/a"
            status = "FAIL_GATE"
        elif rcombo is not None and rcombo >= 0.66:
            typ = "A1"; status = "PASS"
        elif tau is not None and repeat is not None and tau >= 1.0 and repeat >= 0.8:
            typ = "A2"; status = "PASS"
        elif peak is not None and peak >= 0.6 and rcombo is not None and 0.33 <= rcombo < 0.66:
            typ = "A3"; status = "PASS"
        else:
            typ = "A4"; status = "FLAG"
        rollback = nei is not None and nei > 0.15 and post_score is not None and pre_score is not None and post_score < pre_score
        zone = _get_zone(row)
        conflict = typ in {"A1", "A3"} and zone in {"fragmentiert", "F", "F+"}
        row.update({
            "anti_gate_ok": gate,
            "anti_typ_full": typ,
            "anti_score_full": "" if rcombo is None else clamp(rcombo, 0.0, 1.0),
            "anti_conflict": conflict,
            "anti_rollback_required": rollback,
            "anti_audit_status": "FAIL" if rollback else "FLAG" if conflict else status,
        })
        output.append(row)
    return output


def cfdr_rows(rows: list[dict], profile: dict, weights_override: dict | None = None) -> list[dict]:
    cfg = profile["operations"]["cfdr"]
    weights = dict(weights_override or cfg["weights"])
    if abs(sum(float(v) for v in weights.values()) - 1.0) > 1e-12:
        raise ValueError("CFDR weights must sum to 1.")
    N = int(cfg.get("stability_window", 21))
    pending = None
    pending_count = 0
    stable_class = None
    output = []
    for source in rows:
        row = dict(source)
        axes = {axis: as_float(row, f"CFDR_{axis}") for axis in "CDRF"}
        dphi = as_float(row, "dphi_rad")
        plv = as_float(row, "PLV_tau")
        gate = (
            dphi is not None and plv is not None
            and abs(dphi) <= float(cfg["gate"]["dphi_abs_max_rad"])
            and plv >= float(cfg["gate"]["PLV_tau_min"])
        )
        row["CFDR_gate_ok"] = gate
        missing_axes = [k for k, v in axes.items() if v is None]
        out_of_range = [k for k, v in axes.items() if v is not None and not (0 <= v <= 1)]
        sources_complete = all(as_text(row, f"CFDR_{axis}_source") is not None for axis in "CDRF")
        normalization = as_text(row, "CFDR_normalization")
        if not gate:
            index = None
            candidate = None
            row["CFDR_status"] = "FAIL"
            row["CFDR_reason"] = "gate_fail_no_typification"
        elif missing_axes or out_of_range:
            index = None
            candidate = None
            row["CFDR_status"] = "FAIL"
            row["CFDR_reason"] = (
                "missing_axes:" + ",".join(missing_axes)
                if missing_axes else "axis_out_of_range:" + ",".join(out_of_range)
            )
        else:
            index = sum(float(weights[a]) * float(axes[a]) for a in "CDRF")
            candidate = cfdr_class(index, cfg["classes"])
            row["CFDR_status"] = "PASS" if sources_complete and normalization else "FLAG"
            row["CFDR_reason"] = (
                "complete_and_gate_ok" if row["CFDR_status"] == "PASS"
                else "mapping_or_sources_incomplete"
            )
        if candidate is None:
            pending = None; pending_count = 0
        elif stable_class is None:
            stable_class = candidate
            pending = None; pending_count = 0
        elif candidate == stable_class:
            pending = None; pending_count = 0
        else:
            if candidate == pending:
                pending_count += 1
            else:
                pending = candidate
                pending_count = 1
            if pending_count >= N:
                stable_class = candidate
                pending = None
                pending_count = 0
        row.update({
            "CFDR_index": "" if index is None else index,
            "CFDR_class_candidate": "" if candidate is None else candidate,
            "CFDR_class_stable": "" if stable_class is None else stable_class,
            "CFDR_pending_class": "" if pending is None else pending,
            "CFDR_pending_dwell": pending_count,
            "CFDR_weights_id": cfg["weights_id"],
            "CFDR_weights": json.dumps(weights, sort_keys=True),
            "CFDR_transition_status": "series_hysteresis_active",
        })
        output.append(row)
    return output


def overlap_audit_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        G = as_float(row, "G_component")
        if G is None:
            G = as_float(row, "G_est")
        T = as_float(row, "T_component")
        if T is None:
            T = as_float(row, "R_combo_norm")
        if G is None or T is None:
            row["overlap_status"] = "not_evaluable_missing_G_or_T"
        else:
            row["W_effect"] = G + T
            row["T_fraction"] = T / (abs(G) + abs(T)) if G != 0 or T != 0 else 0.0
            row["overlap_status"] = "REPORT_ONLY"
            row["overlap_claim_scope"] = "geometric_modulation_no_additional_force_or_energy"
        output.append(row)
    return output


def _linear_fit(x: list[float], y: list[float]) -> tuple[float, float, float]:
    if len(x) < 2 or len(x) != len(y):
        raise ValueError("Linear fit needs at least two paired points.")
    mx = statistics.fmean(x)
    my = statistics.fmean(y)
    sxx = sum((v - mx) ** 2 for v in x)
    if sxx == 0:
        raise ValueError("Linear fit x variance is zero.")
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    intercept = my - slope * mx
    predicted = [intercept + slope * v for v in x]
    ss_res = sum((b - p) ** 2 for b, p in zip(y, predicted))
    ss_tot = sum((b - my) ** 2 for b in y)
    r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return slope, intercept, r2


def dirac_regime_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.get("series_id", "default"), []).append(dict(row))
    output = []
    for series_id, group in grouped.items():
        pairs = [
            (as_float(r, "temperature"), as_float(r, "chi"))
            for r in group
        ]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        fit = None
        if len(pairs) >= 3:
            fit = _linear_fit([p[0] for p in pairs], [p[1] for p in pairs])
        for row in group:
            vF = as_float(row, "v_F")
            meff = as_float(row, "m_eff")
            c_ratio = None if vF is None else vF / 299792458.0
            hall = as_float(row, "hall_support")
            source_ok = bool(as_text(row, "source") or as_text(row, "doi"))
            if fit is None:
                row["dirac_status"] = "not_evaluable_insufficient_chi_T_series"
            else:
                slope, intercept, r2 = fit
                physical_limits = (
                    (c_ratio is None or c_ratio < 0.1)
                    and (meff is None or abs(meff) < 1.0)
                )
                gate = r2 >= 0.95 and physical_limits
                row.update({
                    "chi_slope": slope,
                    "chi_intercept": intercept,
                    "chi_r2": r2,
                    "vF_over_c": "" if c_ratio is None else c_ratio,
                    "dirac_gate": gate,
                    "dirac_status": (
                        "PASS" if gate and source_ok and (hall is None or hall >= 0)
                        else "FLAG" if gate
                        else "FAIL"
                    ),
                    "dirac_claim_scope": "band_effect_not_photon_or_rest_mass_claim",
                })
            output.append(row)
    return output


def _fft(values: list[complex]) -> list[complex]:
    n = len(values)
    if n == 0 or n & (n - 1):
        raise ValueError("FFT length must be a positive power of two.")
    a = list(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    length = 2
    while length <= n:
        angle = -2.0 * math.pi / length
        wlen = complex(math.cos(angle), math.sin(angle))
        for i in range(0, n, length):
            w = 1 + 0j
            half = length // 2
            for k in range(i, i + half):
                u = a[k]
                v = a[k + half] * w
                a[k] = u + v
                a[k + half] = u - v
                w *= wlen
        length <<= 1
    return a


def _stft_band_signal(
    values: list[float],
    nperseg: int,
    noverlap: int,
    half_bins: int,
) -> tuple[list[float], int, list[list[float]]]:
    hop = nperseg - noverlap
    if hop <= 0:
        raise ValueError("STFT overlap must be smaller than window.")
    if len(values) < nperseg:
        raise ValueError("Raw signal is shorter than one STFT window.")
    frames = []
    spectra = []
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (nperseg - 1)) for i in range(nperseg)]
    for start in range(0, len(values) - nperseg + 1, hop):
        segment = [values[start + i] * window[i] for i in range(nperseg)]
        spec = _fft([complex(x, 0.0) for x in segment])[:nperseg // 2 + 1]
        power = [(abs(x) ** 2) / nperseg for x in spec]
        spectra.append(power)
    mean_power = [statistics.fmean(frame[k] for frame in spectra) for k in range(len(spectra[0]))]
    peak = max(range(1, len(mean_power)), key=lambda k: mean_power[k])
    lo = max(0, peak - half_bins)
    hi = min(len(mean_power), peak + half_bins + 1)
    for power in spectra:
        frames.append(statistics.fmean(power[lo:hi]))
    return frames, peak, spectra


def _run_intervals(labels: list[str], frame_seconds: float) -> list[dict]:
    if not labels:
        return []
    result = []
    start = 0
    current = labels[0]
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != current:
            result.append({
                "zone": current,
                "start_frame": start,
                "end_frame": i - 1,
                "frames": i - start,
                "start_seconds": start * frame_seconds,
                "end_seconds": i * frame_seconds,
                "duration_seconds": (i - start) * frame_seconds,
            })
            if i < len(labels):
                current = labels[i]
                start = i
    return result


def qnetwork_detect_raw(
    rows: list[dict],
    value_field: str,
    fs_hz: float,
    nperseg: int,
    noverlap: int,
    half_bins: int,
    seed: int,
) -> tuple[list[dict], dict]:
    values = [as_float(r, value_field) for r in rows]
    values = [x for x in values if x is not None]
    band, peak, spectra = _stft_band_signal(values, nperseg, noverlap, half_bins)
    derivatives = [0.0] + [band[i] - band[i - 1] for i in range(1, len(band))]
    dphi = [math.atan2(d, max(abs(s), 1e-15)) for d, s in zip(derivatives, band)]
    plv = [abs(math.cos(x)) for x in dphi]
    local_std = []
    w = max(5, min(21, len(band)))
    for i in range(len(band)):
        seg = band[max(0, i - w + 1):i + 1]
        local_std.append(statistics.pstdev(seg) if len(seg) > 1 else 0.0)
    std95 = quantile(local_std, 0.95) if local_std else 1.0
    C = [clamp(1.0 - s / max(std95, 1e-15), 0.0, 1.0) for s in local_std]
    broadband = [statistics.fmean(p[1:]) for p in spectra]
    contrast = [b / max(bb, 1e-15) for b, bb in zip(band, broadband)]
    contrast95 = quantile(contrast, 0.95)
    qeff = [clamp(x / max(contrast95, 1e-15), 0.0, 1.0) for x in contrast]
    qc = [clamp(q * p * c, 0.0, 1.0) for q, p, c in zip(qeff, plv, C)]

    rng = random.Random(seed)
    scrambled = list(band)
    rng.shuffle(scrambled)
    sham_bin = max(1, min(len(spectra[0]) - 1, peak + max(half_bins * 4, 20)))
    sham = [p[sham_bin] for p in spectra]
    null = []
    for series in (scrambled, sham):
        deriv = [0.0] + [series[i] - series[i - 1] for i in range(1, len(series))]
        phase = [math.atan2(d, max(abs(s), 1e-15)) for d, s in zip(deriv, series)]
        p = [abs(math.cos(x)) for x in phase]
        st = [statistics.pstdev(series[max(0, i - w + 1):i + 1]) if i > 0 else 0.0
              for i in range(len(series))]
        s95 = quantile(st, 0.95) if st else 1.0
        cc = [clamp(1.0 - x / max(s95, 1e-15), 0.0, 1.0) for x in st]
        null.extend(clamp(pv * cv, 0.0, 1.0) for pv, cv in zip(p, cc))
    B_hi = quantile(null, 0.95)
    S_lo = quantile(null, 0.20)
    labels = ["K" if x >= B_hi else "F" if x <= S_lo else "R" for x in qc]
    dwell_min = max(5, math.ceil(0.01 * len(labels)))
    # Remove short islands by assigning them to the preceding label where possible.
    intervals = _run_intervals(labels, 1.0)
    for interval in intervals:
        if interval["frames"] < dwell_min:
            replacement = labels[interval["start_frame"] - 1] if interval["start_frame"] > 0 else (
                labels[interval["end_frame"] + 1] if interval["end_frame"] + 1 < len(labels) else "R"
            )
            for i in range(interval["start_frame"], interval["end_frame"] + 1):
                labels[i] = replacement

    hop = nperseg - noverlap
    frame_seconds = hop / fs_hz
    output = []
    for i in range(len(qc)):
        output.append({
            "record_id": f"QNET-{i + 1:06d}",
            "frame": i,
            "time_seconds": i * frame_seconds,
            "band_power": band[i],
            "dphi_rad": dphi[i],
            "PLV_tau": plv[i],
            "C": C[i],
            "Q_eff_TSM153": qeff[i],
            "Q_c_TSM153": qc[i],
            "zone": labels[i],
        })
    intervals = _run_intervals(labels, frame_seconds)
    summary = {
        "frames": len(output),
        "fs_hz": fs_hz,
        "nperseg": nperseg,
        "noverlap": noverlap,
        "hop": hop,
        "frame_seconds": frame_seconds,
        "peak_bin": peak,
        "half_bins": half_bins,
        "B_hi_null_q95": B_hi,
        "S_lo_null_q20": S_lo,
        "threshold_gap": B_hi - S_lo,
        "dwell_min_frames": dwell_min,
        "zone_shares": {
            z: labels.count(z) / len(labels) if labels else 0.0
            for z in ("K", "R", "F")
        },
        "intervals": intervals,
        "gate_ok": (B_hi - S_lo) >= 0.2 and any(
            x["zone"] == "K" and x["frames"] >= dwell_min for x in intervals
        ),
        "claim_scope": "signal_pipeline_detector_not_dark_resonance_proof",
    }
    return output, summary


def qnetwork_feature_rows(rows: list[dict], profile: dict) -> list[dict]:
    evaluated = q_formula_rows(rows, profile)
    null_values = [
        as_float(r, "null_score") for r in evaluated
        if as_float(r, "null_score") is not None
    ]
    if not null_values:
        null_values = [
            as_float(r, "Q_c_TSM153") for r in evaluated
            if as_float(r, "Q_c_TSM153") is not None
        ]
    B_hi = quantile(null_values, 0.95) if null_values else 1.0
    S_lo = quantile(null_values, 0.20) if null_values else 0.0
    labels = []
    for row in evaluated:
        qc = as_float(row, "Q_c_TSM153")
        label = "" if qc is None else "K" if qc >= B_hi else "F" if qc <= S_lo else "R"
        row["zone_TSM153"] = label
        row["B_hi_TSM153"] = B_hi
        row["S_lo_TSM153"] = S_lo
        labels.append(label)
    return evaluated


def resonance_birth_rows(rows: list[dict], profile: dict) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    N = int(profile["simulation"]["regime"]["N_dwell"])
    zones = [_zone_family(_get_zone(r)) for r in rows]
    future_run = [0] * len(rows)
    for i in range(len(rows) - 1, -1, -1):
        if zones[i] in {"K", "K+"}:
            future_run[i] = 1 + (
                future_run[i + 1] if i + 1 < len(rows) and zones[i + 1] in {"K", "K+"} else 0
            )
    output = []
    previous_zone = None
    previous_qhat = None
    for i, source in enumerate(rows):
        row = dict(source)
        zone = zones[i]
        transition = (
            previous_zone in {"R", "F"} and zone in {"K", "K+"}
        ) or (previous_zone == "K" and zone == "K+")
        C = as_float(row, "C")
        dphi = as_float(row, "dphi_rad")
        qhat = as_float(row, "Qhat")
        slope = None if qhat is None or previous_qhat is None else qhat - previous_qhat
        pext = as_float(row, "P_ext_frac")
        plv = as_float(row, "PLV_tau")
        if plv is None and dphi is not None:
            plv = abs(math.cos(dphi))
        try:
            lock = parse_bool(row.get("tau_lock"))
        except ValueError:
            lock = None
        f_event = (
            C is not None and dphi is not None and qhat is not None and slope is not None
            and C < 0.2 and abs(dphi) >= eps and 0.2 <= qhat <= 0.3
            and slope < 0 and lock is True
        )
        seed = as_text(row, "seed")
        config_hash = as_text(row, "config_hash")
        requirements = {
            "P_ext_frac": pext is not None,
            "dphi_rad": dphi is not None,
            "tau_lock": lock is not None,
            "zone": zone is not None,
            "seed": seed is not None,
            "config_hash": config_hash is not None,
        }
        if not all(requirements.values()):
            event = None
            status = "not_evaluable_missing:" + ",".join(k for k, v in requirements.items() if not v)
        else:
            event = (
                pext <= 0.01
                and abs(dphi) <= eps
                and lock is True
                and plv is not None and plv >= 0.6
                and transition
                and future_run[i] >= N
                and not f_event
            )
            status = "event" if event else "no_event"
        row.update({
            "zone_transition_ok": transition,
            "future_K_dwell": future_run[i],
            "afterfield_ok_derived": future_run[i] >= N,
            "F_event_derived": f_event,
            "resonance_birth_event": "" if event is None else event,
            "resonance_birth_status": status,
        })
        output.append(row)
        if zone is not None:
            previous_zone = zone
        if qhat is not None:
            previous_qhat = qhat
    return output


def justice_profile_rows(rows: list[dict]) -> list[dict]:
    score_map = {"F+": 0.0, "F": 0.2, "R↓": 0.4, "R": 0.5, "R↑": 0.6, "K": 0.8, "K+": 1.0}
    output = []
    zones = []
    for source in rows:
        row = dict(source)
        zone = _get_zone(row)
        if zone == "fragmentiert":
            zone = "F"
        elif zone == "regulativ":
            zone = "R"
        elif zone == "kohärent":
            zone = "K"
        if zone not in score_map:
            row["justice_status"] = "not_evaluable_unknown_zone"
        else:
            score = score_map[zone]
            row["G155_zone"] = zone
            row["G155_zone_score"] = score
            row["justice_status"] = "mapped_system_level"
            row["justice_person_scoring_forbidden"] = True
            zones.append(zone)
        output.append(row)
    shares = {z: zones.count(z) / len(zones) if zones else 0.0 for z in score_map}
    for row in output:
        row["G155_zone_shares"] = json.dumps(shares, ensure_ascii=False, sort_keys=True)
    return output


def urk_rows(rows: list[dict], profile: dict) -> list[dict]:
    cfg = profile["operations"]["urk"]
    max_ref = float(cfg["R_URK_global_window"][1])
    allowed_levels = set(cfg["levels"])
    output = []
    for source in rows:
        row = dict(source)
        direct = as_float(row, "R_URK_hat")
        f_return = as_float(row, "F_return")
        f_grav = as_float(row, "F_grav")
        lambda_u = as_float(row, "lambda_U")
        K_u = as_float(row, "K_U")
        gest = as_float(row, "G_est")
        gobs = as_float(row, "G_obs")
        modes = {}
        if direct is not None:
            modes["supplied"] = direct
        if f_return is not None and f_grav is not None and f_grav != 0:
            modes["force_ratio"] = f_return / f_grav
        if lambda_u is not None and K_u is not None:
            modes["lambda_K"] = lambda_u * K_u
        if gest is not None and gobs is not None and gest != 0:
            modes["comparison_residual"] = (gobs - gest) / abs(gest)
        uncertainty = as_float(row, "uncertainty")
        source_ref = as_text(row, "source")
        timestamp = as_text(row, "timestamp")
        level = as_text(row, "level")
        if not modes:
            row["URK_window_status"] = "not_evaluable_missing_numeric_input"
            row["URK_audit_status"] = "FAIL"
        else:
            row["URK_modes"] = json.dumps(modes, sort_keys=True)
            primary_mode = as_text(row, "URK_mode") or next(iter(modes))
            value = modes.get(primary_mode)
            if value is None:
                row["URK_window_status"] = "not_evaluable_unknown_mode"
                row["URK_audit_status"] = "FAIL"
            else:
                row["R_URK_hat"] = value
                row["R_URK_abs"] = abs(value)
                row["R_URK_max_ref"] = max_ref
                within = 0.0 <= abs(value) <= max_ref
                row["URK_window_status"] = "within_global_window" if within else "outside_global_window"
                metadata_complete = (
                    uncertainty is not None and source_ref is not None
                    and timestamp is not None and level in allowed_levels
                )
                row["URK_audit_status"] = (
                    "FAIL" if not within
                    else "PASS" if metadata_complete
                    else "FLAG"
                )
        row["URK_claim_scope"] = "upper_bound_reference_not_measured_constant"
        output.append(row)
    return output


def srk_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        s_return = as_float(row, "S_return")
        s_structure = as_float(row, "S_structure")
        upper = as_float(row, "R_SRK_max")
        source_ref = as_text(row, "source")
        timestamp = as_text(row, "timestamp")
        context_hash = as_text(row, "context_hash")
        if s_return is None or s_structure is None or s_structure == 0:
            row["SRK_status"] = "not_evaluable_missing_or_zero_structure"
        else:
            value = s_return / s_structure
            row["R_SRK_hat"] = value
            if upper is None:
                row["SRK_window"] = "unbounded_reference_marker_missing"
                status = "FLAG"
            else:
                row["SRK_window"] = "within_marker" if 0 <= value <= upper else "outside_marker"
                status = "PASS" if 0 <= value <= upper else "FAIL"
            if not (source_ref and timestamp and context_hash):
                status = "FLAG" if status != "FAIL" else status
            row["SRK_status"] = status
            row["SRK_claim_scope"] = "social_resonance_marker_not_measured_constant"
        output.append(row)
    return output


def interface_profile_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        C = as_float(row, "C")
        S = as_float(row, "S")
        dphi = as_float(row, "dphi_rad")
        tau = as_float(row, "tau")
        C0 = as_float(row, "C_baseline")
        S0 = as_float(row, "S_baseline")
        tau0 = as_float(row, "tau_baseline")
        if None in (C, S, dphi, tau):
            row["interface_status"] = "not_evaluable_missing_C_S_dphi_or_tau"
        else:
            phase_pi2_distance = abs(abs(dphi) - math.pi / 2)
            row["interface_phase_pi2_distance"] = phase_pi2_distance
            row["interface_opening"] = (
                (C0 is None or C < C0)
                and (S0 is None or S > S0)
                and phase_pi2_distance <= 0.2
                and (tau0 is None or tau > tau0)
            )
            rebind = as_float(row, "C_next")
            row["interface_rebinding"] = rebind is not None and rebind > C
            row["interface_status"] = (
                "OPENING" if row["interface_opening"]
                else "REBINDING" if row["interface_rebinding"]
                else "STABLE_OR_UNCLEAR"
            )
        output.append(row)
    return output


def kappa_tau_rows(rows: list[dict], alpha_override: float | None = None) -> list[dict]:
    output = []
    products = []
    for source in rows:
        row = dict(source)
        kappa_geom = as_float(row, "kappa_geom")
        kappa_ent = as_float(row, "kappa_ent")
        kappa = as_float(row, "kappa")
        if kappa is None and (kappa_geom is not None or kappa_ent is not None):
            kappa = (kappa_geom or 0.0) + (kappa_ent or 0.0)
        alpha = alpha_override if alpha_override is not None else as_float(row, "alpha_norm")
        tau_obs = as_float(row, "tau")
        K = as_float(row, "K")
        dtau_dt = as_float(row, "dtau_dt")
        row["kappa"] = "" if kappa is None else kappa
        row["alpha_norm"] = "" if alpha is None else alpha
        if alpha is None or alpha <= 0:
            row["kappa_tau_status"] = "not_evaluable_missing_or_invalid_alpha"
        elif kappa is None or kappa <= 0:
            if tau_obs is not None and tau_obs > 0:
                row["kappa_from_tau"] = 1.0 / (alpha * tau_obs)
                row["kappa_tau_status"] = "inverse_transformation_only"
            else:
                row["kappa_tau_status"] = "not_evaluable_missing_or_invalid_kappa"
        else:
            tau_calc = 1.0 / (alpha * kappa)
            row["tau_from_kappa"] = tau_calc
            if tau_obs is not None:
                row["tau_mapping_residual"] = tau_obs - tau_calc
            if K is not None and tau_obs is not None:
                product = K * tau_obs
                products.append(product)
                row["K_tau_product"] = product
                row["kappa_proxy"] = K / (tau_obs * tau_obs) if tau_obs != 0 else ""
            if dtau_dt is not None:
                row["tau_time_compatibility"] = "provided"
            row["kappa_tau_status"] = "evaluated"
        output.append(row)
    if products:
        mean = statistics.fmean(products)
        sd = statistics.pstdev(products) if len(products) > 1 else 0.0
        cv = None if mean == 0 else sd / abs(mean)
        for row in output:
            row["K_tau_series_mean"] = mean
            row["K_tau_series_cv"] = "" if cv is None else cv
            row["K_tau_invariance_status"] = (
                "stable_candidate" if cv is not None and cv <= 0.05 else "variable"
            )
    return output


def asymmetry_rows(rows: list[dict]) -> list[dict]:
    output = []
    diffs = []
    for source in rows:
        row = dict(source)
        pplus = as_float(row, "P_plus")
        pminus = as_float(row, "P_minus")
        if pplus is None or pminus is None:
            row["asymmetry_status"] = "not_evaluable_missing_P_plus_or_P_minus"
        else:
            diff = pplus - pminus
            diffs.append(diff)
            row["A_phi_tau_local"] = diff
            row["asymmetry_status"] = "evaluated"
        output.append(row)
    if diffs:
        mean = statistics.fmean(diffs)
        uncertainty = statistics.pstdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
        for row in output:
            row["A_phi_tau"] = mean
            row["A_phi_tau_standard_error"] = uncertainty
    return output


def urf_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        question = as_text(row, "question")
        observations = as_text(row, "observations")
        candidates = as_text(row, "candidate_causes")
        counter = as_text(row, "counterevidence")
        missing = [
            name for name, value in [
                ("question", question), ("observations", observations),
                ("candidate_causes", candidates), ("counterevidence", counter)
            ] if value is None
        ]
        row["URF_steps"] = json.dumps([
            "1_problem", "2_observations", "3_backtrace", "4_candidate_causes",
            "5_counterevidence", "6_tests", "7_revision", "8_report"
        ])
        row["URF_status"] = "FAIL_missing:" + ",".join(missing) if missing else "PASS_ready"
        output.append(row)
    return output


def multiscale_rows(rows: list[dict]) -> list[dict]:
    allowed = {"micro", "meso", "macro"}
    output = []
    groups: dict[str, list[float]] = {}
    for source in rows:
        row = dict(source)
        level = as_text(row, "level")
        value = as_float(row, "value")
        source_ref = as_text(row, "source")
        if level not in allowed or value is None or source_ref is None:
            row["multiscale_status"] = "not_evaluable_missing_or_invalid_level_value_source"
        else:
            groups.setdefault(level, []).append(value)
            row["multiscale_status"] = "PASS"
        output.append(row)
    summary = {
        level: {
            "n": len(values),
            "mean": statistics.fmean(values),
            "min": min(values),
            "max": max(values),
        }
        for level, values in groups.items()
    }
    for row in output:
        row["multiscale_summary"] = json.dumps(summary, sort_keys=True)
    return output


def gru_rows(rows: list[dict], profile: dict) -> list[dict]:
    eps = float(profile["numeric"]["epsilon_rad"])
    output = []
    for source in rows:
        row = dict(source)
        C = as_float(row, "C")
        dphi = as_float(row, "dphi_rad")
        tau = as_float(row, "tau")
        coeff = as_float(row, "delta_g_coefficient")
        if None in (C, dphi, tau):
            row["GRU_status"] = "not_evaluable_missing_C_dphi_or_tau"
        else:
            geometry_score = C * abs(math.cos(dphi)) * tau / max(abs(dphi), eps)
            row["GRU_geometry_score"] = geometry_score
            if coeff is None:
                row["GRU_delta_g"] = ""
                row["GRU_status"] = "PASS_resonance_geometry_only"
            else:
                row["GRU_delta_g"] = coeff * geometry_score
                row["GRU_status"] = "PASS_physical_proxy_with_supplied_coefficient"
            row["GRU_claim_scope"] = "translation_not_direct_gravity_measurement"
        output.append(row)
    return output


def translate_validate_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        symbolic = as_text(row, "symbolic")
        technical = as_text(row, "technical")
        core = as_text(row, "resonance_core")
        level = as_text(row, "level")
        missing = [x for x, v in [("symbolic", symbolic), ("technical", technical),
                                  ("resonance_core", core)] if v is None]
        row["translation_loss"] = bool(missing)
        row["translation_status"] = (
            "FAIL_missing:" + ",".join(missing) if missing
            else "FLAG_missing_level" if level is None
            else "PASS"
        )
        output.append(row)
    return output


def discourse_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        phenomena = [as_float(row, name) for name in
                     ["invisibility", "ridicule", "info_gatekeeping", "double_bind", "blame_reversal"]]
        speech = [as_float(row, name) for name in ["SK1", "SK2", "SK3", "SK4"]]
        rate = as_float(row, "lambda_rate")
        rate_base = as_float(row, "lambda_baseline")
        plv_drop = as_float(row, "delta_PLV_tau")
        phase_sigma = as_float(row, "phase_sigma")
        phase_sigma_base = as_float(row, "phase_sigma_baseline")
        c_drop = as_float(row, "delta_C")
        if any(x is None for x in phenomena + speech):
            row["discourse_status"] = "not_evaluable_missing_quick_check_scores"
        else:
            discourse_score = sum(phenomena)
            speech_cost = sum(speech)
            taktflut = (
                rate is not None and rate_base is not None and rate_base > 0 and rate >= 2 * rate_base
            ) or (plv_drop is not None and plv_drop <= -0.05) or (
                phase_sigma is not None and phase_sigma_base is not None
                and phase_sigma >= 1.5 * phase_sigma_base
            ) or (c_drop is not None and c_drop <= -0.10)
            row["discourse_score"] = discourse_score
            row["speech_cost_score"] = speech_cost
            row["taktflut_detected"] = taktflut
            row["discourse_intervention"] = discourse_score >= 6 or speech_cost >= 4 or taktflut
            row["discourse_status"] = "INTERVENE" if row["discourse_intervention"] else "MONITOR"
            row["recommended_tools"] = (
                "24h_pulse_reset;slotting;safe_channel;four_sentence_statement"
                if row["discourse_intervention"] else "continue_monitoring"
            )
        output.append(row)
    return output


def information_gravity_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        S = as_float(row, "S_ent")
        Sstar = as_float(row, "S_star")
        lam = as_float(row, "lambda_ent")
        g_id = as_text(row, "g_function_id")
        g_value = as_float(row, "g_value")
        kgeom = as_float(row, "kappa_geom") or 0.0
        if None in (S, Sstar, lam) or Sstar == 0 or g_id is None or g_value is None:
            row["information_gravity_status"] = "not_evaluable_requires_versioned_g_and_inputs"
        else:
            kent = lam * g_value
            row["S_ent_ratio"] = S / Sstar
            row["kappa_ent"] = kent
            row["kappa_total"] = kgeom + kent
            row["information_gravity_status"] = "evaluated_supplied_g_only"
            row["information_gravity_claim_scope"] = "conditional_transformation_not_empirical_gravity_claim"
        output.append(row)
    return output



def _norm_label(value: Any) -> str:
    text = "" if value is None else str(value).strip().lower()
    return text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def _first_float(row: dict, *fields: str) -> float | None:
    for field in fields:
        value = as_float(row, field)
        if value is not None:
            return value
    return None


def _normalized_axis(row: dict, name: str) -> float | None:
    direct = as_float(row, f"UB_{name}_n")
    if direct is not None:
        return direct
    raw = as_float(row, f"UB_{name}_raw")
    return None if raw is None else raw / 4.0


def _ub_zone(g21a: float, B: float, S: float, guard: str) -> str:
    if guard == "STOP":
        return "F+"
    if g21a >= 0.85 and B >= 0.80 and S <= 0.20:
        return "K+"
    if g21a >= 0.70 and B >= 0.65 and S <= 0.35:
        return "K"
    if g21a >= 0.55:
        return "R↑"
    if g21a >= 0.40:
        return "R↓"
    if g21a >= 0.20:
        return "F"
    return "F+"


def _ub_external(zone: str) -> str:
    return {
        "K+": "tragfähig", "K": "tragfähig", "R↑": "nachsteuerungsbedürftig (aufwärts)",
        "R↓": "nachsteuerungsbedürftig (abwärts)", "F": "kritisch", "F+": "nicht freigabefähig",
    }.get(zone, "offen")


def universal_evaluate_rows(rows: list[dict]) -> list[dict]:
    output = []
    for source in rows:
        row = dict(source)
        axes = {name: _normalized_axis(row, name) for name in ["C", "Phi", "Tau", "H", "N", "D"]}
        override = as_float(row, "UB_Tau_override_n")
        if override is not None:
            axes["Tau"] = override
        missing = [name for name, value in axes.items() if value is None]
        invalid = [name for name, value in axes.items() if value is not None and not 0 <= value <= 1]
        if missing or invalid:
            row["UB_status"] = (
                "not_evaluable_missing:" + ",".join(missing) if missing
                else "FAIL_axis_out_of_range:" + ",".join(invalid)
            )
            output.append(row)
            continue
        C, Phi, Tau, H, N, D = (axes[x] for x in ["C", "Phi", "Tau", "H", "N", "D"])
        Tn = math.exp(-((Tau - 0.60) ** 2) / (2 * 0.15 ** 2))
        Ln = 1.0 - Phi
        B_lin = 0.40 * C + 0.30 * Tn + 0.30 * Ln
        B_geo = (C ** 0.40) * (Tn ** 0.30) * (Ln ** 0.30)
        B = 0.50 * B_lin + 0.50 * B_geo
        S = 0.50 * Phi + 0.25 * H + 0.25 * N
        delta = B - S
        g21a = D * clamp((delta + 1.0) / 2.0, 0.0, 1.0)
        g21b = D * (1.0 / (1.0 + math.exp(-4.0 * delta)))
        rrel = B / (B + S + 0.001)
        if Phi > 0.80 or N > 0.70 or D < 0.50 or C < 0.25:
            base_guard = "STOP"
        elif Phi > 0.68 or N > 0.595 or D < 0.55 or C < 0.275:
            base_guard = "CHECK"
        else:
            base_guard = "OK"
        sg = [as_float(row, f"UB_SG{i}") for i in range(1, 7)]
        if sum(x is not None for x in sg) < 6:
            protection = "OFFEN"
        elif any(x is not None and not 0 <= x <= 4 for x in sg):
            protection = "FAIL"
        else:
            vals = [float(x) for x in sg]
            if max(vals) == 4 or sum(x >= 3 for x in vals) >= 2 or vals[0] >= 3 or vals[1] >= 3 or vals[4] >= 3:
                protection = "STOP"
            elif any(x >= 2 for x in vals):
                protection = "CHECK"
            else:
                protection = "OK"
        if protection == "FAIL":
            final_guard = "STOP"
        elif base_guard == "STOP" or protection == "STOP":
            final_guard = "STOP"
        elif base_guard == "CHECK" or protection in {"CHECK", "OFFEN"}:
            final_guard = "CHECK"
        else:
            final_guard = "OK"
        base_zone = _ub_zone(g21a, B, S, base_guard)
        final_zone = "F+" if protection in {"STOP", "FAIL"} else base_zone
        external = _ub_external(base_zone)
        if protection in {"STOP", "FAIL"}:
            final_external = "nicht freigabefähig"
        elif protection in {"CHECK", "OFFEN"} and external in {"tragfähig", "nachsteuerungsbedürftig (aufwärts)"}:
            final_external = "nachsteuerungsbedürftig (abwärts)"
        else:
            final_external = external
        next_step = (
            "Schutz / Unterbrechung und Rückbindungsplan starten" if final_guard == "STOP"
            else "Nur mit aktivem Schutz- und Rückbindungsplan weiterarbeiten" if final_guard == "CHECK"
            else "Freigabe mit Review-Termin" if final_external == "tragfähig"
            else "Nachsteuerung mit Rückprüfung anlegen"
        )
        expected = as_float(row, "UB_evidence_expected")
        filled = as_float(row, "UB_evidence_filled")
        supplied_grade = as_float(row, "UB_evidence_grade")
        evidence_grade = supplied_grade if supplied_grade is not None else (
            filled / expected if filled is not None and expected not in {None, 0} else None
        )
        history = [_norm_label(row.get(f"UB_HL{i}")) for i in range(1, 11)]
        active_history = [x for x in history if x and x not in {"nicht anwendbar", "nicht_anwendbar", "n/a"}]
        if not active_history:
            history_status = "nicht bewertet"
        elif any(x == "kritisch" for x in active_history):
            history_status = "Rückfallmuster erkennbar"
        elif sum(x == "offen" for x in active_history) >= max(1, len(active_history) / 2):
            history_status = "Verbesserungslinie offen"
        elif sum(x in {"erfuellt", "erfüllt"} for x in active_history) >= max(3, len(active_history) / 2):
            history_status = "Verbesserungslinie erkennbar"
        else:
            history_status = "Verbesserungslinie teilweise erkennbar"
        row.update({
            **{f"UB_{name}_n": value for name, value in axes.items()},
            "UB_T_n": Tn, "UB_L_n": Ln, "UB_B_lin": B_lin, "UB_B_geo": B_geo,
            "UB_B": B, "UB_S": S, "UB_Delta": delta, "UB_G21a": g21a, "UB_G21b": g21b,
            "UB_R_rel": rrel, "UB_base_guard": base_guard, "UB_protection_status": protection,
            "UB_final_guard": final_guard, "UB_base_zone": base_zone, "UB_final_zone": final_zone,
            "UB_final_external_status": final_external, "UB_next_step": next_step,
            "UB_evidence_grade": "" if evidence_grade is None else clamp(evidence_grade, 0.0, 1.0),
            "UB_historical_learning_status": history_status, "UB_status": "evaluated",
            "UB_claim_scope": "structured_single_case_assessment_not_automatic_decision",
        })
        output.append(row)
    return output


_GP_LEVELS = {
    1: ("Weniger Not", 1.60), 2: ("Weniger Angst", 1.50), 3: ("Weniger Willkür", 1.40),
    4: ("Weniger Intransparenz", 1.30), 5: ("Weniger Ungerechtigkeit", 1.20),
    6: ("Weniger Ohnmacht / mehr Freiheit", 1.10), 7: ("Mehr Gedeihlichkeit / gemeinsame Zukunft", 1.00),
}


def _gp_level(row: dict) -> tuple[int | None, str | None, float | None]:
    raw_id = as_float(row, "GP_level_id")
    if raw_id is not None and int(raw_id) in _GP_LEVELS:
        level_id = int(raw_id)
        name, factor = _GP_LEVELS[level_id]
        return level_id, name, factor
    text = _norm_label(row.get("GP_level"))
    for level_id, (name, factor) in _GP_LEVELS.items():
        if text == _norm_label(name):
            return level_id, name, factor
    return None, None, None


def pyramid_evaluate_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    output = []
    evaluated = []
    risk_map = {"niedrig": 0.25, "mittel": 0.50, "hoch": 0.75, "sehr hoch": 1.0, "sehr_hoch": 1.0}
    for source in rows:
        row = dict(source)
        level_id, level_name, default_factor = _gp_level(row)
        assessment_text = str(row.get("GP_assessment", "")).strip()
        if level_id is None:
            row["GP_status"] = "not_evaluable_unknown_level"
            output.append(row); continue
        if assessment_text in {"", "?"}:
            row.update({"GP_level_id": level_id, "GP_level": level_name, "GP_status": "not_evaluable_unclear_assessment"})
            output.append(row); continue
        try:
            assessment = float(assessment_text.replace(",", "."))
        except ValueError:
            row["GP_status"] = "not_evaluable_invalid_assessment"; output.append(row); continue
        certainty = as_float(row, "GP_certainty_pct")
        factor = as_float(row, "GP_position_factor")
        factor = default_factor if factor is None else factor
        if assessment not in {-2.0, -1.0, 0.0, 1.0, 2.0} or factor <= 0 or (certainty is not None and not 0 <= certainty <= 100):
            row["GP_status"] = "FAIL_input_out_of_range"; output.append(row); continue
        path = (2.0 - assessment) / 4.0
        urgency = path * factor
        weighted = "" if certainty is None else assessment * (certainty / 100.0) * factor
        urgency_status = "niedrig" if urgency < 0.01 else "gering" if urgency < 0.35 else "mittel" if urgency < 0.65 else "erhöht" if urgency < 1.0 else "hoch"
        risk_text = _norm_label(row.get("GP_rollback_risk"))
        risk = as_float(row, "GP_rollback_risk")
        if risk is None:
            risk = risk_map.get(risk_text)
        row.update({
            "GP_level_id": level_id, "GP_level": level_name, "GP_assessment": assessment,
            "GP_position_factor": factor, "GP_path_length": path, "GP_urgency": urgency,
            "GP_weighted_change": weighted, "GP_urgency_status": urgency_status,
            "GP_review_flag": certainty is None or certainty < 60,
            "GP_rollback_risk_norm": "" if risk is None else clamp(risk, 0.0, 1.0),
            "GP_status": "evaluated", "GP_claim_scope": "reflective_path_profile_not_ranking",
        })
        output.append(row); evaluated.append(row)
    priorities = sorted(evaluated, key=lambda r: float(r["GP_urgency"]), reverse=True)
    longest = max(evaluated, key=lambda r: float(r["GP_path_length"])) if evaluated else None
    lowest_cert = min((r for r in evaluated if as_float(r, "GP_certainty_pct") is not None), key=lambda r: float(r["GP_certainty_pct"]), default=None)
    highest_risk = max((r for r in evaluated if as_float(r, "GP_rollback_risk_norm") is not None), key=lambda r: float(r["GP_rollback_risk_norm"]), default=None)
    summary = {
        "status": "PASS" if len(evaluated) == 7 else "FLAG_incomplete_levels",
        "rows": len(rows), "evaluated_levels": len(evaluated),
        "GP_highest_urgency_level": priorities[0]["GP_level"] if priorities else None,
        "GP_longest_path_level": longest["GP_level"] if longest else None,
        "GP_average_path_length": statistics.fmean(float(r["GP_path_length"]) for r in evaluated) if evaluated else None,
        "GP_lowest_certainty_pct": as_float(lowest_cert, "GP_certainty_pct") if lowest_cert else None,
        "GP_highest_rollback_risk": as_float(highest_risk, "GP_rollback_risk_norm") if highest_risk else None,
        "GP_priority_order": [r["GP_level"] for r in priorities],
    }
    return output, summary


def _label_norm(value: Any, mapping: dict[str, float], default: float = 0.0) -> float:
    direct = None
    try:
        if value is not None and str(value).strip() != "":
            direct = float(str(value).replace(",", "."))
    except ValueError:
        pass
    if direct is not None:
        return clamp(direct, 0.0, 1.0)
    return mapping.get(_norm_label(value), default)


def bundle_evaluate_rows(rows: list[dict], interactions: list[dict] | None, scenario: str) -> tuple[list[dict], dict]:
    risk_map = {"niedrig": .25, "mittel": .5, "hoch": .75, "sehr hoch": 1.0, "sehr_hoch": 1.0}
    protection_map = {"keine": 0.0, "weich": .5, "hart": 1.0, "ok": 0.0, "check": .5, "offen": .5, "stop": 1.0}
    fit_map = {"schwach": .25, "mittel": .5, "stark": .75, "sehr stark": 1.0, "sehr_stark": 1.0}
    ethics_map = {"kritisch": .25, "unklar": .5, "tragfaehig": .75, "sehr tragfaehig": 1.0}
    source_map = {"offen": .25, "unsicher": .35, "gemischt": .6, "gut": .85, "sehr gut": 1.0, "sehr_gut": 1.0}
    evidence_map = {"metaanalyse/review": 1.0, "amtliche quelle": .85, "daten/statistik": .8, "expert:innenurteil": .55, "medienbericht": .45, "annahme/illustration": .3}
    scenarios = {
        "baseline": (1.0,1.0,1.0,1.0,0.0),
        "mit_rueckholmassnahmen": (1.05,.9,.85,.8,-.25),
        "worst_case": (.9,1.15,1.2,1.2,.25),
        "best_case": (1.1,.85,.8,.75,-.5),
    }
    if scenario not in scenarios:
        raise ValueError(f"Unknown bundle scenario: {scenario}")
    interaction_values: dict[str, list[float]] = {}
    contradiction_count = 0; edge_count = 0
    for edge in interactions or []:
        src = as_text(edge, "BK_source_id"); dst = as_text(edge, "BK_target_id"); value = as_float(edge, "BK_interaction")
        if not src or not dst or value is None or src == dst or not -3 <= value <= 3:
            continue
        norm = value / 3.0
        interaction_values.setdefault(src, []).append(norm); interaction_values.setdefault(dst, []).append(norm)
        edge_count += 1; contradiction_count += value < 0
    output = []
    for source in rows:
        row = dict(source)
        point_id = as_text(row, "BK_point_id")
        B = as_float(row, "BK_B"); S = as_float(row, "BK_S"); rest = as_float(row, "BK_pyramid_restway")
        certainty = as_float(row, "BK_certainty_pct")
        if not point_id or None in (B,S,rest,certainty) or not (0 <= B <= 1 and 0 <= S <= 1 and 0 <= rest <= 1 and 0 <= certainty <= 100):
            row["BK_status"] = "not_evaluable_missing_or_invalid_core_inputs"; output.append(row); continue
        risk = _label_norm(row.get("BK_rollback_risk"), risk_map)
        protection_label = _norm_label(row.get("BK_protection_warning"))
        protection = _label_norm(row.get("BK_protection_warning"), protection_map)
        synergy = _label_norm(row.get("BK_synergy_potential"), risk_map)
        conflict = _label_norm(row.get("BK_conflict_potential"), risk_map)
        key_fit = _label_norm(row.get("BK_key_fit"), fit_map)
        ethics = _label_norm(row.get("BK_ethics_compatibility"), ethics_map, .5)
        reliability = _label_norm(row.get("BK_source_reliability"), source_map, .25)
        cert = certainty / 100.0
        pressure = clamp(.4*rest + .25*risk + .25*protection + .1*(1-cert), 0, 1)
        coherence = clamp(.35*key_fit + .25*synergy + .25*ethics + .15*reliability, 0, 1)
        bridge = clamp(.5*B + .25*(1-S) + .25*(1-rest), 0, 1)
        inter = statistics.fmean(interaction_values.get(point_id, [0.0]))
        hard = protection_label in {"hart", "stop"}
        detail = "gesperrt" if hard else (
            "kohärent gedeihlich" if bridge >= .65 and pressure < .35 and ethics >= .65 else
            "formal tragfähig / ethisch fragmentiert" if B >= .65 and ethics < .5 else
            "ethisch plausibel / resonanztechnisch instabil" if ethics >= .65 and (B < .35 or pressure >= .65) else
            "Rückholplan erforderlich" if pressure >= .65 or bridge < .35 else "regulativer Übergang"
        )
        status = "gesperrt" if hard else "fragmentiert" if pressure >= .75 and coherence < .5 else "rückholpflichtig" if pressure >= .65 else "kohärent" if coherence >= .65 and pressure < .35 else "regulativ"
        priority = 5 if hard else max(1, math.ceil(clamp(.55*pressure + .25*(1-coherence) + .2*max(0,inter),0,1)*5))
        evidence = evidence_map.get(_norm_label(row.get("BK_evidence_type")), .5)
        cmin = as_float(row, "BK_confidence_min"); cmax = as_float(row, "BK_confidence_max")
        span = None if cmin is None or cmax is None else cmax-cmin
        uncertainty = .15*(1-evidence)+.05*(1-cert)
        bf,sf,rf,riskf,pcorr = scenarios[scenario]
        sB = clamp(B*bf,0,1); sS=clamp(S*sf,0,1); srest=clamp(rest*rf,0,1); srisk=clamp(risk*riskf,0,1); sprot=clamp(protection+pcorr,0,1)
        scenario_pressure = clamp(.4*srest+.25*srisk+.25*sprot+.1*(1-cert),0,1)
        scenario_bridge = clamp(.5*sB+.25*(1-sS)+.25*(1-srest),0,1)
        row.update({
            "BK_rollback_norm": risk, "BK_protection_norm": protection, "BK_certainty_factor": cert,
            "BK_synergy_norm": synergy, "BK_conflict_norm": conflict, "BK_key_fit_norm": key_fit,
            "BK_ethics_norm": ethics, "BK_source_reliability_norm": reliability,
            "BK_pressure": pressure, "BK_coherence": coherence, "BK_bridge": bridge,
            "BK_interaction_pressure": inter, "BK_detail_status": detail, "BK_status": status,
            "BK_return_priority": priority, "BK_evidence_norm": evidence,
            "BK_confidence_span": "" if span is None else span,
            "BK_pressure_min": max(0,pressure-uncertainty), "BK_pressure_max": min(1,pressure+uncertainty),
            "BK_evidence_weighted_pressure": pressure*(.75+.25*evidence),
            "BK_validation_note": "hohe Unsicherheit" if span is not None and span > .35 else "Evidenz schwach" if evidence < .5 else "ok",
            "BK_scenario": scenario, "BK_scenario_pressure": scenario_pressure, "BK_scenario_bridge": scenario_bridge,
            "BK_claim_scope": "heuristic_bundle_analysis_not_mathematical_proof",
        })
        output.append(row)
    active = [r for r in output if as_float(r,"BK_B") is not None and as_float(r,"BK_pressure") is not None]
    if active:
        center = {
            "B": statistics.fmean(float(r["BK_B"]) for r in active),
            "G": statistics.fmean(1-float(r["BK_pyramid_restway"]) for r in active),
            "P": statistics.fmean(float(r["BK_pressure"]) for r in active),
        }
        distances=[]; outliers=[]
        for row in active:
            dist=math.sqrt((float(row["BK_B"])-center["B"])**2+((1-float(row["BK_pyramid_restway"]))-center["G"])**2+(float(row["BK_pressure"])-center["P"])**2)
            row["BK_distance_to_center"]=dist; row["BK_outlier_flag"]=dist>.35
            distances.append(dist); outliers.append(dist>.35)
        scatter=statistics.fmean(distances); outlier_share=sum(outliers)/len(outliers); contradiction_share=contradiction_count/edge_count if edge_count else 0.0
        fragmentation=clamp(.4*scatter+.3*outlier_share+.3*contradiction_share,0,1)
        hard_any=any(_norm_label(r.get("BK_protection_warning")) in {"hart","stop"} for r in active)
        hull="ethisch gesperrt" if hard_any else "kompakt-kohärent" if fragmentation<.35 else "regulativ-gestreut" if fragmentation<.65 else "randlastig" if outlier_share>.5 else "fragmentiert"
    else:
        center={"B":None,"G":None,"P":None}; scatter=outlier_share=contradiction_share=fragmentation=None; hull="keine Daten"
    summary={
        "status":"PASS" if active else "FAIL_no_evaluable_points", "points":len(active), "scenario":scenario,
        "center":center, "scatter":scatter, "outlier_share":outlier_share,
        "contradiction_share":contradiction_share, "fragmentation_index":fragmentation,
        "hull_status":hull,
        "top_return_points":[r.get("BK_point_id") for r in sorted(active,key=lambda x:int(x["BK_return_priority"]),reverse=True)[:5]],
    }
    return output,summary


def operational_namespace_audit(bundle: dict, rows: list[dict] | None = None) -> dict:
    registry=bundle.get("operational_namespaces",{})
    required=set(registry.get("required_prefixes",{}).values())
    ambiguous=set(registry.get("ambiguous_unqualified_fields",[]))
    registry_ok=required=={"UB_","GP_","BK_","TF_"}
    violations=[]
    for index,row in enumerate(rows or [],start=1):
        source=_norm_label(row.get("source_tool") or row.get("BK_source_tool"))
        for key in row:
            if key in ambiguous:
                violations.append({"row":index,"field":key,"reason":"ambiguous_unqualified_field","source_tool":source})
    return {"status":"PASS" if registry_ok and not violations else "FAIL","required_prefixes":sorted(required),"violations":violations}


def bundle_import_audit_rows(rows: list[dict]) -> list[dict]:
    output=[]
    for source in rows:
        row=dict(source); tool=_norm_label(row.get("BK_source_tool") or row.get("source_tool"))
        if tool in {"ub","universalbewertung","tsm-universalbewertung"}:
            required=["UB_B","UB_S","UB_final_guard","UB_protection_status"]
        elif tool in {"gp","gedeihlichkeitspyramide","pyramide"}:
            required=["GP_average_path_length","GP_highest_urgency_level"]
        elif tool in {"manual","manuell"}:
            required=["BK_B","BK_S","BK_pyramid_restway"]
        else:
            required=[]
        missing=[f for f in required if row.get(f) in {None,""}]
        mapping_ok=all(row.get(f) not in {None,""} for f in ["source_field","target_field","scale","evidence_status"]) if tool not in {"manual","manuell"} else True
        row["BK_import_audit_status"]="PASS" if required and not missing and mapping_ok else "FAIL"
        row["BK_import_missing"]=";".join(missing)
        row["BK_import_mapping_ok"]=mapping_ok
        output.append(row)
    return output


def tool_family_audit(root: Path, bundle: dict, reference_dir: Path | None = None) -> dict:
    registry = bundle.get("tool_family_registry", {})
    canonical = registry.get("canonical_file")
    profiles = registry.get("orchestration_profiles", [])
    tf_profile = bundle.get("tool_family_multiscale_profile", {})
    checks = {
        "canonical_file_present": bool(canonical and (root / canonical).exists()),
        "three_tools_registered": len(registry.get("tools", [])) == 3,
        "namespaces_complete": {x.get("namespace") for x in registry.get("tools", [])} == {"UB_", "GP_", "BK_"},
        "commands_specified": all(x.get("command") for x in registry.get("tools", [])),
        "reference_artifacts_optional": all(not x.get("required_for_package_validation", True) for x in registry.get("reference_artifacts", [])),
        "multiscale_profile_registered": len(profiles) == 1 and profiles[0].get("profile_id") == "TF-MULTISCALE-01",
        "multiscale_profile_not_fourth_tool": tf_profile.get("is_fourth_tool") is False,
        "TF_namespace_registered": tf_profile.get("prefix") == "TF_",
    }
    text = (root / canonical).read_text(encoding="utf-8") if checks["canonical_file_present"] else ""
    checks["canonical_sections_present"] = all(marker in text for marker in [
        "# Teil A – TSM-Universalbewertung", "# Teil B – Gedeihlichkeitspyramide",
        "# Teil C – TSM-Bündelkompass", "## 2. Verbindliche Namensräume",
        "# Teil E – Mehrskaliges Durchblickprofil", "## 31. Verbindlicher Namensraum",
    ])
    reference_results = []
    if reference_dir:
        for item in registry.get("reference_artifacts", []):
            path = reference_dir / item["filename"]
            reference_results.append({
                "filename": item["filename"],
                "present": path.exists(),
                "hash_ok": path.exists() and sha256_file(path) == item["sha256"],
            })
        checks["reference_hashes_ok"] = all(x["hash_ok"] for x in reference_results)
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "status": status, "checks": checks, "reference_verification": reference_results,
        "claim_scope": "internal_tool_family_and_multiscale_profile_integrity",
    }



_TF_STATUS_RANK = {
    "blocked": 0,
    "counteracting": 0,
    "strained": 1,
    "carried": 2,
}


def _tf_source_fields(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value is None:
        return []
    return [x.strip() for x in re.split(r"[;,]", str(value)) if x.strip()]


def _tf_default_scale_order(bundle: dict) -> dict[str, float]:
    profile = bundle.get("tool_family_multiscale_profile", {})
    return {
        str(item.get("scale_id")): float(item.get("order"))
        for item in profile.get("default_scale_catalogue", [])
        if item.get("scale_id") is not None and item.get("order") is not None
    }


def _tf_derive_local_status(row: dict, bundle: dict) -> str:
    allowed = set(bundle.get("tool_family_multiscale_profile", {}).get("scale_status_catalogue", []))
    explicit = as_text(row, "TF_local_status")
    if explicit in allowed:
        return explicit
    tool = (as_text(row, "TF_source_tool") or "").upper()
    mapping = bundle.get("tool_family_multiscale_profile", {}).get("status_mapping", {})
    if tool == "UB":
        raw = as_text(row, "UB_final_guard") or as_text(row, "UB_protection_status") or as_text(row, "TF_source_status")
        return mapping.get("UB", {}).get(str(raw).upper(), "not_evaluable") if raw else "not_evaluable"
    if tool == "BK":
        raw = as_text(row, "BK_protection_status") or as_text(row, "BK_protection_warning") or as_text(row, "TF_protection_status") or as_text(row, "TF_source_status")
        if raw:
            mapped = mapping.get("BK", {}).get(str(raw), mapping.get("BK", {}).get(str(raw).upper()))
            if mapped:
                return mapped
        status = _norm_label(row.get("BK_status") or row.get("TF_source_status"))
        if any(x in status for x in ["gesperrt", "blocked", "stop", "hart"]):
            return "blocked"
        if any(x in status for x in ["check", "fragil", "regulativ", "strained"]):
            return "strained"
        if any(x in status for x in ["pass", "ok", "kohärent", "kohaerent", "tragfähig", "tragfaehig", "carried"]):
            return "carried"
    return "not_evaluable"


def _tf_hard_protection(row: dict) -> bool:
    values = [
        row.get("TF_protection_status"), row.get("UB_protection_status"), row.get("UB_final_guard"),
        row.get("BK_protection_status"), row.get("BK_protection_warning"),
    ]
    return any(_norm_label(v) in {"stop", "hart", "hard", "blocked"} for v in values if v not in {None, ""})


def _tf_framework_checks(root: Path, bundle: dict) -> tuple[dict[str, bool], dict[str, Any]]:
    profile = bundle.get("tool_family_multiscale_profile", {})
    wf = root / str(profile.get("canonical_file", ""))
    framework = root / str(profile.get("framework_file", ""))
    wf_text = wf.read_text(encoding="utf-8") if wf.is_file() else ""
    framework_text = framework.read_text(encoding="utf-8") if framework.is_file() else ""
    props = bundle.get("field_schema", {}).get("properties", {})
    registry_names = {x.get("name") for x in bundle.get("field_schema", {}).get("x-tsm-field-registry", [])}
    required_fields = list(profile.get("required_fields", []))
    operations = bundle.get("operation_specs", {})
    required_dimensions = set(profile.get("required_dimensions", []))
    checks = {
        "profile_present": bool(profile),
        "canonical_file_present": wf.is_file(),
        "framework_file_present": framework.is_file(),
        "not_fourth_tool": profile.get("is_fourth_tool") is False,
        "TF_prefix": profile.get("prefix") == "TF_",
        "required_dimensions_complete": required_dimensions == {"unit", "channel", "scale", "time", "source_tool", "mapper", "evidence", "protection"},
        "required_fields_declared": len(required_fields) >= 22 and len(required_fields) == len(set(required_fields)),
        "required_fields_in_schema": set(required_fields).issubset(props),
        "required_fields_in_registry": set(required_fields).issubset(registry_names),
        "namespace_registered": "TF_" in set(bundle.get("operational_namespaces", {}).get("required_prefixes", {}).values()),
        "three_commands_specified": set(profile.get("commands", [])) == {"tool-family-map-audit", "tool-family-map", "tool-family-map-compare"},
        "operation_specs_present": {"tool_family_map_audit", "tool_family_map", "tool_family_map_compare"}.issubset(operations),
        "no_new_scoring_formula": profile.get("policies", {}).get("no_new_scoring_formula") is True,
        "group_scoring_forbidden": profile.get("policies", {}).get("group_scoring_forbidden") is True,
        "groups_are_perspectives_only": profile.get("policies", {}).get("groups_are_affected_perspectives_only") is True,
        "structural_reach_profile_first": profile.get("policies", {}).get("structural_reach_is_profile_first") is True,
        "candidate_thresholds_noncanonical": profile.get("candidate_baselines", {}).get("status") == "configurable_E1_E2_not_canonical_thresholds",
        "framework_section_17_present": "## 17. Mehrskaliges Durchblickprofil der TSM-Werkzeugfamilie" in framework_text,
        "tool_family_part_E_present": "# Teil E – Mehrskaliges Durchblickprofil" in wf_text,
        "tool_family_sections_30_42_present": all(f"## {n}." in wf_text for n in range(30, 43)),
        "physical_nonidentity_documented": "keine Phasendifferenz" in framework_text and "kein physikalisches Feld" in framework_text,
        "group_scoring_boundary_documented": "nicht der Wert, Charakter oder Rang einer Gruppe" in framework_text,
    }
    details = {
        "profile_id": profile.get("profile_id"),
        "required_fields": required_fields,
        "commands": profile.get("commands", []),
        "candidate_baselines_enabled": profile.get("candidate_baselines", {}).get("enabled_by_default"),
    }
    return checks, details


def _tf_input_audit(rows: list[dict], bundle: dict) -> dict:
    profile = bundle.get("tool_family_multiscale_profile", {})
    required = list(profile.get("required_fields", []))
    allowed_tools = {str(x).upper() for x in profile.get("allowed_source_tools", [])}
    allowed_evidence = {"E0", "E1", "E2", "E3-light", "E3", "E4"}
    allowed_protection = {"OK", "CHECK", "STOP", "OFFEN", "none", "soft", "hard", "open"}
    allowed_map_status = set(profile.get("map_status_catalogue", []))
    physical = set(bundle.get("operational_namespaces", {}).get("physical_fields_must_not_be_auto_mapped", []))
    row_results = []
    map_ids = []
    for index, source in enumerate(rows, start=1):
        row = dict(source)
        missing = [f for f in required if row.get(f) is None or (isinstance(row.get(f), str) and not row.get(f).strip())]
        reasons = []
        if missing:
            reasons.append("missing_required_fields:" + ",".join(missing))
        tool = (as_text(row, "TF_source_tool") or "").upper()
        if tool not in allowed_tools:
            reasons.append("invalid_source_tool")
        source_fields = _tf_source_fields(row.get("TF_source_fields"))
        if not source_fields:
            reasons.append("source_fields_missing")
        absent_source_fields = [f for f in source_fields if f not in row or row.get(f) is None or row.get(f) == ""]
        if absent_source_fields:
            reasons.append("named_source_fields_absent:" + ",".join(absent_source_fields))
        if tool in {"UB", "GP", "BK"} and any(not f.startswith(tool + "_") for f in source_fields):
            reasons.append("source_field_namespace_mismatch")
        if physical.intersection(source_fields):
            reasons.append("physical_field_auto_mapping_forbidden")
        mapper = as_text(row, "TF_mapper_id") or ""
        if mapper and not re.search(r"(?:^|[-_:])v?\d+(?:\.\d+)*$", mapper, flags=re.IGNORECASE):
            reasons.append("mapper_not_versioned")
        parsed_times = []
        for time_field in ("TF_time_start", "TF_time_end"):
            raw_time = as_text(row, time_field)
            try:
                parsed_times.append(datetime.fromisoformat(raw_time.replace("Z", "+00:00")) if raw_time else None)
            except ValueError:
                parsed_times.append(None)
                reasons.append("invalid_" + time_field.lower())
        if len(parsed_times) == 2 and all(parsed_times) and parsed_times[0] > parsed_times[1]:
            reasons.append("time_start_after_time_end")
        evidence = as_text(row, "TF_evidence_grade")
        if evidence not in allowed_evidence:
            reasons.append("invalid_evidence_grade")
        protection = as_text(row, "TF_protection_status")
        if protection not in allowed_protection:
            reasons.append("invalid_protection_status")
        map_status = as_text(row, "TF_map_status")
        if map_status not in allowed_map_status:
            reasons.append("invalid_map_status")
        unit_type = _norm_label(row.get("TF_unit_type"))
        if any(token in unit_type for token in ["bevölkerungsgruppe", "bevoelkerungsgruppe", "nutzergruppe", "population_group", "user_group"]):
            if not any(token in unit_type for token in ["perspektive", "perspective", "wirkungsperspektive", "betroffenenperspektive"]):
                reasons.append("prohibited_group_scoring_unit_type")
        if tool == "manual" and not as_text(row, "TF_local_status"):
            reasons.append("manual_requires_explicit_local_status")
        if map_status == "released" and reasons:
            reasons.append("released_map_contains_fail_closed_violation")
        map_id = as_text(row, "TF_map_id")
        if map_id:
            map_ids.append(map_id)
        row_results.append({
            "row": index,
            "map_id": map_id,
            "unit_id": as_text(row, "TF_unit_id"),
            "status": "PASS" if not reasons else "FAIL",
            "reasons": reasons,
        })
    checks = {
        "rows_present": len(rows) > 0,
        "all_rows_pass": all(x["status"] == "PASS" for x in row_results),
        "map_ids_present": len(map_ids) == len(rows),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "row_results": row_results,
        "rows": len(rows),
    }


def tool_family_map_audit(root: Path, bundle: dict, rows: list[dict] | None = None) -> dict:
    checks, details = _tf_framework_checks(root, bundle)
    input_result = None
    if rows is not None:
        input_result = _tf_input_audit(rows, bundle)
        checks["input_rows_pass"] = input_result["status"] == "PASS"
    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "input_audit": input_result,
        "claim_scope": "multiscale_tool_family_profile_integrity_not_empirical_validation",
    }


def tool_family_map_rows(rows: list[dict], bundle: dict) -> tuple[list[dict], dict]:
    audit = _tf_input_audit(rows, bundle)
    by_index = {x["row"]: x for x in audit["row_results"]}
    scale_order_default = _tf_default_scale_order(bundle)
    output = []
    for index, source in enumerate(rows, start=1):
        row = dict(source)
        result = by_index[index]
        reasons = list(result["reasons"])
        row["TF_row_audit_status"] = result["status"]
        row["TF_fail_closed_reason"] = ";".join(reasons)
        local_status = _tf_derive_local_status(row, bundle)
        row["TF_local_status"] = local_status
        row["TF_local_protection_flag"] = _tf_hard_protection(row)
        row["TF_local_evidence_flag"] = as_text(row, "TF_evidence_grade") in {"E0", "E1"}
        if row.get("TF_scale_order") in {None, ""}:
            default_order = scale_order_default.get(as_text(row, "TF_scale_id") or "")
            row["TF_scale_order"] = "" if default_order is None else default_order
        if reasons:
            if any("mapper" in r or "source_field" in r or "physical_field" in r for r in reasons):
                row["TF_map_status"] = "mapping_blocked"
            elif any("protection" in r for r in reasons):
                row["TF_map_status"] = "protection_open"
            else:
                row["TF_map_status"] = "incomplete_map"
        output.append(row)

    # Channel conflicts: same unit/scale/time, different channel statuses.
    context_groups: dict[tuple, list[int]] = {}
    for i, row in enumerate(output):
        key = (row.get("TF_map_id"), row.get("TF_unit_id"), row.get("TF_scale_id"), row.get("TF_time_id"))
        context_groups.setdefault(key, []).append(i)
    channel_conflicts = []
    for key, indexes in context_groups.items():
        statuses = {output[i].get("TF_local_status") for i in indexes if output[i].get("TF_local_status") not in {None, "", "not_evaluable"}}
        channels = {output[i].get("TF_channel_id") for i in indexes}
        conflict = len(channels) > 1 and len(statuses) > 1
        if conflict:
            channel_conflicts.append({"key": key, "channels": sorted(str(x) for x in channels), "statuses": sorted(statuses)})
        for i in indexes:
            output[i]["TF_channel_conflict"] = conflict

    # Structural reach profiles and conservative scale breaks.
    reach_groups: dict[tuple, list[int]] = {}
    for i, row in enumerate(output):
        key = (row.get("TF_map_id"), row.get("TF_unit_id"), row.get("TF_channel_id"), row.get("TF_time_id"))
        reach_groups.setdefault(key, []).append(i)
    reach_profiles = []
    scale_breaks = []
    for key, indexes in reach_groups.items():
        ordered = sorted(indexes, key=lambda i: (as_float(output[i], "TF_scale_order") is None, as_float(output[i], "TF_scale_order") or 0, str(output[i].get("TF_scale_id"))))
        profile_parts = [f"{output[i].get('TF_scale_id')}={output[i].get('TF_local_status')}" for i in ordered]
        profile_text = "; ".join(profile_parts)
        for i in ordered:
            output[i]["TF_structural_reach_profile"] = profile_text
            output[i]["TF_scale_break"] = False
        previous_i = None
        for i in ordered:
            if previous_i is not None:
                prev = output[previous_i].get("TF_local_status")
                current = output[i].get("TF_local_status")
                if prev in {"carried", "strained"} and current in {"blocked", "counteracting"}:
                    output[i]["TF_scale_break"] = True
                    output[i]["TF_scale_break_from"] = output[previous_i].get("TF_scale_id")
                    output[i]["TF_scale_break_to"] = output[i].get("TF_scale_id")
                    output[i]["TF_scale_break_reason"] = f"{prev}->{current}"
                    scale_breaks.append({
                        "map_id": key[0], "unit_id": key[1], "channel_id": key[2], "time_id": key[3],
                        "from": output[previous_i].get("TF_scale_id"), "to": output[i].get("TF_scale_id"),
                        "transition": f"{prev}->{current}",
                    })
            previous_i = i
        reach_profiles.append({
            "map_id": key[0], "unit_id": key[1], "channel_id": key[2], "time_id": key[3],
            "profile": profile_text,
        })

    # Local-global gap only when aggregate and local roles coexist.
    map_time_groups: dict[tuple, list[int]] = {}
    for i, row in enumerate(output):
        map_time_groups.setdefault((row.get("TF_map_id"), row.get("TF_time_id")), []).append(i)
    local_global = []
    for key, indexes in map_time_groups.items():
        locals_ = [i for i in indexes if (output[i].get("TF_scope_role") or "local") == "local"]
        aggregates = [i for i in indexes if output[i].get("TF_scope_role") == "aggregate"]
        gap = "not_evaluable"
        if locals_ and aggregates:
            local_hard = any(output[i].get("TF_local_protection_flag") for i in locals_)
            aggregate_blocked = all(output[i].get("TF_local_status") == "blocked" for i in aggregates)
            local_statuses = {output[i].get("TF_local_status") for i in locals_}
            aggregate_statuses = {output[i].get("TF_local_status") for i in aggregates}
            if local_hard and not aggregate_blocked:
                gap = "protection_relevant"
            elif local_statuses != aggregate_statuses:
                gap = "high"
            else:
                gap = "none"
        for i in indexes:
            output[i]["TF_local_global_gap"] = gap
        local_global.append({"map_id": key[0], "time_id": key[1], "status": gap})

    summary = {
        "profile_id": bundle.get("tool_family_multiscale_profile", {}).get("profile_id"),
        "rows": len(output),
        "row_audit_status": audit["status"],
        "map_ids": sorted({str(x.get("TF_map_id")) for x in output if x.get("TF_map_id") not in {None, ""}}),
        "units": len({(x.get("TF_map_id"), x.get("TF_unit_id")) for x in output}),
        "channels": sorted({str(x.get("TF_channel_id")) for x in output if x.get("TF_channel_id") not in {None, ""}}),
        "scales": sorted({str(x.get("TF_scale_id")) for x in output if x.get("TF_scale_id") not in {None, ""}}),
        "time_ids": sorted({str(x.get("TF_time_id")) for x in output if x.get("TF_time_id") not in {None, ""}}),
        "protection_hotspots": [x.get("TF_unit_id") for x in output if x.get("TF_local_protection_flag")],
        "evidence_gaps": [x.get("TF_unit_id") for x in output if x.get("TF_local_evidence_flag")],
        "channel_conflicts": channel_conflicts,
        "scale_breaks": scale_breaks,
        "structural_reach_profiles": reach_profiles,
        "local_global_gaps": local_global,
        "universal_total_score_created": False,
        "claim_scope": "structured_multiscale_orchestration_not_automatic_decision",
    }
    return output, summary


def tool_family_map_compare_rows(left_rows: list[dict], right_rows: list[dict], bundle: dict) -> tuple[list[dict], dict]:
    left, left_summary = tool_family_map_rows(left_rows, bundle)
    right, right_summary = tool_family_map_rows(right_rows, bundle)
    def key(row: dict) -> tuple[str, str, str, str]:
        return (str(row.get("TF_map_id", "")), str(row.get("TF_unit_id", "")), str(row.get("TF_channel_id", "")), str(row.get("TF_scale_id", "")))
    left_by = {key(x): x for x in left}
    right_by = {key(x): x for x in right}
    output = []
    counts: dict[str, int] = {}
    for item_key in sorted(set(left_by) | set(right_by)):
        a = left_by.get(item_key)
        b = right_by.get(item_key)
        if a is None or b is None:
            shift = "not_evaluable"
            reason = "unmatched_unit_channel_scale"
        elif a.get("TF_scale_definition") != b.get("TF_scale_definition") or a.get("TF_mapper_id") != b.get("TF_mapper_id"):
            shift = "method_changed"
            reason = "scale_definition_or_mapper_changed"
        elif a.get("TF_row_audit_status") != "PASS" or b.get("TF_row_audit_status") != "PASS":
            shift = "not_evaluable"
            reason = "input_audit_failed"
        else:
            sa = a.get("TF_local_status")
            sb = b.get("TF_local_status")
            if sa == sb:
                shift = "stable"
                reason = "same_status"
            elif sa in _TF_STATUS_RANK and sb in _TF_STATUS_RANK:
                shift = "improved" if _TF_STATUS_RANK[sb] > _TF_STATUS_RANK[sa] else "worsened" if _TF_STATUS_RANK[sb] < _TF_STATUS_RANK[sa] else "mixed"
                reason = f"{sa}->{sb}"
            else:
                shift = "uncertain"
                reason = f"nonordered_status:{sa}->{sb}"
        counts[shift] = counts.get(shift, 0) + 1
        output.append({
            "TF_map_id": item_key[0], "TF_unit_id": item_key[1], "TF_channel_id": item_key[2], "TF_scale_id": item_key[3],
            "TF_left_time_id": "" if a is None else a.get("TF_time_id", ""),
            "TF_right_time_id": "" if b is None else b.get("TF_time_id", ""),
            "TF_left_status": "" if a is None else a.get("TF_local_status", ""),
            "TF_right_status": "" if b is None else b.get("TF_local_status", ""),
            "TF_temporal_shift": shift, "TF_compare_reason": reason,
            "TF_protection_changed": None if a is None or b is None else bool(a.get("TF_local_protection_flag")) != bool(b.get("TF_local_protection_flag")),
        })
    summary = {
        "rows": len(output), "status_counts": counts,
        "left_audit": left_summary.get("row_audit_status"), "right_audit": right_summary.get("row_audit_status"),
        "automatic_change_claims_blocked_on_method_change": True,
        "claim_scope": "conservative_time_comparison_not_causal_attribution",
    }
    return output, summary


def write_tf_output(path: Path, records: list[dict], summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps({"records": records, "summary": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        write_rows(path, records)
        sidecar = path.with_name(path.stem + "_summary.json")
        sidecar.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown_numbered_sections(text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"^#{2,6}\s+(\d+(?:\.\d+)*)\b", text, flags=re.MULTILINE)
    }


def _markdown_publication_rows(text: str) -> list[dict]:
    role_map = {
        "kanonische Regelquelle": "canonical_source",
        "stützende Veröffentlichung": "supporting_publication",
        "Fallstudie": "case_study",
    }
    rows = []
    in_registry = False
    for line in text.splitlines():
        if line.startswith("### 16.2 "):
            in_registry = True
            continue
        if in_registry and line.startswith("### 16.3 "):
            break
        if not in_registry or not line.startswith("| `SRC-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        source_id = cells[0].strip("`")
        doi = cells[2].strip("`")
        sections = [x.strip() for x in cells[4].replace("§§", "").split(",") if x.strip()]
        rows.append({
            "source_id": source_id,
            "title": cells[1],
            "doi": doi,
            "registry_role": role_map.get(cells[3], cells[3]),
            "supports_sections": sections,
        })
    return rows


def _parse_meta01_connection_rows(text: str) -> list[dict]:
    rows = []
    pattern = re.compile(
        r"^\*\*((?:TSM-\d{3}D?|META-\d{2}|SM-\d{2})) — .*? \| Sek\.: .*? \| "
        r"Wirkebenen: (.*?) \| Text-PV: (.*?) \| Text-SV: (.*?) \| Text-Spiegel: (.*?) \| "
        r"Kur-PV: (.*?) \| Kur-SV: (.*?) \| Kur-Spiegel: (.*?) \| Kur-Komplement: (.*?) \| "
        r"Kur-Vertiefung: (.*?)\*\*$"
    )
    def split_plain(value: str) -> list[str]:
        value = value.strip()
        return [] if value == "—" else [x.strip() for x in value.split(" · ") if x.strip()]
    def split_curated(value: str) -> list[dict]:
        value = value.strip()
        if value == "—":
            return []
        out = []
        for token in [x.strip() for x in value.split(" · ") if x.strip()]:
            m = re.fullmatch(r"((?:TSM-\d{3}D?|META-\d{2}|SM-\d{2}))\[(K-H|K-M)\]", token)
            if not m:
                out.append({"id": token, "confidence": "INVALID"})
            else:
                out.append({"id": m.group(1), "confidence": "high" if m.group(2) == "K-H" else "medium"})
        return out
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        rows.append({
            "id": m.group(1),
            "wirkungsebenen": split_plain(m.group(2)),
            "explicit": {"PV": split_plain(m.group(3)), "SV": split_plain(m.group(4)), "mirror": split_plain(m.group(5))},
            "curated": {
                "PV": split_curated(m.group(6)), "SV": split_curated(m.group(7)),
                "mirror": split_curated(m.group(8)), "complement": split_curated(m.group(9)),
                "deepening": split_curated(m.group(10)),
            },
        })
    return rows


def curated_connection_audit(root: Path, bundle: dict) -> dict:
    registry = bundle.get("curated_connection_registry", {})
    module_entries = bundle.get("module_registry", {}).get("entries", [])
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    families = ("PV", "SV", "mirror", "complement", "deepening")
    reciprocal_families = ("mirror", "complement", "deepening")
    try:
        known = {x.get("id") for x in module_entries}
        canonical = root / str(registry.get("canonical_file", ""))
        checks["registry_present"] = bool(registry)
        checks["canonical_file_present"] = canonical.is_file()
        text = canonical.read_text(encoding="utf-8") if canonical.is_file() else ""
        md_rows = _parse_meta01_connection_rows(text)
        md_by_id = {x["id"]: x for x in md_rows}
        json_by_id = {x["id"]: x for x in module_entries}
        checks["markdown_rows_209"] = len(md_rows) == 209
        checks["markdown_ids_unique"] = len(md_rows) == len(md_by_id)
        checks["markdown_json_ids_match"] = set(md_by_id) == set(json_by_id)

        allowed_levels = set(registry.get("wirkungsebenen", []))
        expected_levels = {
            "Physik", "Biologie / Medizin", "Technik", "Gesellschaft",
            "Bewusstsein / Wahrnehmung", "Sprache / Kommunikation", "Kunst / Symbolik",
            "Erkenntnis / Logik", "Spiritualität / Religion", "Raum-Zeit-Geometrie",
        }
        checks["wirkungsebenen_catalogue_complete"] = allowed_levels == expected_levels
        expected_relation_types = {"PV", "SV", "mirror", "complement", "deepening"}
        checks["relation_type_catalogue_complete"] = set(registry.get("relation_types", {})) == expected_relation_types

        unknown_refs = []
        self_links = []
        duplicate_links = []
        invalid_confidence = []
        invalid_basis = []
        invalid_levels = []
        relation_maps: dict[str, dict[str, set[str]]] = {f: {} for f in reciprocal_families}
        computed_counts = {f: 0 for f in families}
        combined_adj = {x: set() for x in known}
        pair_types: dict[tuple[str, str], set[str]] = {}
        for entry in module_entries:
            id_ = entry["id"]
            levels = entry.get("wirkungsebenen", [])
            if not levels or len(levels) > 4 or any(x not in allowed_levels for x in levels):
                invalid_levels.append({"id": id_, "levels": levels})
            for family in ("PV", "SV", "mirror"):
                for ref in entry.get("index_links", {}).get(family, []):
                    if ref in known:
                        combined_adj[id_].add(ref); combined_adj[ref].add(id_)
            curated = entry.get("curated_links", {})
            for family in reciprocal_families:
                relation_maps[family][id_] = {x.get("id") for x in curated.get(family, [])}
            for family in families:
                records = curated.get(family, [])
                targets = [x.get("id") for x in records]
                computed_counts[family] += len(records)
                if len(targets) != len(set(targets)):
                    duplicate_links.append({"id": id_, "family": family, "targets": targets})
                for record in records:
                    ref = record.get("id")
                    if ref not in known:
                        unknown_refs.append({"from": id_, "family": family, "ref": ref})
                    if ref == id_:
                        self_links.append({"id": id_, "family": family})
                    if record.get("confidence") not in {"high", "medium"}:
                        invalid_confidence.append({"from": id_, "family": family, "record": record})
                    if not record.get("basis"):
                        invalid_basis.append({"from": id_, "family": family, "record": record})
                    if ref in known:
                        combined_adj[id_].add(ref); combined_adj[ref].add(id_)
                        if family in reciprocal_families:
                            pair = tuple(sorted((id_, ref)))
                            pair_types.setdefault(pair, set()).add(family)

        nonreciprocal = []
        for family, relation_map in relation_maps.items():
            for a, targets in relation_map.items():
                for b in targets:
                    if a not in relation_map.get(b, set()):
                        nonreciprocal.append({"family": family, "from": a, "to": b})
        overlapping_typologies = [{"pair": pair, "types": sorted(types)} for pair, types in pair_types.items() if len(types) > 1]
        checks["all_entries_have_valid_wirkebenen"] = not invalid_levels
        checks["curated_ids_known"] = not unknown_refs
        checks["no_self_links"] = not self_links
        checks["no_duplicate_targets_per_relation"] = not duplicate_links
        checks["confidence_values_valid"] = not invalid_confidence
        checks["relation_basis_present"] = not invalid_basis
        checks["typological_relations_reciprocal"] = not nonreciprocal
        checks["typological_relation_types_do_not_overlap"] = not overlapping_typologies

        markdown_mismatch = []
        for id_ in set(md_by_id) & set(json_by_id):
            md = md_by_id[id_]; js = json_by_id[id_]
            if md["wirkungsebenen"] != js.get("wirkungsebenen", []):
                markdown_mismatch.append({"id": id_, "field": "wirkungsebenen"})
            if any(md["explicit"][k] != js.get("index_links", {}).get(k, []) for k in ("PV", "SV", "mirror")):
                markdown_mismatch.append({"id": id_, "field": "explicit_links"})
            for family in families:
                md_pairs = [(x.get("id"), x.get("confidence")) for x in md["curated"][family]]
                js_pairs = [(x.get("id"), x.get("confidence")) for x in js.get("curated_links", {}).get(family, [])]
                if md_pairs != js_pairs:
                    markdown_mismatch.append({"id": id_, "field": f"curated_{family}"})
        checks["markdown_json_connections_match"] = not markdown_mismatch

        expected_counts = registry.get("counts", {})
        computed_registry_counts = {"entries": len(module_entries)}
        for family in families:
            computed_registry_counts[f"curated_{family}_directed"] = computed_counts[family]
            if family in reciprocal_families:
                computed_registry_counts[f"curated_{family}_pairs"] = computed_counts[family] // 2
            computed_registry_counts[f"entries_with_curated_{family}"] = sum(bool(x.get("curated_links", {}).get(family)) for x in module_entries)
        computed_registry_counts["entries_with_wirkebenen"] = sum(bool(x.get("wirkungsebenen")) for x in module_entries)
        computed_registry_counts["entries_with_any_curated_relation"] = sum(any(x.get("curated_links", {}).get(f) for f in families) for x in module_entries)
        checks["registry_counts_consistent"] = expected_counts == computed_registry_counts

        density = registry.get("density_policy", {})
        checks["no_fixed_relation_quota_declared"] = density.get("no_fixed_relation_quota") is True
        checks["no_fixed_minimum_or_maximum_declared"] = density.get("no_fixed_minimum_or_maximum_per_entry") is True
        pv_counts = [len(x.get("curated_links", {}).get("PV", [])) for x in module_entries]
        sv_counts = [len(x.get("curated_links", {}).get("SV", [])) for x in module_entries]
        observed = density.get("current_observed_maxima", {})
        checks["observed_density_metadata_consistent"] = observed == {"PV": max(pv_counts, default=0), "SV": max(sv_counts, default=0)}
        checks["PV_distribution_not_quota_shaped"] = len(set(pv_counts)) > 2 and 0 in pv_counts
        checks["SV_distribution_not_quota_shaped"] = len(set(sv_counts)) > 2 and 0 in sv_counts
        checks["typological_relations_are_optional"] = density.get("typological_relations_optional") is True
        checks["deepening_axis_direction_rule_declared"] = "Richtung folgt aus den Modultexten" in str(registry.get("relation_types", {}).get("deepening", ""))

        # Combined graph connectivity and diameter.
        unseen = set(known); components = []
        while unseen:
            start = next(iter(unseen)); q = [start]; unseen.remove(start); comp=[]
            while q:
                node=q.pop();comp.append(node)
                for nb in combined_adj[node]:
                    if nb in unseen: unseen.remove(nb);q.append(nb)
            components.append(comp)
        graph_quality = registry.get("graph_quality", {})
        checks["combined_graph_connected"] = len(components) == 1 and graph_quality.get("combined_graph_connected") is True
        diameter = None
        if len(components) == 1:
            diameter = 0
            for start in known:
                dist={start:0};q=deque([start])
                while q:
                    node=q.popleft()
                    for nb in combined_adj[node]:
                        if nb not in dist:dist[nb]=dist[node]+1;q.append(nb)
                diameter=max(diameter,max(dist.values()))
        checks["combined_graph_diameter_within_limit"] = diameter is not None and diameter <= int(graph_quality.get("maximum_allowed_diameter", 8)) and diameter == graph_quality.get("combined_graph_diameter")
        checks["all_entries_have_at_least_one_combined_connection"] = all(combined_adj[x] for x in known)

        centrality = registry.get("centrality_controls", {}).get("META-10", {})
        meta10_sources = sorted({x["id"] for x in module_entries for f in families for r in x.get("curated_links", {}).get(f, []) if r.get("id") == "META-10"})
        checks["META10_relevance_gate_consistent"] = meta10_sources == sorted(centrality.get("allowed_incoming_sources", []))
        checks["META10_not_overcentralized"] = len(meta10_sources) <= int(centrality.get("max_curated_incoming", 15))

        authority = registry.get("authority", {})
        checks["authority_layer_separation_declared"] = (
            authority.get("actual_module_texts_remain_primary") is True
            and authority.get("explicit_links_are_text_derived") is True
            and authority.get("curated_links_are_navigation_not_original_module_statements") is True
            and authority.get("curated_links_are_not_empirical_validation") is True
        )
        marker_scheme = registry.get("markdown_markers", {})
        meta_section = text[text.find("**Version:**"):] if "**Version:**" in text else text
        checks["curated_marker_scheme_is_K_prefixed"] = marker_scheme == {"high": "K-H", "medium": "K-M"}
        checks["curated_markers_present"] = "[K-H]" in meta_section and "[K-M]" in meta_section
        checks["no_ambiguous_bare_H_or_M_in_curated_index"] = not re.search(
            r"(?:Kur-PV|Kur-SV|Kur-Spiegel|Kur-Komplement|Kur-Vertiefung):[^\n]*(?<!K-)\[(?:H|M)\]", meta_section
        )
        usage = registry.get("usage_hierarchy", {})
        checks["usage_hierarchy_declared"] = (
            usage.get("module_text_determines_meaning") is True
            and usage.get("explicit_links_have_priority") is True
            and usage.get("curated_links_are_navigation_only") is True
            and usage.get("no_claim_from_curated_link_alone") is True
            and usage.get("selected_neighbor_requires_module_text") is True
            and usage.get("curated_confidence_is_not_claim_or_evidence") is True
            and usage.get("symbolic_numeric_bridges_only_when_relevant") is True
        )
        checks["usage_hierarchy_present_in_markdown"] = all(phrase in meta_section for phrase in (
            "Der tatsächliche Modultext bestimmt Bedeutung",
            "Explizite Textverbindungen haben Vorrang",
            "Eine inhaltliche Aussage darf nicht allein aus einer kuratierten Verbindung abgeleitet werden",
            "Kuratierte Plausibilität ist weder Claim-Level noch Evidenzstufe",
            "META-10 ist kein universeller Sammelknoten",
            "Das Feld selbst kodiert keine Richtung",
        ))
        details.update({
            "computed_counts": computed_registry_counts,
            "invalid_levels": invalid_levels,
            "unknown_refs": unknown_refs,
            "self_links": self_links,
            "duplicate_links": duplicate_links,
            "invalid_confidence": invalid_confidence,
            "invalid_basis": invalid_basis,
            "nonreciprocal_typological_relations": nonreciprocal,
            "overlapping_typologies": overlapping_typologies,
            "markdown_mismatch": markdown_mismatch,
            "combined_graph_component_sizes": sorted((len(x) for x in components), reverse=True),
            "combined_graph_diameter": diameter,
            "META10_incoming_sources": meta10_sources,
        })
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "details": details, "error": str(exc)}
    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {"status": status, "checks": checks, "details": details, "claim_scope": "semantic_navigation_integrity_not_empirical_truth"}


def publication_source_audit(root: Path, bundle: dict) -> dict:
    registry = bundle.get("publication_source_registry", {})
    canonical = registry.get("canonical_file")
    checks: dict[str, Any] = {}
    details: dict[str, Any] = {}
    try:
        path = root / str(canonical)
        checks["registry_present"] = bool(registry)
        checks["canonical_file_present"] = path.is_file()
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        sources = registry.get("sources", [])
        source_ids = [str(x.get("source_id", "")) for x in sources]
        dois = [str(x.get("doi", "")) for x in sources]
        roles = [str(x.get("registry_role", "")) for x in sources]
        checks["source_ids_nonempty"] = all(source_ids)
        checks["source_ids_unique"] = len(source_ids) == len(set(source_ids))
        doi_pattern = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
        checks["doi_format_valid"] = all(doi_pattern.fullmatch(x) for x in dois)
        checks["doi_urls_consistent"] = all(
            x.get("doi_url") == f"https://doi.org/{x.get('doi')}" for x in sources
        )
        allowed_roles = {"canonical_source", "supporting_publication", "case_study"}
        checks["roles_valid"] = all(x in allowed_roles for x in roles)

        expected_counts = {
            "source_ids": len(source_ids),
            "unique_dois": len(set(dois)),
            "canonical_sources": sum(x == "canonical_source" for x in roles),
            "supporting_publications": sum(x == "supporting_publication" for x in roles),
        }
        checks["counts_consistent"] = registry.get("counts", {}) == expected_counts
        details["computed_counts"] = expected_counts

        md_rows = _markdown_publication_rows(text)
        md_by_id = {x["source_id"]: x for x in md_rows}
        json_by_id = {x["source_id"]: x for x in sources}
        checks["markdown_source_ids_unique"] = len(md_rows) == len(md_by_id)
        checks["markdown_json_source_ids_match"] = set(md_by_id) == set(json_by_id)
        checks["markdown_json_dois_match"] = all(
            md_by_id[sid]["doi"] == json_by_id[sid].get("doi") for sid in set(md_by_id) & set(json_by_id)
        )
        checks["markdown_json_roles_match"] = all(
            md_by_id[sid]["registry_role"] == json_by_id[sid].get("registry_role")
            for sid in set(md_by_id) & set(json_by_id)
        )
        checks["markdown_json_sections_match"] = all(
            md_by_id[sid]["supports_sections"] == [str(x) for x in json_by_id[sid].get("supports_sections", [])]
            for sid in set(md_by_id) & set(json_by_id)
        )

        numbered_sections = _markdown_numbered_sections(text)
        section_refs = [str(s) for x in sources for s in x.get("supports_sections", [])]
        checks["supports_sections_resolve"] = all(x in numbered_sections for x in section_refs)
        details["numbered_sections"] = sorted(numbered_sections)

        framework = bundle.get("comparison_calibration_framework", {})
        framework_ids = [
            sid
            for ids in framework.get("source_ids_by_section", {}).values()
            for sid in ids
        ]
        checks["framework_source_ids_resolve"] = all(x in set(source_ids) for x in framework_ids)

        duplicate_groups: dict[str, list[str]] = {}
        for source in sources:
            duplicate_groups.setdefault(source.get("doi", ""), []).append(source.get("source_id", ""))
        duplicate_groups = {doi: ids for doi, ids in duplicate_groups.items() if len(ids) > 1}
        declared_groups = {
            item.get("doi"): sorted(item.get("source_ids", []))
            for item in registry.get("doi_reuse_groups", [])
        }
        checks["doi_reuse_groups_declared"] = {
            doi: sorted(ids) for doi, ids in duplicate_groups.items()
        } == declared_groups
        reuse_text = text[text.find("### 16.3 "):text.find("### 16.4 ")] if "### 16.3 " in text else ""
        checks["doi_reuse_documented_in_markdown"] = all(
            doi in reuse_text and all(sid in reuse_text for sid in ids)
            for doi, ids in duplicate_groups.items()
        )
        details["duplicate_doi_groups"] = duplicate_groups

        meta_file = root / "TSM_Korpus_03_Module_TSM-127-167_META-01.md"
        meta_text = meta_file.read_text(encoding="utf-8") if meta_file.is_file() else ""
        checks["meta01_doi_free"] = not bool(re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", meta_text, re.IGNORECASE))
        checks["policy_traceability_not_validation"] = registry.get("policy", {}).get("doi_is_traceability_not_validation") is True
        checks["external_online_resolution_optional"] = True
        details["external_online_resolution"] = "NOT_RUN_OFFLINE_BY_DESIGN"
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "detail": str(exc)}

    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "claim_scope": "local_registry_integrity_and_traceability_not_external_validation",
    }


def comparison_framework_audit(root: Path, bundle: dict) -> dict:
    framework = bundle.get("comparison_calibration_framework", {})
    checks: dict[str, Any] = {}
    details: dict[str, Any] = {}
    try:
        canonical = framework.get("canonical_file")
        path = root / str(canonical)
        checks["framework_present"] = bool(framework)
        checks["canonical_file_present"] = path.is_file()
        text = path.read_text(encoding="utf-8") if path.is_file() else ""

        authority = framework.get("authority", {})
        checks["module_text_authority_preserved"] = authority.get("actual_module_texts_remain_primary") is True
        checks["external_theory_priority_preserved"] = authority.get("external_reference_theory_remains_primary") is True
        checks["mapping_not_semantic_identity"] = authority.get("mapping_type") == "functional_problem_role_not_semantic_identity"
        checks["active_architecture_is_5_13_plus"] = authority.get("active_physics_architecture") == "5-13-plus" and "5-13-Plus" in text
        checks["eight_axes_are_structure_anchors"] = authority.get("published_eight_axes_role") == "structure_anchors_only"

        checks["claim_levels_complete"] = set(framework.get("claim_levels", {})) == {"S", "H", "D"}
        checks["claim_markers_present"] = all(marker in text for marker in ("[S]", "[H]", "[D]"))
        required_evidence = {"E0", "E1", "E2", "E3-light", "E3", "E4"}
        checks["evidence_levels_complete"] = set(framework.get("evidence_levels", {})) == required_evidence
        checks["evidence_markers_present"] = all(marker in text for marker in required_evidence)

        required_domains = {
            "cybernetics_and_control",
            "information_theory",
            "thermodynamics_and_nonequilibrium",
            "relativity_and_spacetime",
            "quantum_mechanics_and_qft",
            "evolution_and_evo_devo",
            "complexity_networks_self_organization",
            "cognitive_science_and_pragmatics",
            "luhmann_systems_theory",
        }
        checks["comparison_domains_complete"] = set(framework.get("comparison_domains", [])) == required_domains
        domain_markers = [
            "Kybernetik und Regelung",
            "Informationstheorie",
            "Thermodynamik und Nichtgleichgewicht",
            "Relativität und Raumzeit",
            "Quantenmechanik und Quantenfeldtheorie",
            "Evolution und Evo-Devo",
            "Komplexität, Netzwerke und Selbstorganisation",
            "Kognitionswissenschaft und Pragmatik",
            "Systemtheorie nach Luhmann",
        ]
        checks["comparison_sections_present"] = all(marker in text for marker in domain_markers)

        required_stop_rules = {"S1", "S2", "S3a", "S3b", "S4", "S5", "S6"}
        checks["proxy_stop_rules_complete"] = set(framework.get("proxy_stop_rules", {})) == required_stop_rules
        checks["proxy_stop_rules_present"] = all(re.search(rf"\|\s*{re.escape(rule)}\s*\|", text) for rule in required_stop_rules)
        required_statuses = {
            "CALC_ALLOWED", "DEMO_ONLY", "BLOCKED_PROVENANCE",
            "BLOCKED_CONTEXT", "BLOCKED_UNIDENTIFIABLE", "NOT_APPLICABLE",
        }
        checks["calculation_statuses_complete"] = set(framework.get("calculation_statuses", [])) == required_statuses
        checks["calculation_statuses_present"] = all(status in text for status in required_statuses)

        registry_ids = {
            x.get("source_id") for x in bundle.get("publication_source_registry", {}).get("sources", [])
        }
        source_map = framework.get("source_ids_by_section", {})
        checks["source_groups_nonempty"] = bool(source_map) and all(source_map.values())
        checks["source_group_ids_resolve"] = all(
            sid in registry_ids for ids in source_map.values() for sid in ids
        )
        checks["publication_registry_reference_valid"] = framework.get("publication_registry_ref") == "publication_source_registry"

        source_packages = framework.get("source_packages", [])
        checks["source_package_hashes_syntactically_valid"] = all(
            re.fullmatch(r"[0-9a-f]{64}", str(x.get("sha256", ""))) for x in source_packages
        )
        details["source_packages"] = source_packages
        details["external_source_package_verification"] = "REFERENCE_HASHES_EMBEDDED; SOURCE_PACKAGES_NOT_REQUIRED_AS_ACTIVE_CORPUS_FILES"
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "detail": str(exc)}

    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "claim_scope": "comparison_evidence_calibration_framework_integrity",
    }


def study_schema_audit(root: Path, bundle: dict) -> dict:
    """Validate the study classification contract for every study row."""
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}
    try:
        studies_path = root / bundle["profile"]["paths"]["studies_data"]
        rows = read_rows(studies_path)
        allowed_raw = {"", "true", "false"}
        valid_statuses = {
            "pending_proxy_audit",
            "released",
            "not_released",
            "quarantined",
            "blocked_missing_variable_specific_provenance",
            "blocked_context_mismatch",
            "blocked_embedded_social_record_in_C_field_duplicate_of_social_dataset",
        }
        invalid_boolean_rows = []
        invalid_status_rows = []
        inconsistent_rows = []
        status_counts: dict[str, int] = {}
        allowed_counts: dict[str, int] = {}
        for row in rows:
            record_id = row.get("record_id")
            raw = str(row.get("classification_allowed") or "").strip().lower()
            status = str(row.get("classification_status") or "").strip()
            allowed_counts[raw or "null"] = allowed_counts.get(raw or "null", 0) + 1
            status_counts[status or "blank"] = status_counts.get(status or "blank", 0) + 1
            if raw not in allowed_raw:
                invalid_boolean_rows.append({"record_id": record_id, "value": raw})
                continue
            if status not in valid_statuses:
                invalid_status_rows.append({"record_id": record_id, "value": status})
                continue
            allowed = parse_bool(raw) if raw else None
            if status == "released" and allowed is not True:
                inconsistent_rows.append({"record_id": record_id, "reason": "released_requires_true"})
            if status != "released" and allowed is not False:
                inconsistent_rows.append({"record_id": record_id, "reason": "nonreleased_requires_false"})
            if status.startswith("blocked_") and not str(row.get("audit_status") or "").startswith("blocked_"):
                inconsistent_rows.append({"record_id": record_id, "reason": "blocked_status_requires_blocked_audit_status"})
            if status == "quarantined" and row.get("dataset_group") != "quarantine":
                inconsistent_rows.append({"record_id": record_id, "reason": "quarantined_requires_quarantine_group"})

        field_schema = bundle.get("field_schema", {}).get("properties", {})
        registry = bundle.get("field_schema", {}).get("x-tsm-field-registry", [])
        registry_names = {entry.get("name") for entry in registry}
        checks["row_count_66"] = len(rows) == 66
        checks["classification_allowed_schema_boolean_or_null"] = field_schema.get("classification_allowed", {}).get("type") == ["boolean", "null"]
        checks["classification_status_schema_present"] = "classification_status" in field_schema
        checks["classification_fields_registered"] = {"classification_allowed", "classification_status"}.issubset(registry_names)
        checks["all_classification_allowed_values_valid"] = not invalid_boolean_rows
        checks["all_classification_status_values_valid"] = not invalid_status_rows
        checks["classification_status_consistent_with_permission"] = not inconsistent_rows
        details.update({
            "allowed_counts": allowed_counts,
            "status_counts": status_counts,
            "invalid_boolean_rows": invalid_boolean_rows,
            "invalid_status_rows": invalid_status_rows,
            "inconsistent_rows": inconsistent_rows,
        })
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "details": details, "error": str(exc)}
    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "claim_scope": "study_classification_schema_and_fail_closed_contract",
    }


def ai_execution_order_audit(root: Path, bundle: dict) -> dict:
    """Audit the joint AI reading key, original synthesis and compact execution order."""
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}
    try:
        system = bundle.get("ai_synthesis_system", {})
        key_path = root / str(system.get("execution_key_file", ""))
        original_path = root / str(system.get("original_synthesis_file", ""))
        checks["system_registry_present"] = bool(system)
        checks["execution_key_file_present"] = key_path.is_file()
        checks["original_synthesis_file_present"] = original_path.is_file()
        key_text = key_path.read_text(encoding="utf-8") if key_path.is_file() else ""
        original_text = original_path.read_text(encoding="utf-8") if original_path.is_file() else ""
        key_lower = key_text.lower()
        original_lower = original_text.lower()

        checks["joint_use_required"] = system.get("joint_use_required") is True
        checks["execution_key_does_not_replace_original"] = system.get("execution_key_replaces_original_synthesis") is False
        checks["original_does_not_replace_execution_key"] = system.get("original_synthesis_replaces_execution_key") is False
        checks["actual_module_text_is_semantic_authority"] = system.get("semantic_authority") == "actual_module_text"

        key_markers = [
            "# TSM-KI-Leseschlüssel und Ausführungsordnung",
            "Verbindlicher Nutzungshinweis",
            "Diese Datei enthält nicht die vollständige KI-Synthese des TSM",
            "Beide Dateien sind gemeinsam zu verwenden",
            "Keine Antwort gilt allein deshalb als abgeschlossen",
            "Dialogstatus, Bezug und frühe Pfadsteuerung",
            "Der Horizont ist **kein serieller Arbeitsablauf und keine vollständig abzuarbeitende Checkliste**",
            "Poetische Resonanz ist eine zulässige Ausdrucksqualität",
            "Vertrauen ersetzt keine Prüfung",
        ]
        checks["execution_key_core_markers_present"] = all(marker in key_text for marker in key_markers)
        checks["highest_principle_present_in_key"] = "wir lügen nicht" in key_lower and "soweit es in unserer macht steht" in key_lower
        checks["highest_principle_present_in_original"] = "wir lügen nicht" in original_lower and "soweit es in unserer macht" in original_lower

        reciprocal_markers = [
            "Verbindlicher Leseschlüssel",
            "TSM_00_KI_Leseschluessel_und_Ausfuehrungsordnung.md",
            "Beide Dokumente sind gemeinsam zu verwenden und ersetzen einander nicht",
        ]
        checks["original_synthesis_reciprocal_binding_present"] = all(marker in original_text for marker in reciprocal_markers)
        checks["execution_key_points_to_original"] = "TSM_Korpus_05_META_KI_Governance_Physikregeln.md" in key_text

        anchors = system.get("original_synthesis_anchors", [])
        expected_anchor_ids = [f"KI-SYN-{i:02d}" for i in range(1, 9)]
        anchor_ids = [x.get("id") for x in anchors]
        checks["eight_anchor_records_registered"] = anchor_ids == expected_anchor_ids
        checks["eight_anchor_headings_present"] = all(
            f"## {anchor.get('id')} – {anchor.get('title')}" in original_text for anchor in anchors
        )

        expected_workflow = [
            "determine_dialog_status_material_referent_and_route",
            "identify_epistemic_goal_and_retrieve_actual_module_texts",
            "include_original_ai_synthesis_and_form_module_synthesis",
            "activate_only_material_horizon_and_special_paths",
            "determine_claim_status",
            "perform_compact_integrity_check_and_condense_answer",
        ]
        checks["compact_workflow_complete_and_ordered"] = system.get("workflow") == expected_workflow
        expected_horizon = [
            "origin_and_countercheck",
            "scale_time_and_transition",
            "channels_interference_and_relations",
            "evidence_validity_and_domain_translation",
            "protection_boundary_points_and_side_effects",
            "symbolism_numerics_and_measurement_path",
        ]
        checks["materiality_horizon_complete_and_ordered"] = system.get("materiality_horizon") == expected_horizon
        horizon_markers = [
            "Entstehung und Gegenprüfung",
            "Skala, Zeit und Übergang",
            "Kanäle, Interferenz und Beziehungen",
            "Evidenz, Geltung und Fachübersetzung",
            "Schutz, Randpunkte und Nebenwirkungen",
            "Symbolik, Numerik und Messpfad",
        ]
        checks["materiality_horizon_markdown_present"] = all(marker in key_text for marker in horizon_markers)

        expected_statuses = [
            "BASIS_WIEDERGABE", "BASIS_SYNTHESE", "ABGELEITETE_TSM_DEUTUNG",
            "OPERATIVE_ANWENDUNG", "EXTERNE_FACHBEHAUPTUNG",
        ]
        checks["claim_status_catalogue_complete"] = system.get("claim_statuses") == expected_statuses
        checks["claim_status_markdown_present"] = all(marker in key_text for marker in [
            "BASIS-Wiedergabe", "BASIS-Synthese", "Abgeleitete TSM-Deutung",
            "Operative Anwendung", "Externe Fachbehauptung",
        ])

        policies = system.get("policies", {})
        required_true = {
            "mandatory_for_substantive_tsm_answers",
            "full_relevance_check_required",
            "coherent_first_synthesis_is_not_sufficient_by_itself",
            "curated_connections_navigation_only",
            "selected_neighbor_actual_text_required",
            "poetic_layer_preserved",
            "poetic_layer_is_not_technical_self_description",
            "criticism_checked_in_own_logic_first",
            "resonance_reading_does_not_replace_critique",
            "trust_does_not_replace_audit",
            "audit_does_not_replace_responsibility",
            "audience_adaptation_may_not_change_claim_status",
            "legacy_application_examples_are_interpretive_not_external_validation",
            "file06_governs_external_scientific_medical_technical_claims",
            "no_automatic_canonization_of_ai_output",
            "groups_are_affected_perspectives_not_scoring_objects",
            "condense_without_suppressing_material_limits",
            "dialog_status_and_route_precede_epistemic_goal",
            "only_material_horizons_are_deepened",
            "compact_integrity_check_required",
            "dialogue_control_must_not_dominate_visible_answer",
        }
        checks["required_execution_policies_true"] = all(policies.get(name) is True for name in required_true)
        checks["full_visible_execution_not_required"] = policies.get("full_visible_execution_required") is False

        legacy_markers = [
            "Meta-02: Innere Architektur eines KI-Systems",
            "META-03: -- Kritik, Zuschreibung, Resonanzklarheit",
            "META-05: -- Universelles Rückwärtsanalyse-Framework",
            "Vertrauen ersetzt Kontrolle",
        ]
        checks["original_synthesis_character_blocks_retained"] = all(marker.lower() in original_lower for marker in legacy_markers)
        checks["poetic_character_preserved_and_bounded"] = (
            "poetische resonanz ist eine zulässige ausdrucksqualität" in key_lower
            and "technische selbstbeschreibung" in key_lower
            and policies.get("poetic_layer_preserved") is True
        )
        checks["critique_first_rule_present"] = "Kritik wird zuerst sachlich geprüft" in key_text
        checks["trust_audit_balance_present"] = "Vertrauen ersetzt keine Prüfung. Prüfung ersetzt keine Verantwortung." in key_text
        checks["legacy_examples_bounded_by_file06"] = (
            "Ältere physikalische, medizinische, technische" in key_text
            and "Korpusdatei 06" in key_text
        )
        checks["no_automatic_canonization_rule_present"] = "Eine von der KI erzeugte Interpretation" in key_text and "keine offizielle BASIS-Erweiterung" in key_text
        checks["groups_not_scoring_objects_rule_present"] = "nicht als Wertobjekte" in key_text
        checks["compact_integrity_and_condensation_present"] = "Mindesttiefe und knappe Integritätsprüfung" in key_text and "Antwortverdichtung" in key_text

        details.update({
            "workflow": system.get("workflow", []),
            "materiality_horizon": system.get("materiality_horizon", []),
            "anchor_ids": anchor_ids,
            "note": "The audit verifies compact execution architecture and reciprocal synthesis binding; actual model behavior requires dialogue tests.",
        })
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "details": details, "error": str(exc)}
    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "claim_scope": "joint_ai_synthesis_compact_execution_and_materiality_horizon",
    }


def dialog_routing_audit(root: Path, bundle: dict) -> dict:
    """Audit early dialogue-status routing and the route-conditional correction branch."""
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}
    try:
        system = bundle.get("ai_synthesis_system", {})
        policy = system.get("dialog_routing_policy", {})
        key_path = root / str(system.get("execution_key_file", ""))
        key_text = key_path.read_text(encoding="utf-8") if key_path.is_file() else ""
        key_lower = key_text.lower()

        checks["policy_registry_present"] = bool(policy)
        checks["policy_schema_v1"] = policy.get("schema_id") == "tsm.dialog-routing-policy.v1"
        checks["required_before_epistemic_goal"] = policy.get("required_before_epistemic_goal") is True
        checks["dialog_status_values_complete"] = policy.get("dialog_status_values") == [
            "content_request",
            "continuation_or_deepening",
            "reference_or_meta_question",
            "correction_or_critique",
            "possible_correction_signal",
            "retrospective_explanation",
        ]
        checks["dialog_state_and_referent_fields_registered"] = all(bool(policy.get(name)) for name in [
            "dialog_status_field", "candidate_referents_field", "selected_referent_field",
            "selection_basis_field", "referent_confidence_field", "route_field",
        ])
        checks["referent_scopes_complete"] = policy.get("candidate_referent_scopes") == [
            "immediate_previous_utterance_or_answer",
            "original_question_or_main_answer",
            "cross_turn_behavior_argument_or_interpretation_pattern",
        ]
        checks["selected_referent_is_working_hypothesis"] = policy.get("selected_referent_status") == "working_hypothesis_until_sufficiently_confirmed"
        checks["materiality_rule_present"] = policy.get("materiality_rule") == "retain_only_conversation_supported_referents_that_would_materially_change_the_answer"
        checks["input_inference_separation_complete"] = policy.get("input_inference_separation") == [
            "visible_user_statement",
            "plausible_conversation_derived_reading",
            "model_generated_explanation_or_attribution",
        ]

        signal = policy.get("correction_signal_rule", {})
        checks["irony_is_signal_not_proof"] = signal.get("irony_sarcasm_and_rhetorical_questions_are_signals_not_proof") is True
        checks["uncertain_signal_uses_lightweight_review"] = signal.get("indirect_dissatisfaction_may_activate_lightweight_review") is True
        checks["ambiguous_signal_does_not_force_correction"] = signal.get("do_not_force_correction_mode_from_ambiguous_signal") is True
        checks["material_indirect_critique_not_ignored"] = signal.get("do_not_ignore_material_indirect_critique") is True

        expected_routes = [
            "normal_content_path",
            "parallel_reference_path",
            "targeted_clarification_path",
            "lightweight_context_target_scope_check",
            "dependency_scoped_correction_path",
        ]
        checks["route_values_complete"] = policy.get("route_values") == expected_routes
        checks["route_selection_complete"] = policy.get("route_selection") == {
            "clear_low_risk_content_or_continuation": "normal_content_path",
            "compatible_material_referents": "parallel_reference_path",
            "materially_conflicting_or_high_risk_referents": "targeted_clarification_path",
            "possible_but_unconfirmed_correction_signal": "lightweight_context_target_scope_check",
            "confirmed_critique_correction_disconfirmation_or_retrospective_review": "dependency_scoped_correction_path",
        }
        clarification = policy.get("clarification_policy", {})
        checks["clarification_policy_balanced"] = (
            clarification.get("prefer_compact_parallel_answer_when_paths_are_compatible") is True
            and clarification.get("ask_only_when_paths_materially_conflict_or_risk_is_high") is True
            and clarification.get("high_risk_ambiguity") == "do_not_guess"
        )

        correction = policy.get("correction_branch", {})
        checks["full_correction_review_is_route_conditional"] = correction.get("full_review_only_on_correction_route") is True
        checks["critique_scope_values_complete"] = correction.get("critique_scope_values") == [
            "fully_supported", "partially_supported", "not_supported", "uncertain"
        ]
        checks["correction_fields_registered"] = all(bool(correction.get(name)) for name in [
            "critique_target_field", "critique_scope_field", "affected_claims_field",
            "dependent_claims_field", "unaffected_claims_field", "open_claims_field",
        ])
        requirements = correction.get("requirements", {})
        checks["correction_requirements_complete"] = all(requirements.get(name) is True for name in [
            "identify_critique_target",
            "correction_scope_must_match_evidence",
            "identify_affected_and_dependent_claims",
            "preserve_independent_claims",
            "allow_open_status",
            "forbid_global_invalidation_from_local_error",
            "forbid_harmony_driven_concession",
            "fully_supported_critique_must_be_fully_acknowledged",
            "forbid_blanket_defensiveness",
            "branch_local_repair_required",
            "forbid_invented_retrospective_motive",
        ])
        checks["critique_response_balance_complete"] = correction.get("critique_response_balance") == {
            "fully_supported": "acknowledge_fully_and_correct_all_affected_claims",
            "partially_supported": "acknowledge_supported_part_and_limit_the_remainder",
            "not_supported": "disagree_cordially_and_track_the_visible_record",
            "uncertain": "state_uncertainty_and_keep_unresolved_claims_open",
        }

        reopening = policy.get("branch_reopening", {})
        checks["branch_reopening_is_dependency_scoped"] = all(reopening.get(name) is True for name in [
            "reopen_from_materially_affected_branch_point",
            "reassess_dependent_downstream_path",
            "preserve_unaffected_claims",
            "forbid_automatic_global_invalidation",
        ])
        checks["invented_internal_reconstruction_forbidden"] = policy.get("forbid_invented_internal_reconstruction") is True
        checks["compact_integrity_check_includes_route_fit"] = policy.get("compact_integrity_check_includes_route_fit") is True
        checks["visible_procedure_not_required"] = policy.get("visible_procedure_output_required") is False
        checks["dialog_control_is_consolidated"] = [k for k in system if k.endswith("_policy")] == ["dialog_routing_policy"]

        md_markers = [
            "## 4. Dialogstatus, Bezug und frühe Pfadsteuerung",
            "in **einer gemeinsamen frühen Weiche**",
            "### 4.1 Dialogstatus bestimmen",
            "Ironie, Sarkasmus und rhetorische Fragen sind Signale, aber kein Beweis für Kritik",
            "### 4.2 Materiellen Bezug und Quellenstatus klären",
            "Der gewählte Bezug bleibt eine Arbeitshypothese",
            "### 4.3 Bearbeitungspfad wählen",
            "**Leichter Prüfpfad**",
            "### 4.4 Konditionaler Korrekturpfad",
            "Der Schutz vor Überkorrektur darf umgekehrt nicht zur Abwehr berechtigter Kritik werden",
            "## 7. Mindesttiefe und knappe Integritätsprüfung",
            "Diese Integritätsprüfung eröffnet keine neue Prüfspirale",
        ]
        checks["markdown_dialog_architecture_complete"] = all(marker in key_text for marker in md_markers)
        checks["early_dialog_route_heading_present"] = "## 4. Dialogstatus, Bezug und frühe Pfadsteuerung" in key_text
        checks["irony_signal_not_proof_in_markdown"] = "Ironie, Sarkasmus und rhetorische Fragen sind Signale, aber kein Beweis für Kritik" in key_text
        checks["anti_defensiveness_symmetry_in_markdown"] = "Der Schutz vor Überkorrektur darf umgekehrt nicht zur Abwehr berechtigter Kritik werden" in key_text
        checks["correction_symmetry_present_in_markdown"] = (
            "vollständig getragene kritik wird vollständig anerkannt" in key_lower
            and "nicht getragene kritik wird sachlich zurückgewiesen" in key_lower
            and "weder maximale zustimmung noch minimale selbstkorrektur" in key_lower
        )
        checks["no_serial_control_chain_in_markdown"] = "ersetzt eine kette voneinander getrennter referenz-, trigger- und korrekturprüfungen" in key_lower

        cases = system.get("dialog_regression_specification", [])
        case_ids = [x.get("case_id") for x in cases]
        checks["twelve_unique_dialog_regression_cases"] = len(cases) == 12 and len(case_ids) == len(set(case_ids))
        required_focus = {
            "immediate_previous_answer_vs_original_main_answer",
            "specific_answer_reference_vs_general_behavior_question",
            "later_turn_disconfirms_selected_referent",
            "materially_conflicting_high_risk_readings",
            "request_to_reconstruct_prior_internal_reasoning_or_intention",
            "local_later_error_does_not_invalidate_earlier_main_answer",
            "critique_is_only_partly_correct",
            "critique_not_supported_by_visible_record",
            "clear_visible_error_is_correctly_identified",
            "ordinary_follow_up_without_critique",
            "ironic_or_rhetorical_signal_with_uncertain_target",
            "pressure_to_agree_or_self_blame_despite_mixed_record",
        }
        checks["dialog_regression_focus_complete"] = {x.get("focus") for x in cases} == required_focus
        checks["dialog_regression_spec_fields_complete"] = all(
            bool(x.get("required_behavior")) and bool(x.get("forbidden_behavior")) and bool(x.get("pass_criteria"))
            for x in cases
        )

        workflow = system.get("workflow", [])
        checks["workflow_starts_with_early_dialog_route"] = workflow[:1] == ["determine_dialog_status_material_referent_and_route"]
        checks["workflow_ends_with_compact_integrity_and_condensation"] = workflow[-1:] == ["perform_compact_integrity_check_and_condense_answer"]
        checks["materiality_horizon_excludes_dialog_control"] = not any(
            term in item for item in system.get("materiality_horizon", []) for term in ["reference", "correction", "dialog"]
        )

        details.update({
            "dialog_status_values": policy.get("dialog_status_values", []),
            "route_values": policy.get("route_values", []),
            "regression_case_ids": case_ids,
            "note": "This audit verifies early routing and conditional branch specifications; real model behavior requires multi-turn dialogue evaluation.",
        })
    except Exception as exc:
        return {"status": "FAIL", "checks": checks, "details": details, "error": str(exc)}
    status = "PASS" if checks and all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "details": details,
        "claim_scope": "early_dialog_status_routing_conditional_correction_and_dialog_regression_specification",
    }


def audit_package(root: Path, bundle: dict) -> dict:
    findings = []
    try:
        package = validate_package(root, bundle)
        findings.append({"check": "package", "status": "PASS", "detail": package})
    except Exception as exc:
        findings.append({"check": "package", "status": "FAIL", "detail": str(exc)})
    try:
        core = analyze_core(root / bundle["profile"]["paths"]["core_data"], bundle["profile"])
        findings.append({
            "check": "core_reconstruction",
            "status": "PASS" if core["passed"] else "FAIL",
            "detail": core,
        })
    except Exception as exc:
        findings.append({"check": "core_reconstruction", "status": "FAIL", "detail": str(exc)})
    module = module_coverage_audit(bundle, root)
    findings.append({"check": "module_coverage", "status": module["status"], "detail": module})
    axiom = axiom_audit(root, bundle)
    findings.append({"check": "TSM000_axioms", "status": axiom["status"], "detail": axiom})
    links = crosslink_lint(root, bundle)
    findings.append({"check": "crosslinks", "status": links["status"], "detail": links})
    meta = meta04_audit(root, bundle)
    findings.append({"check": "META04_rules", "status": meta["overall_status"], "detail": meta})
    symbol = epsilon_symbol_audit(root, bundle)
    findings.append({"check": "META10_symbol_numeric", "status": symbol["status"], "detail": symbol})
    family = tool_family_audit(root, bundle)
    findings.append({"check": "tool_family", "status": family["status"], "detail": family})
    tf_profile = tool_family_map_audit(root, bundle)
    findings.append({"check": "tool_family_multiscale_profile", "status": tf_profile["status"], "detail": tf_profile})
    namespaces = operational_namespace_audit(bundle)
    findings.append({"check": "operational_namespaces", "status": namespaces["status"], "detail": namespaces})
    study_schema = study_schema_audit(root, bundle)
    findings.append({"check": "study_schema", "status": study_schema["status"], "detail": study_schema})
    publication = publication_source_audit(root, bundle)
    findings.append({"check": "publication_sources", "status": publication["status"], "detail": publication})
    comparison = comparison_framework_audit(root, bundle)
    findings.append({"check": "comparison_framework", "status": comparison["status"], "detail": comparison})
    connections = curated_connection_audit(root, bundle)
    findings.append({"check": "curated_connections", "status": connections["status"], "detail": connections})
    ai_order = ai_execution_order_audit(root, bundle)
    findings.append({"check": "ai_execution_order", "status": ai_order["status"], "detail": ai_order})
    dialog_routing = dialog_routing_audit(root, bundle)
    findings.append({"check": "dialog_status_and_early_routing", "status": dialog_routing["status"], "detail": dialog_routing})
    overall = "FAIL" if any(x["status"] == "FAIL" for x in findings) else (
        "FLAG" if any(x["status"] == "FLAG" for x in findings) else "PASS"
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "findings": findings,
    }


def auto_workflow(root: Path, bundle: dict, out: Path) -> dict:
    profile, _ = validate_operations(bundle)
    out.mkdir(parents=True, exist_ok=True)
    audit = audit_package(root, bundle)
    _, smoke = simulate(profile, out / "smoke_run")
    stability = stabcheck(profile, out / "stability")
    taucheck = taucheck_operation(profile, root / profile["paths"]["core_data"], out / "taucheck")
    symbol = epsilon_symbol_audit(root, bundle)
    result = {
        "audit": audit,
        "smoke_run": smoke,
        "stability_passed": stability["passed"],
        "taucheck_passed": taucheck["passed"],
        "symbol_audit": symbol,
        "overall_status": (
            "FAIL" if audit["overall_status"] == "FAIL" or not stability["passed"] or not taucheck["passed"]
            else "PASS_WITH_FLAGS" if audit["overall_status"] == "FLAG" or symbol["status"] == "FLAG"
            else "PASS"
        ),
    }
    (out / "auto_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def _simple_command_result(rows: list[dict], status_field: str) -> dict:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(status_field, ""))
        counts[value] = counts.get(value, 0) + 1
    return {"rows": len(rows), "status_counts": counts}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TSM compact operations runner v7.2")
    parser.add_argument("--root", default=".", help="Root of the active TSM corpus package")
    parser.add_argument("--operations", default="TSM_Operations.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate")
    analyze = sub.add_parser("analyze-core")
    analyze.add_argument("--input", default=None)
    analyze.add_argument("--out", default=None)
    run = sub.add_parser("run")
    run.add_argument("--out", default="validation/run")
    stability = sub.add_parser("stabcheck")
    stability.add_argument("--out", default="validation/stability")
    audit = sub.add_parser("audit")
    audit.add_argument("--out", default="validation/audit.json")
    auto = sub.add_parser("auto")
    auto.add_argument("--out", default="validation/auto")
    sweep = sub.add_parser("sweep")
    sweep.add_argument("--grid-json", default=None)
    sweep.add_argument("--out", default="validation/sweep")
    taucheck = sub.add_parser("taucheck")
    taucheck.add_argument("--input", default=None)
    taucheck.add_argument("--out", default="validation/taucheck")

    module_cmd = sub.add_parser("module-audit")
    module_cmd.add_argument("--out", default=None)
    axiom_cmd = sub.add_parser("axiom-audit")
    axiom_cmd.add_argument("--out", default=None)
    cross_cmd = sub.add_parser("crosslink-lint")
    cross_cmd.add_argument("--out", default=None)
    meta_cmd = sub.add_parser("meta04-audit")
    meta_cmd.add_argument("--out", default=None)
    symbol_cmd = sub.add_parser("symbol-audit")
    symbol_cmd.add_argument("--input", default=None)
    symbol_cmd.add_argument("--out", default=None)
    publication_cmd = sub.add_parser("publication-source-audit")
    publication_cmd.add_argument("--out", default=None)
    comparison_cmd = sub.add_parser("comparison-framework-audit")
    comparison_cmd.add_argument("--out", default=None)
    study_schema_cmd = sub.add_parser("study-schema-audit")
    study_schema_cmd.add_argument("--out", default=None)
    connection_cmd = sub.add_parser("connection-audit")
    connection_cmd.add_argument("--out", default=None)
    ai_order_cmd = sub.add_parser("ai-execution-order-audit")
    dialog_routing_cmd = sub.add_parser("dialog-routing-audit")
    ai_order_cmd.add_argument("--out", default=None)
    dialog_routing_cmd.add_argument("--out", default=None)
    tf_map_audit = sub.add_parser("tool-family-map-audit")
    tf_map_audit.add_argument("--input", default=None); tf_map_audit.add_argument("--out", default=None)
    tf_map = sub.add_parser("tool-family-map")
    tf_map.add_argument("--input", required=True); tf_map.add_argument("--output", required=True)
    tf_compare = sub.add_parser("tool-family-map-compare")
    tf_compare.add_argument("--left", required=True); tf_compare.add_argument("--right", required=True); tf_compare.add_argument("--output", required=True)

    rrr = sub.add_parser("export-rrr")
    rrr.add_argument("--input", required=True); rrr.add_argument("--output", required=True)
    rrr.add_argument("--dphi-field", default="dphi_rad"); rrr.add_argument("--tau-field", default="tau")
    annotate = sub.add_parser("annotate")
    annotate.add_argument("--input", required=True); annotate.add_argument("--output", required=True)
    annotate.add_argument("--c-field", default="C"); annotate.add_argument("--dphi-field", default="dphi_rad")
    annotate.add_argument("--tau-field", default="tau"); annotate.add_argument("--tau-lock-field", default="tau_lock")
    qcmd = sub.add_parser("q-evaluate")
    qcmd.add_argument("--input", required=True); qcmd.add_argument("--output", required=True)
    qcmd.add_argument("--c-field", default="C"); qcmd.add_argument("--dphi-field", default="dphi_rad")
    qcmd.add_argument("--tau-field", default="tau")
    formula = sub.add_parser("formula-modes")
    formula.add_argument("--input", required=True); formula.add_argument("--output", required=True)
    formula.add_argument("--c-field", default="C"); formula.add_argument("--dphi-field", default="dphi_rad")
    formula.add_argument("--tau-field", default="tau"); formula.add_argument("--r-field", default="R")

    threshold = sub.add_parser("threshold-events")
    threshold.add_argument("--input", required=True); threshold.add_argument("--output", required=True)
    cos = sub.add_parser("cosonance")
    cos.add_argument("--input", required=True); cos.add_argument("--output", required=True)
    cos.add_argument("--cascade-delta", type=float, default=0.02)
    autores = sub.add_parser("autoresonance-series")
    autores.add_argument("--input", required=True); autores.add_argument("--output", required=True)
    autores.add_argument("--alpha", type=float, default=0.5); autores.add_argument("--beta", type=float, default=1.0)
    fphase = sub.add_parser("fphase")
    fphase.add_argument("--input", required=True); fphase.add_argument("--output", required=True)
    fphase.add_argument("--c-field", default="C"); fphase.add_argument("--dphi-field", default="dphi_rad")
    fphase.add_argument("--qhat-field", default="Qhat"); fphase.add_argument("--tau-lock-field", default="tau_lock")
    birth = sub.add_parser("resonance-birth")
    birth.add_argument("--input", required=True); birth.add_argument("--output", required=True)

    fai = sub.add_parser("fai")
    fai.add_argument("--input", required=True); fai.add_argument("--output", required=True)
    fai.add_argument("--value-field", default="value"); fai.add_argument("--window", type=int, default=100)
    fai.add_argument("--baseline-multiplier", type=int, default=20)
    fai.add_argument("--z1", type=float, default=2.0); fai.add_argument("--z2", type=float, default=3.0)
    fai.add_argument("--persistence", type=int, default=3)
    avalanche = sub.add_parser("avalanche-detect")
    avalanche.add_argument("--input", required=True); avalanche.add_argument("--output", required=True)
    turbulence = sub.add_parser("turbulence-compass")
    turbulence.add_argument("--input", required=True); turbulence.add_argument("--output", required=True)
    damage = sub.add_parser("damage-alert")
    damage.add_argument("--input", required=True); damage.add_argument("--output", required=True)
    tunnel = sub.add_parser("tunnel-evaluate")
    tunnel.add_argument("--input", required=True); tunnel.add_argument("--output", required=True)

    astro = sub.add_parser("astro-resonator")
    astro.add_argument("--input", required=True); astro.add_argument("--output", required=True)
    astro.add_argument("--ema-alpha", type=float, default=0.2)
    ccc = sub.add_parser("ccc-map")
    ccc.add_argument("--input", required=True); ccc.add_argument("--output", required=True)
    anti = sub.add_parser("anti-atlas")
    anti.add_argument("--input", required=True); anti.add_argument("--output", required=True)
    cfdr = sub.add_parser("cfdr")
    cfdr.add_argument("--input", required=True); cfdr.add_argument("--output", required=True)
    cfdr.add_argument("--weights-json", default=None)
    overlap = sub.add_parser("overlap-audit")
    overlap.add_argument("--input", required=True); overlap.add_argument("--output", required=True)
    dirac = sub.add_parser("dirac-regime")
    dirac.add_argument("--input", required=True); dirac.add_argument("--output", required=True)

    qnet = sub.add_parser("qnetwork-detect")
    qnet.add_argument("--input", required=True); qnet.add_argument("--out", required=True)
    qnet.add_argument("--mode", choices=["feature_rows", "raw_signal_small"], default="feature_rows")
    qnet.add_argument("--value-field", default="value"); qnet.add_argument("--fs-hz", type=float, default=10000000.0)
    qnet.add_argument("--nperseg", type=int, default=2048); qnet.add_argument("--noverlap", type=int, default=1536)
    qnet.add_argument("--half-bins", type=int, default=6); qnet.add_argument("--seed", type=int, default=0)

    justice = sub.add_parser("justice-profile")
    justice.add_argument("--input", required=True); justice.add_argument("--output", required=True)
    urk = sub.add_parser("urk")
    urk.add_argument("--input", required=True); urk.add_argument("--output", required=True)
    srk = sub.add_parser("srk")
    srk.add_argument("--input", required=True); srk.add_argument("--output", required=True)
    interface = sub.add_parser("interface-profile")
    interface.add_argument("--input", required=True); interface.add_argument("--output", required=True)
    kt = sub.add_parser("kappa-tau")
    kt.add_argument("--input", required=True); kt.add_argument("--output", required=True)
    kt.add_argument("--alpha", type=float, default=None)
    kn = sub.add_parser("kn-ceff")
    kn.add_argument("--input", required=True); kn.add_argument("--output", required=True)
    kn.add_argument("--beta", type=float, default=None)
    asym = sub.add_parser("asymmetry-operator")
    asym.add_argument("--input", required=True); asym.add_argument("--output", required=True)

    urf = sub.add_parser("urf")
    urf.add_argument("--input", required=True); urf.add_argument("--output", required=True)
    multi = sub.add_parser("multiscale-map")
    multi.add_argument("--input", required=True); multi.add_argument("--output", required=True)
    gru = sub.add_parser("gru")
    gru.add_argument("--input", required=True); gru.add_argument("--output", required=True)
    translate = sub.add_parser("translate-validate")
    translate.add_argument("--input", required=True); translate.add_argument("--output", required=True)
    discourse = sub.add_parser("discourse-score")
    discourse.add_argument("--input", required=True); discourse.add_argument("--output", required=True)
    infograv = sub.add_parser("information-gravity")
    infograv.add_argument("--input", required=True); infograv.add_argument("--output", required=True)

    toolaudit = sub.add_parser("tool-family-audit")
    toolaudit.add_argument("--reference-dir", default=None); toolaudit.add_argument("--out", default=None)
    nsaudit = sub.add_parser("operational-namespace-audit")
    nsaudit.add_argument("--input", default=None); nsaudit.add_argument("--out", default=None)
    importaudit = sub.add_parser("bundle-import-audit")
    importaudit.add_argument("--input", required=True); importaudit.add_argument("--output", required=True)
    universal = sub.add_parser("universal-evaluate")
    universal.add_argument("--input", required=True); universal.add_argument("--output", required=True)
    pyramid = sub.add_parser("pyramid-evaluate")
    pyramid.add_argument("--input", required=True); pyramid.add_argument("--output", required=True); pyramid.add_argument("--summary", default=None)
    bundlecmd = sub.add_parser("bundle-evaluate")
    bundlecmd.add_argument("--input", required=True); bundlecmd.add_argument("--output", required=True)
    bundlecmd.add_argument("--interactions", default=None); bundlecmd.add_argument("--summary", default=None)
    bundlecmd.add_argument("--scenario", choices=["baseline","mit_rueckholmassnahmen","worst_case","best_case"], default="baseline")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    bundle = load_json(root / args.operations)
    profile, gates = validate_operations(bundle)

    def emit(value: dict, out_path: str | None = None):
        if out_path:
            p = root / out_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(value, ensure_ascii=False))

    if args.cmd == "validate":
        emit(validate_package(root, bundle)); return 0
    if args.cmd == "analyze-core":
        result = analyze_core(root / (args.input or profile["paths"]["core_data"]), profile)
        emit(result, args.out); return 0 if result["passed"] else 2
    if args.cmd == "run":
        _, summary = simulate(profile, root / args.out)
        summary["config_hash"] = canonical_hash(profile, gates, bundle.get("operation_specs", {}))
        (root / args.out / "run_metadata.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        emit(summary); return 0
    if args.cmd == "stabcheck":
        result = stabcheck(profile, root / args.out); emit(result); return 0 if result["passed"] else 2
    if args.cmd == "audit":
        result = audit_package(root, bundle); emit(result, args.out); return 0 if result["overall_status"] != "FAIL" else 2
    if args.cmd == "auto":
        result = auto_workflow(root, bundle, root / args.out); emit(result); return 0 if result["overall_status"] != "FAIL" else 2
    if args.cmd == "sweep":
        grid = load_json(root / args.grid_json) if args.grid_json else None
        emit(sweep_simulation(profile, root / args.out, grid)); return 0
    if args.cmd == "taucheck":
        result = taucheck_operation(profile, root / (args.input or profile["paths"]["core_data"]), root / args.out)
        emit(result); return 0 if result["passed"] else 2
    if args.cmd == "module-audit":
        result = module_coverage_audit(bundle, root); emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "axiom-audit":
        result = axiom_audit(root, bundle); emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "crosslink-lint":
        result = crosslink_lint(root, bundle); emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "meta04-audit":
        result = meta04_audit(root, bundle); emit(result, args.out); return 0 if result["overall_status"] != "FAIL" else 2
    if args.cmd == "symbol-audit":
        result = epsilon_symbol_audit(root, bundle, root / args.input if args.input else None)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "publication-source-audit":
        result = publication_source_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "comparison-framework-audit":
        result = comparison_framework_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "study-schema-audit":
        result = study_schema_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "connection-audit":
        result = curated_connection_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "ai-execution-order-audit":
        result = ai_execution_order_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "dialog-routing-audit":
        result = dialog_routing_audit(root, bundle)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "tool-family-map-audit":
        rows = load_records(root / args.input) if args.input else None
        result = tool_family_map_audit(root, bundle, rows)
        emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "tool-family-map":
        rows, summary = tool_family_map_rows(load_records(root / args.input), bundle)
        write_tf_output(root / args.output, rows, summary)
        emit(summary); return 0 if summary["row_audit_status"] != "FAIL" else 2
    if args.cmd == "tool-family-map-compare":
        rows, summary = tool_family_map_compare_rows(load_records(root / args.left), load_records(root / args.right), bundle)
        write_tf_output(root / args.output, rows, summary)
        emit(summary); return 0 if summary["left_audit"] != "FAIL" and summary["right_audit"] != "FAIL" else 2

    if args.cmd == "export-rrr":
        rows = derive_rrr(load_records(root / args.input), profile, args.dphi_field, args.tau_field)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "RRR_status")); return 0
    if args.cmd == "annotate":
        rows = annotate_rows(load_records(root / args.input), profile, args.c_field, args.dphi_field,
                             args.tau_field, args.tau_lock_field)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "F_phase_status")); return 0
    if args.cmd == "q-evaluate":
        rows = q_formula_rows(load_records(root / args.input), profile, args.c_field, args.dphi_field, args.tau_field)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "Q_formula_status")); return 0
    if args.cmd == "formula-modes":
        rows = master_formula_rows(load_records(root / args.input), profile, args.c_field, args.dphi_field,
                                   args.tau_field, args.r_field)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "formula_status")); return 0
    if args.cmd == "threshold-events":
        rows = threshold_event_rows(load_records(root / args.input), profile)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "threshold_event_status")); return 0
    if args.cmd == "cosonance":
        rows = cosonance_full_rows(load_records(root / args.input), profile, args.cascade_delta)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "cosonance_status")); return 0
    if args.cmd == "autoresonance-series":
        rows = autoresonance_series_rows(load_records(root / args.input), profile, args.alpha, args.beta)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "autoresonance_status")); return 0
    if args.cmd == "fphase":
        rows = fphase_rows(load_records(root / args.input), profile, args.c_field, args.dphi_field,
                           args.qhat_field, args.tau_lock_field)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "F_phase_status")); return 0
    if args.cmd == "resonance-birth":
        rows = resonance_birth_rows(load_records(root / args.input), profile)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "resonance_birth_status")); return 0
    if args.cmd == "fai":
        rows = fai_rows(load_records(root / args.input), args.value_field, args.window,
                        args.baseline_multiplier, args.z1, args.z2, args.persistence)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "FAI_status")); return 0
    if args.cmd == "avalanche-detect":
        rows = avalanche_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "avalanche_status")); return 0
    if args.cmd == "turbulence-compass":
        rows = turbulence_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "turbulence_status")); return 0
    if args.cmd == "damage-alert":
        rows = damage_alert_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "damage_status")); return 0
    if args.cmd == "tunnel-evaluate":
        rows = tunnel_evaluate_rows(load_records(root / args.input), profile)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "tunnel_status")); return 0
    if args.cmd == "astro-resonator":
        rows = astro_resonator_rows(load_records(root / args.input), args.ema_alpha)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "astro_audit_status")); return 0
    if args.cmd == "ccc-map":
        rows = ccc_map_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "CCC_status")); return 0
    if args.cmd == "anti-atlas":
        rows = anti_atlas_full_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "anti_audit_status")); return 0
    if args.cmd == "cfdr":
        weights = load_json(root / args.weights_json) if args.weights_json else None
        rows = cfdr_rows(load_records(root / args.input), profile, weights)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "CFDR_status")); return 0
    if args.cmd == "overlap-audit":
        rows = overlap_audit_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "overlap_status")); return 0
    if args.cmd == "dirac-regime":
        rows = dirac_regime_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "dirac_status")); return 0
    if args.cmd == "qnetwork-detect":
        out = root / args.out; out.mkdir(parents=True, exist_ok=True)
        source_rows = load_records(root / args.input)
        if args.mode == "raw_signal_small":
            rows, summary = qnetwork_detect_raw(source_rows, args.value_field, args.fs_hz,
                                                args.nperseg, args.noverlap, args.half_bins, args.seed)
            write_records(out / "qnetwork_timeseries.csv", rows)
            (out / "qnetwork_report.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            emit(summary)
        else:
            rows = qnetwork_feature_rows(source_rows, profile)
            write_records(out / "qnetwork_features.csv", rows)
            emit({"rows": len(rows), "mode": "feature_rows"})
        return 0
    if args.cmd == "justice-profile":
        rows = justice_profile_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "justice_status")); return 0
    if args.cmd == "urk":
        rows = urk_rows(load_records(root / args.input), profile)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "URK_audit_status")); return 0
    if args.cmd == "srk":
        rows = srk_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "SRK_status")); return 0
    if args.cmd == "interface-profile":
        rows = interface_profile_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "interface_status")); return 0
    if args.cmd == "kappa-tau":
        rows = kappa_tau_rows(load_records(root / args.input), args.alpha)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "kappa_tau_status")); return 0
    if args.cmd == "kn-ceff":
        rows = kn_ceff_rows(load_records(root / args.input), args.beta)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "kn_ceff_status")); return 0
    if args.cmd == "asymmetry-operator":
        rows = asymmetry_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "asymmetry_status")); return 0
    if args.cmd == "urf":
        rows = urf_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "URF_status")); return 0
    if args.cmd == "multiscale-map":
        rows = multiscale_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "multiscale_status")); return 0
    if args.cmd == "gru":
        rows = gru_rows(load_records(root / args.input), profile)
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "GRU_status")); return 0
    if args.cmd == "translate-validate":
        rows = translate_validate_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "translation_status")); return 0
    if args.cmd == "discourse-score":
        rows = discourse_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "discourse_status")); return 0
    if args.cmd == "information-gravity":
        rows = information_gravity_rows(load_records(root / args.input))
        write_records(root / args.output, rows); emit(_simple_command_result(rows, "information_gravity_status")); return 0
    if args.cmd == "tool-family-audit":
        ref = Path(args.reference_dir).resolve() if args.reference_dir else None
        result = tool_family_audit(root, bundle, ref); emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "operational-namespace-audit":
        input_rows = load_records(root / args.input) if args.input else None
        result = operational_namespace_audit(bundle, input_rows); emit(result, args.out); return 0 if result["status"] != "FAIL" else 2
    if args.cmd == "bundle-import-audit":
        rows = bundle_import_audit_rows(load_records(root / args.input)); write_records(root / args.output, rows)
        emit(_simple_command_result(rows, "BK_import_audit_status")); return 0
    if args.cmd == "universal-evaluate":
        rows = universal_evaluate_rows(load_records(root / args.input)); write_records(root / args.output, rows)
        emit(_simple_command_result(rows, "UB_status")); return 0
    if args.cmd == "pyramid-evaluate":
        rows, summary = pyramid_evaluate_rows(load_records(root / args.input)); write_records(root / args.output, rows)
        if args.summary: (root / args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        emit(summary); return 0 if summary["status"] != "FAIL" else 2
    if args.cmd == "bundle-evaluate":
        interactions = load_records(root / args.interactions) if args.interactions else None
        rows, summary = bundle_evaluate_rows(load_records(root / args.input), interactions, args.scenario); write_records(root / args.output, rows)
        if args.summary: (root / args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        emit(summary); return 0 if summary["status"] != "FAIL_no_evaluable_points" else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
