#!/usr/bin/env python3
"""
TSM–GR Runner v0.2 — Ein‑Datei‑Referenzimplementierung
======================================================
Funktionen (CLI):
  • run        – Einzellauf; schreibt trajectory.csv, zones.csv, run.log.jsonl
  • sweep      – Parameter-Sweeps (eingebautes Grid oder externes grid.json)
  • taucheck   – τ‑Reparametrisations‑Check (vergleicht Invarianten)
  • stabcheck  – Stabilitäts‑Guard (NaN/Inf, Schrittweiten‑Robustheit)
Ziele / Design:
  • Keine externen Abhängigkeiten außer Python ≥ 3.9
  • Parametrisierung via params.json (optional). Alias „lambda“ → „lambda_“ erlaubt.
  • Zonen/Hysterese nach TSM‑GR v0.2: Labels ["F+","F","R↑","R↓","K","K+"]
  • Outputs kompatibel zum Analyzer (tsm_gr_v_0(3).py): trajectory.csv, zones.csv
Hinweis:
  Dies ist eine praktikable Referenz, die die im Korpus beschriebenen Kernelemente
  abbildet (effektive Geodäsie −α∇K, Rückholfluss ε' = −λ K ε, Zonenlogik mit Hysterese
  und Dwell‑Zähler). Es ist kein physikalisches Endmodell, sondern ein reproduzierbarer
  Arbeitsläufer für Demonstration, Sweeps und Berichte.
Dateistruktur bei Läufen (–out DIR):
  DIR/
    trajectory.csv       # Zeitreihe über τ
    zones.csv            # Zonensequenz (Start/Ende/Dwell)
    run.log.jsonl        # JSON‑Log pro Schritt
  (bei sweep zusätzlich)
    sweep_summary.csv    # Kennzahlen je Fall
Autor: TSM‑GR (v0.2)
Lizenz: MIT
"""
from __future__ import annotations
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import argparse, csv, json, random, sys, statistics
# -----------------------------
# Utils
# -----------------------------
def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x
def sigmoid(z: float) -> float:
    # numerisch robuste Sigmoid
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)
def vdot(a: List[float], b: List[float]) -> float:
    return float(sum((ai * bi for ai, bi in zip(a, b))))
def vadd(a: List[float], b: List[float]) -> List[float]:
    return [ai + bi for ai, bi in zip(a, b)]
def vsub(a: List[float], b: List[float]) -> List[float]:
    return [ai - bi for ai, bi in zip(a, b)]
def vscale(a: List[float], s: float) -> List[float]:
    return [ai * s for ai in a]
def vnorm(a: List[float]) -> float:
    return math.sqrt(max(0.0, vdot(a, a)))
def wrap_angle(rad: float) -> float:
    # wrap to [−π, +π)
    twopi = 2.0 * math.pi
    r = (rad + math.pi) % twopi - math.pi
    # im seltenen Grenzfall −π → +π zur Stabilität klammern
    if r == -math.pi:
        r = math.pi
    return r
# -----------------------------
# Parameter
# -----------------------------
@dataclass
class Params:
    version: str = "tsm-gr-v0.2"
    # Dynamik
    alpha: float = 1.0          # Geodäsie‑Kopplung (−α∇K)
    lambda_: float = 1.0        # Rückholrate in ε' = −λ K ε
    delta: float = 0.1          # lineare Dämpfung der Geschwindigkeit
    gamma0: float = 0.0         # Offset für K‑Potential
    gamma1: float = 1.0         # Steilheit für K‑Potential (sigmoid)
    # Zonen/Hysterese
    B_hi: float = 0.8
    S_lo: float = 0.3
    eps_phi: float = 0.0174533   # ~1° (π/180)
    hK: float = 0.02            # Schwell‑Hysterese auf K / Kdot
    N_dwell: int = 3            # Mindestverweildauer pro Zone
    # Integration
    dtau: float = 0.1
    steps: int = 300
    seed: int = 0
    # Phasenlage / Modus
    omega_phi: float = 0.0
    mode: str = "potential"
    # CCC bridge (optional)
    alpha_mode: str = "off"     # {"off","ccc_map"}
    ccc_alpha: float = 0.0      # external α (CCC)
    A: float = 0.0              # ΔK = A * α
    B: float = 0.0              # Δλ = B * α
    C: float = 0.0              # Δφ via ωφ offset = C * α
     # {"potential"|"residual"}
    # Geometrie/Skalierung
    kappa: float = 1.0          # Skala für Richtungs‑Kopplung
    x_star: List[float] = None  # Attraktor der Geodäsie (optional)
    # Anisotrope Adressierung
    xi_center: List[float] = None
    xi_k: List[float] = None
    xi_sigma: float = 1.0
    xi_omega: float = 0.2
    # τ‑Reparametrisation (nur taucheck)
    a_tau: float = 0.0
    def finalize(self):
        if self.x_star is None:
            self.x_star = [0.0, 0.0, 0.0]
        if self.xi_center is None:
            self.xi_center = [0.0, 0.0, 0.0]
        if self.xi_k is None:
            self.xi_k = [0.5, 0.0, 0.0]
        # Klammern
        self.B_hi = clamp(self.B_hi, 0.0, 1.0)
        self.S_lo = clamp(self.S_lo, 0.0, 1.0)
        self.hK   = clamp(self.hK, 0.0, 0.1)
        self.eps_phi = clamp(self.eps_phi, 0.0, 0.523599)
        self.N_dwell = max(1, int(self.N_dwell))
        self.dtau = max(1e-6, float(self.dtau))
        self.steps = max(1, int(self.steps))
        self.lambda_ = max(0.0, float(self.lambda_))
        self.alpha = max(0.0, float(self.alpha))
        self.delta = max(0.0, float(self.delta))
        self.gamma1 = float(self.gamma1)
        self.gamma0 = float(self.gamma0)
        self.kappa = float(self.kappa)
        self.xi_sigma = max(1e-6, float(self.xi_sigma))
        self.omega_phi = float(self.omega_phi)
        self.mode = str(self.mode)
        # CCC mapping (optional)
        try:
            self.alpha_mode = str(self.alpha_mode)
            self.ccc_alpha = float(self.ccc_alpha)
            self.A = float(self.A); self.B = float(self.B); self.C = float(self.C)
        except Exception:
            pass
        if getattr(self, "alpha_mode", "off") == "ccc_map" and (abs(self.ccc_alpha) > 0.0):
            self.gamma0 = float(self.gamma0) + self.A * self.ccc_alpha
            self.lambda_ = max(0.0, float(self.lambda_) + self.B * self.ccc_alpha)
            self.omega_phi = float(self.omega_phi) + self.C * self.ccc_alpha
def load_params(folder: Path) -> Params:
    p = Params()
    params_path = folder / "params.json"
    if params_path.exists():
        with open(params_path, "r", encoding="utf-8") as f:
            js = json.load(f)
        # Alias‑Mapping: "lambda" → "lambda_"
        if "lambda" in js and "lambda_" not in js:
            js["lambda_"] = js["lambda"]
        for k, v in js.items():
            if hasattr(p, k):
                setattr(p, k, v)
    p.finalize()
    return p
# -----------------------------
# K‑Potential und Ableitungen
# -----------------------------
def K_and_grad(x: List[float], phi: float, prm: Params) -> Tuple[float, List[float]]:
    """Sigmoid‑basiertes K‑Potential entlang Richtung xi_k mit Phasenmodulation.
    z = kappa * ⟨x − xi_center, xi_k⟩ + gamma0 + gamma1 * cos(phi)
    K = σ(z)
    ∇K = σ(z)(1−σ(z)) * kappa * xi_k
    """
    d = vsub(x, prm.xi_center)
    z = prm.kappa * vdot(d, prm.xi_k) + prm.gamma0 + prm.gamma1 * math.cos(phi)
    K = sigmoid(z)
    s = K * (1.0 - K)
    grad = vscale(prm.xi_k, prm.kappa * s)
    return K, grad

def lambda_adaptive(C: float, dphi: float, lambda_base: float,
                    lambda_min_rel: float = 0.2,
                    lambda_max_rel: float = 0.8) -> float:
    """Adaptive Rueckholrate lambda_eff(C, dphi) nach TSM-84/TSM-136D/TSM-146.

    C           : Koharenzmaß, hier typischerweise K in [0,1].
    dphi        : Phasenwinkel (Radiant).
    lambda_base : Basis-Rueckholrate (z.B. prm.lambda_).
    lambda_min_rel, lambda_max_rel : Minimaler bzw. maximaler relativer Faktor.
    """
    if lambda_base <= 0.0:
        return 0.0
    # |Delta phi| verwenden und auf [0, pi] begrenzen
    dphi_abs = min(abs(dphi), math.pi)
    # PLV-Phasenterm: |cos(Delta phi)| in [0, 1]
    plv = abs(math.cos(dphi_abs))
    # relative Rueckholrate in [lambda_min_rel, lambda_max_rel]
    lam_rel = lambda_min_rel + (lambda_max_rel - lambda_min_rel) * (1.0 - C) * plv
    if lam_rel < lambda_min_rel:
        lam_rel = lambda_min_rel
    elif lam_rel > lambda_max_rel:
        lam_rel = lambda_max_rel
    return lambda_base * lam_rel


# -----------------------------
# Zonenlogik mit Hysterese & Dwell
# -----------------------------
ZONE_ORDER = ["F+", "F", "R↑", "R↓", "K", "K+"]

class ZoneTracker:
    """
    Tracks discrete zones with simple hysteresis/dwell logic and records intervals.
    """
    def __init__(self, prm: Params):
        self.prm = prm
        self.current: Optional[str] = None
        self.dwell: int = 0
        self.entries: List[Dict[str, Any]] = []  # {zone,start,end,dwell}
        self.last_K: Optional[float] = None
        self.last_step: int = 0
        # diagnostics
        self.switch_attempts: int = 0
        self.veto_count: int = 0

    def _propose(self, K: float, Kdot: float) -> str:
        p = self.prm
        if K >= p.B_hi and Kdot >= p.hK:
            return "K+"
        if K >= p.B_hi:
            return "K"
        if K <= p.S_lo and Kdot <= -p.hK:
            return "F+"
        if K <= p.S_lo:
            return "F"
        if Kdot > 0.0:
            return "R↑"
        return "R↓"

    def step(self, step_idx: int, K: float, Kprev: Optional[float]) -> str:
        p = self.prm
        Kdot = 0.0 if Kprev is None else (K - Kprev) / p.dtau
        prop = self._propose(K, Kdot)

        if self.current is None:
            self.current = prop
            self.dwell = 1
            self.last_step = step_idx
            self.last_K = K
            return self.current

        if prop != self.current:
            self.switch_attempts += 1
            if self.dwell >= p.N_dwell:
                # add hysteresis guards around thresholds
                if self.current in ("K", "K+") and K >= (p.B_hi - p.hK):
                    pass  # stay bound until clear fall
                elif self.current in ("F", "F+") and K <= (p.S_lo + p.hK):
                    pass  # stay free until clear rise
                else:
                    # commit switch: close previous interval
                    self.entries.append({
                        "zone": self.current,
                        "start": self.last_step - self.dwell + 1,
                        "end": self.last_step,
                        "dwell": self.dwell,
                    })
                    self.current = prop
                    self.dwell = 1
            else:
                # not long enough: veto switch
                self.veto_count += 1
                self.dwell += 1
        else:
            self.dwell += 1

        self.last_step = step_idx
        self.last_K = K
        return self.current
# -----------------------------
# Integrator
# -----------------------------
@dataclass
class State:
    tau: float
    x: List[float]
    v: List[float]
    eps: float
    phi: float
    K: float
    Kdot: float
    zone: str
def simulate(prm: Params, out_dir: Path) -> List[State]:
    random.seed(prm.seed)
    # Anfangswerte
    x = list(prm.x_star)
    v = [0.0, 0.0, 0.0]
    # leichte Startstörung, um Bewegung zu initiieren
    jitter = 0.01
    x = [xi + (random.random() - 0.5) * jitter for xi in x]
    eps = 1.0
    phi = 0.0
    K, gK = K_and_grad(x, phi, prm)
    Kprev: Optional[float] = None
    zones = ZoneTracker(prm)
    states: List[State] = []
    tau = 0.0
    # Output‑Dateien vorbereiten
    out_dir.mkdir(parents=True, exist_ok=True)
    traj_path = out_dir / "trajectory.csv"
    z_path = out_dir / "zones.csv"
    log_path = out_dir / "run.log.jsonl"
    traj_writer = csv.writer(open(traj_path, "w", newline=""))
    include_alpha_cols = (abs(getattr(prm,"alpha",1.0) - 1.0) > 1e-12) or (getattr(prm, "alpha_mode", "off") != "off" and abs(getattr(prm, "ccc_alpha", 0.0)) > 0.0) or (abs(getattr(prm,"A",0.0))+abs(getattr(prm,"B",0.0))+abs(getattr(prm,"C",0.0))>0.0)
    traj_header = [
        "step","tau",
        "x0","x1","x2","v0","v1","v2",
        "K","eps","phi","Kdot","zone", 'F_flag']
    if include_alpha_cols:
        traj_header += ["alpha","ccc_alpha"]
    traj_header += ["PLV_tau","Q_eff","R_combo","gate_ok","anti_typ","anti_score"]

    traj_header += ["F_flag"]
    traj_writer.writerow(traj_header)
    z_writer = csv.writer(open(z_path, "w", newline=""))
    z_writer.writerow(["zone","start","end","dwell"])
    log_f = open(log_path, "w", encoding="utf-8")
    try:
        log_f.write(json.dumps({"config": {"alpha": getattr(prm, "alpha", 1.0), "alpha_mode": getattr(prm, "alpha_mode", "off"), "ccc_alpha": getattr(prm, "ccc_alpha", 0.0), "A": getattr(prm, "A", 0.0), "B": getattr(prm, "B", 0.0), "C": getattr(prm, "C", 0.0), "gamma0": prm.gamma0, "gamma1": prm.gamma1, "lambda_": prm.lambda_}}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    for step in range(prm.steps):
        # gate diagnostics
        gate_fail = 0
        gate_near = 0
        near_plv = 0.55
        near_eps_factor = 1.5
        # Zonenlogik
        zone = zones.step(step, K, Kprev)
        # --- TSM-146 Anti-Atlas metrics ---
        dphi = abs(phi)
        PLV_tau = abs(math.cos(phi))
        eps_rad = getattr(prm, "eps_phi", 0.01745)  # ≈ 1° fallback
        Q_eff = tau / max(dphi, eps_rad) if max(dphi, eps_rad) > 0 else 0.0
        R_raw = Q_eff * PLV_tau
        R_combo = R_raw / (1.0 + R_raw) if R_raw >= 0 else 0.0
        gate_ok = (dphi <= 0.10) and (PLV_tau >= 0.60)  # defaults; may be parameterized
        if not gate_ok:
            gate_fail += 1
            if (dphi <= near_eps_factor * eps_rad) or (PLV_tau >= near_plv):
                gate_near += 1
        if not gate_ok:
            anti_typ, anti_score = "n/a", 0.0
        else:
            if R_combo >= 0.66:
                anti_typ = "A1"
            elif (Q_eff >= 1.0) and (R_combo < 0.66):
                anti_typ = "A2" if tau > 1.0 else "A3"
            elif R_combo >= 0.33:
                anti_typ = "A3"
            else:
                anti_typ = "A4"
            anti_score = R_combo
        # Log & Trajektorie schreiben

        # --- F-phase detection (TSM-150) ---
        dphi = abs(phi)
        PLV_tau = abs(math.cos(phi))
        eps_rad = getattr(prm, "eps_phi", 0.01745)
        Q_eff = tau / max(dphi, eps_rad) if max(dphi, eps_rad) > 0 else 0.0
        R_raw = Q_eff * PLV_tau
        R_combo = R_raw / (1.0 + R_raw) if R_raw >= 0 else 0.0  # 0..1
        # normalized Q̂ proxy from Q_eff
        Qhat_norm = Q_eff / (1.0 + Q_eff) if Q_eff >= 0 else 0.0  # 0..1

        C_proxy = R_combo  # coherence proxy in [0,1]
        in_C = (C_proxy < 0.2)
        in_phi = (dphi >= 0.01745)  # ≥ 1°
        in_Qhat = (0.2 <= Qhat_norm <= 0.3)
        # slope negative? compare to short rolling mean
        qhat_hist.append(Qhat_norm)
        if len(qhat_hist) > 5:
            qhat_hist.pop(0)
        slope_neg = False
        if len(qhat_hist) >= 2:
            prev_mean = sum(qhat_hist[:-1]) / max(1, len(qhat_hist)-1)
            slope_neg = (Qhat_norm < prev_mean)
        F_flag = int(in_C and in_phi and in_Qhat and slope_neg)

        # update intervals
        if F_flag and not f_active:
            f_active = True
            f_start_step = step
            f_start_tau = tau
        elif (not F_flag) and f_active:
            f_events.append((f_start_step, step-1, f_start_tau, tau))
            f_active = False
            f_start_step = None
            f_start_tau = None

        row = [ step, tau,
            x[0], x[1], x[2], v[0], v[1], v[2],
            K, eps, phi, 0.0 if Kprev is None else (K - Kprev) / prm.dtau,
            zone
        ]
        if include_alpha_cols:
            row += [prm.alpha, getattr(prm, "ccc_alpha", 0.0)]
        
        row += [int(F_flag), PLV_tau, Q_eff, R_combo, int(gate_ok), anti_typ, anti_score]
        traj_writer.writerow(row)
        log_f.write(json.dumps({
            "step": step, "tau": tau, "zone": zone,
            "x": x, "v": v, "K": K, "eps": eps, "phi": phi
        }, ensure_ascii=False) + "\n")
        states.append(State(tau, list(x), list(v), eps, phi, K,
                            0.0 if Kprev is None else (K - Kprev) / prm.dtau,
                            zone))
        # Dynamik: explizites Euler (bewusst einfach, reproduzierbar)
        # 1) ε' = −λ K ε
        lambda_min_rel = getattr(prm, "lambda_min_rel", 0.2)
        lambda_max_rel = getattr(prm, "lambda_max_rel", 0.8)
        lambda_eff = lambda_adaptive(K, phi, prm.lambda_,
                                     lambda_min_rel=lambda_min_rel,
                                     lambda_max_rel=lambda_max_rel)
        deps = -lambda_eff * K * eps
        eps_next = eps + prm.dtau * deps
        # 2) φ' = ω (schlichtes Driftmodell)
        dphi = prm.omega_phi
        phi_next = wrap_angle(phi + prm.dtau * dphi)
        # 3) Geodäsie: v' = −α ∇K − δ v
        K_curr, gradK = K_and_grad(x, phi, prm)
        for i in range(3):
            v[i] = v[i] + prm.dtau * (-prm.alpha * gradK[i] - prm.delta * v[i])
            x[i] = x[i] + prm.dtau * v[i]
        # 4) Update K
        Kprev = K
        K, _ = K_and_grad(x, phi_next, prm)
        # Fortschreiben
        eps = eps_next
        phi = phi_next
        tau += prm.dtau
        # Numerik‑Wächter
        if (math.isnan(K) or math.isinf(K) or
            any(math.isnan(q) or math.isinf(q) for q in x + v + [eps, phi])):
            # frühen Abbruch protokollieren
            break
    # Zonenabschluss
    zones.finalize()
    # --- Diagnostics summary (added by patch) ---
    try:
        n_steps = max(1, step + 1)
        summary = {
            "dwell_veto_rate": (zones.veto_count / zones.switch_attempts) if getattr(zones, "switch_attempts", 0) else 0.0,
            "switch_attempts": getattr(zones, "switch_attempts", 0),
            "veto_count": getattr(zones, "veto_count", 0),
            "gate_fail_rate": gate_fail / n_steps if 'gate_fail' in locals() else 0.0,
            "gate_near_rate": gate_near / n_steps if 'gate_near' in locals() else 0.0
        }
        log_f.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")
    except Exception:
        pass

    for e in zones.entries:
        z_writer.writerow([e["zone"], e["start"], e["end"], e["dwell"]])

    # close open F-interval
    if f_active and (f_start_step is not None):
        f_events.append((f_start_step, prm.steps-1, f_start_tau, tau))

    # write F-event file
    try:
        ev_path = out_dir / "events_f.csv"
        with open(ev_path, "w", newline="") as evf:
            import csv as _csv
            w = _csv.writer(evf)
            w.writerow(["step_start","step_end","tau_start","tau_end","dwell_steps"])
            for (s0, s1, t0, t1) in f_events:
                dwell = (s1 - s0 + 1) if (s1 is not None and s0 is not None) else 0
                w.writerow([s0, s1, f"{t0:.6f}", f"{t1:.6f}", dwell])
        # add summary to log
        try:
            with open(log_path, "a", encoding="utf-8") as _lf:
                _lf.write(json.dumps({"F_events": {"count": len(f_events)}}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception:
        pass

    log_f.close()
    return states

# -----------------------------
# Kennzahlen & Sweep
# -----------------------------
def summarize(states: List[State]) -> Dict[str, Any]:
    if not states:
        return {"n": 0}
    K_vals = [s.K for s in states]
    eps_vals = [s.eps for s in states]
    zones = [s.zone for s in states]
    shares: Dict[str, float] = {}
    n = len(states)
    for z in ZONE_ORDER:
        shares[z] = sum(1 for zz in zones if zz == z) / n
    # Stabilitätsindex (einfach): Var(K) klein & |Kdot| klein → stabil
    Kdot_vals = [s.Kdot for s in states]
    varK = statistics.pvariance(K_vals) if n > 1 else 0.0
    mean_abs_Kdot = sum(abs(d) for d in Kdot_vals) / n
    stability = 1.0 / (1.0 + varK + mean_abs_Kdot)
    return {
        "n": n,
        "K_mean": sum(K_vals) / n,
        "K_median": statistics.median(K_vals),
        "eps_last": eps_vals[-1],
        "stability": stability,
        **{f"share_{k}": v for k, v in shares.items()},
    }
def sweep(root: Path, out_dir: Path):
    # Grid laden (optional)
    grid_path = root / "grid.json"
    if grid_path.exists():
        with open(grid_path, "r", encoding="utf-8") as f:
            grid = json.load(f)
    else:
        # eingebautes Mini‑Grid
        grid = {
            "alpha": [0.5, 1.0, 2.0],
            "lambda_": [0.5, 1.0, 2.0],
            "gamma1": [0.5, 1.0],
        }
    # Kartesisch erzeugen
    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    def rec(idx: int, cur: Dict[str, Any], acc: List[Dict[str, Any]]):
        if idx == len(keys):
            acc.append(cur.copy())
            return
        k = keys[idx]
        for v in values[idx]:
            cur[k] = v
            rec(idx + 1, cur, acc)
    combos: List[Dict[str, Any]] = []
    rec(0, {}, combos)
    out_dir.mkdir(parents=True, exist_ok=True)
    sum_path = out_dir / "sweep_summary.csv"
    with open(sum_path, "w", newline="") as fsum:
        writer = None
        case_no = 0
        for combo in combos:
            case_no += 1
            # params vorbereiten
            prm = load_params(root)
            for k, v in combo.items():
                if hasattr(prm, k):
                    setattr(prm, k, v)
            prm.finalize()
            # Lauf
            run_dir = out_dir / f"case_{case_no:04d}"
            states = simulate(prm, run_dir)
            # Summary schreiben
            summ = summarize(states)
            row = {"case": case_no, **combo, **summ}
            if writer is None:
                writer = csv.DictWriter(fsum, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow(row)
# -----------------------------
# Checks
# -----------------------------
def taucheck(root: Path, out_dir: Path):
    """Vergleicht zwei Läufe mit (dtau, steps) vs. (a*dtau, steps/a)"""
    prm = load_params(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Basis
    states_a = simulate(prm, out_dir / "taucheck_a")
    sum_a = summarize(states_a)
    # Skaliert
    a = 2.0  # fester Faktor für v0.2
    prm2 = load_params(root)
    prm2.dtau = prm.dtau * a
    prm2.steps = max(1, int(prm.steps / a))
    prm2.finalize()
    states_b = simulate(prm2, out_dir / "taucheck_b")
    sum_b = summarize(states_b)
    # Vergleich protokollieren
    with open(out_dir / "taucheck_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "a": a,
            "base": sum_a,
            "scaled": sum_b,
            "delta": {k: (sum_b.get(k) - sum_a.get(k)) for k in sum_a.keys() if k in sum_b}
        }, f, ensure_ascii=False, indent=2)
def stabcheck(root: Path, out_dir: Path):
    prm = load_params(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for dt in [prm.dtau * f for f in [0.5, 1.0, 1.5, 2.0, 3.0]]:
        prm2 = load_params(root)
        prm2.dtau = dt
        prm2.steps = prm.steps
        prm2.finalize()
        states = simulate(prm2, out_dir / f"stab_dt_{dt:.6f}")
        bad = any(
            math.isnan(s.K) or math.isinf(s.K) or
            any(math.isnan(q) or math.isinf(q) for q in s.x + s.v + [s.eps, s.phi])
            for s in states
        )
        summ = summarize(states)
        results.append({
            "dtau": dt,
            "n": summ.get("n", 0),
            "stable": (not bad) and summ.get("n", 0) > 0,
            **summ,
        })
    with open(out_dir / "stabcheck_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        for r in results:
            writer.writerow(r)
# -----------------------------
# CLI
# -----------------------------
def read_summary(out_dir: Path):
    """Read the last JSON object with a 'summary' field from run.log.jsonl in out_dir."""
    log_file = out_dir / "run.log.jsonl"
    if not log_file.exists():
        return {}
    try:
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                j = json.loads(line)
                if isinstance(j, dict) and "summary" in j:
                    return j["summary"]
            except Exception:
                continue
        return {}
    except Exception:
        return {}

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="TSM–GR v0.2 Runner")
    sp = ap.add_subparsers(dest="cmd", required=True)
    ap.add_argument("--out", type=str, default="./out", help="Output‑Verzeichnis (default: ./out)")
    ap.add_argument("--root", type=str, default=".", help="Root/Arbeitsverzeichnis (default: .)")
    sp.add_parser("run", help="Einzellauf mit params.json (optional)")
    sp.add_parser("sweep", help="Sweep über Grid (grid.json optional; sonst eingebautes Grid)")
    sp.add_parser("taucheck", help="τ‑Reparametrisations‑Check")
    sp.add_parser("stabcheck", help="Stabilitäts‑Guard")
    sp_auto = sp.add_parser("auto", help="Audit-Run und optionaler Auto-Preview")
    sp_auto.add_argument("--dwell-veto-threshold", type=float, default=0.20, help="Grenze für dwell_veto_rate")
    sp_auto.add_argument("--gate-near-threshold", type=float, default=0.10, help="Grenze für gate_near_rate")
    sp_auto.add_argument("--preview-N-dwell", type=int, default=11, help="N_dwell im Preview-Lauf")
    sp_auto.add_argument("--tau-lock-mode", type=str, default="soft", help="Hinweisflag für Analyzer")
    ap.add_argument("--alpha", type=float, help="Override dynamics coupling α (−α∇K)")
    ap.add_argument("--alpha-mode", type=str, choices=["off","ccc_map"], help="CCC mapping mode (default: off)")
    ap.add_argument("--ccc-alpha", type=float, help="External CCC alpha parameter")
    ap.add_argument("--A", type=float, help="Mapping coefficient for ΔK = A*α")
    ap.add_argument("--B", type=float, help="Mapping coefficient for Δλ = B*α")
    ap.add_argument("--C", type=float, help="Mapping coefficient for Δφ via ωφ offset = C*α")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    if args.cmd == "run":
        prm = load_params(root)
        # CLI overrides (alpha + CCC mapping)
        if args.alpha is not None:
            prm.alpha = args.alpha
        if args.alpha_mode:
            prm.alpha_mode = args.alpha_mode
        if args.ccc_alpha is not None:
            prm.ccc_alpha = args.ccc_alpha
        if args.A is not None:
            prm.A = args.A
        if args.B is not None:
            prm.B = args.B
        if args.C is not None:
            prm.C = args.C
        prm.finalize()
        simulate(prm, out)
        return 0
if args.cmd == "auto":
    # Strict AUDIT
    out_audit = out / "audit"
    prm.finalize()
    simulate(prm, out_audit)
    s = read_summary(out_audit) or {}
    dv = float(s.get("dwell_veto_rate", 0.0) or 0.0)
    gn = float(s.get("gate_near_rate", 0.0) or 0.0)
    # Decide on PREVIEW
    need_preview = (dv > getattr(args, "dwell_veto_threshold", 0.20)) or (gn > getattr(args, "gate_near_threshold", 0.10))
    if not need_preview:
        # Write sidecar summary and finish
        side = {
            "run_mode": "audit",
            "audit_summary": s,
            "thresholds": {
                "dwell_veto_rate": getattr(args, "dwell_veto_threshold", 0.20),
                "gate_near_rate": getattr(args, "gate_near_threshold", 0.10)
            }
        }
        with open(out / "autopilot_summary.json", "w", encoding="utf-8") as f:
            json.dump(side, f, ensure_ascii=False, indent=2)
        return 0
    # PREVIEW with lighter settings
    out_preview = out / "preview"
    prm2 = load_params(root)
    # carry select overrides if provided
    if args.alpha is not None: prm2.alpha = args.alpha
    if args.alpha_mode is not None: prm2.alpha_mode = args.alpha_mode
    if args.ccc_alpha is not None: prm2.ccc_alpha = args.ccc_alpha
    if args.A is not None: prm2.A = args.A
    if args.B is not None: prm2.B = args.B
    if args.C is not None: prm2.C = args.C
    prm2.N_dwell = int(getattr(args, "preview_N_dwell", 11))
    prm2.finalize()
    simulate(prm2, out_preview)
    side = {
        "run_mode": "audit+preview",
        "audit_summary": s,
        "trigger": {
            "dwell_veto_rate": dv,
            "gate_near_rate": gn,
            "thresholds": {
                "dwell_veto_rate": getattr(args, "dwell_veto_threshold", 0.20),
                "gate_near_rate": getattr(args, "gate_near_threshold", 0.10)
            }
        },
        "preview_params": {
            "N_dwell": prm2.N_dwell,
            "tau_lock_mode": getattr(args, "tau_lock_mode", "soft")
        }
    }
    with open(out / "autopilot_summary.json", "w", encoding="utf-8") as f:
        json.dump(side, f, ensure_ascii=False, indent=2)
    return 0
    if args.cmd == "sweep":
        sweep(root, out)
        return 0
    if args.cmd == "taucheck":
        taucheck(root, out)
        return 0
    if args.cmd == "stabcheck":
        stabcheck(root, out)
        return 0
    return 1
if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------
# CFDR (TSM-147) — Universelles Metrikmodell (C/D/R/F) — Helper
# Additiv integriert; keine Änderung am bestehenden Runner-Verhalten.
# Exportierte Funktionen: compute_cfdr, apply_hysteresis
# ---------------------------------------------------------------------
def _cfdr_plv_from_dphi(dphi_rad: float) -> float:
    import math
    return abs(math.cos(float(dphi_rad)))

def compute_cfdr(
    axes: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
    gate: Optional[Dict[str, float]] = None,
    dphi_rad: Optional[float] = None,
    plv_override: Optional[float] = None
) -> Tuple[float, bool]:
    """
    Compute CFDR index and gate_ok.

    axes: dict with keys 'C','D','R','F' in [0,1]
    weights: dict with keys 'C','D','R','F' summing to 1.0 (defaults to 0.30/0.20/0.20/0.30)
    gate: dict with {'eps_rad': float, 'plv_min': float} defaults to 1° and 0.60
    dphi_rad: optional phase deviation (rad) for PLV gating
    plv_override: optional PLV to use directly (if provided, dphi_rad is ignored)

    Returns: (index, gate_ok)
    """
    w = weights or {"C":0.30,"D":0.20,"R":0.20,"F":0.30}
    g = gate or {"eps_rad": 0.0174519943295, "plv_min": 0.60}

    # Clamp inputs to [0,1] to be robust
    C = max(0.0, min(1.0, float(axes.get("C", 0.0))))
    D = max(0.0, min(1.0, float(axes.get("D", 0.0))))
    R = max(0.0, min(1.0, float(axes.get("R", 0.0))))
    F = max(0.0, min(1.0, float(axes.get("F", 0.0))))

    idx = C * float(w.get("C", 0.0)) + D * float(w.get("D", 0.0)) + R * float(w.get("R", 0.0)) + F * float(w.get("F", 0.0))

    # Gate logic
    if plv_override is not None:
        plv = float(plv_override)
        dphi_ok = True  # caller is responsible for dphi check when overriding PLV
    else:
        if dphi_rad is None:
            # Conservatively fail gate if no phase information is provided
            return idx, False
        plv = _cfdr_plv_from_dphi(float(dphi_rad))
        dphi_ok = abs(float(dphi_rad)) <= float(g.get("eps_rad", 0.0174519943295))

    gate_ok = (plv >= float(g.get("plv_min", 0.60))) and dphi_ok
    return idx, gate_ok

def apply_hysteresis(prev_index: float, new_index: float, delta_min: float = 0.02) -> float:
    """
    Apply minimal delta threshold on the aggregated index for status switching.
    Simple deadband around prev_index.
    """
    if abs(new_index - prev_index) < float(delta_min):
        return float(prev_index)
    return float(new_index)


# --- F-PHASE (TSM-150) INLINE DETECTOR ---------------------------------------
# Criteria: C < 0.2, |Δϕ| ≥ 1° (0.01745 rad), Q̂ in [0.2, 0.3] and decreasing, within τ-lock
# This block is self-contained; it requires pandas and numpy if CSV-based detection is used.

def _map_columns(df):
    """
    Map flexible column names in df to the canonical set:
    time, C, dphi_rad, Qhat, tau_lock
    Heuristics:
      - C: prefer 'C', else 'coherence', else 'R_combo' (used as proxy)
      - dphi_rad: prefer 'dphi_rad', else 'dphi', else build from 'dphi_deg' * pi/180
      - Qhat: prefer 'Qhat', else 'Qhat_norm', else build from Q_eff/(1+Q_eff)
      - tau_lock: 'tau_lock' if present otherwise True
      - time: prefer 'time', else 't', else index
    """
    import numpy as np
    import pandas as pd

    out = df.copy()
    cols = {c.lower(): c for c in df.columns}

    # time
    time_col = None
    for k in ["time", "t"]:
        if k in cols:
            time_col = cols[k]
            break
    if time_col is None:
        out["time"] = np.arange(len(out), dtype=float)
    else:
        if time_col != "time":
            out = out.rename(columns={time_col: "time"})

    # C
    C_col = None
    for k in ["c", "coherence", "r_combo"]:
        if k in cols:
            C_col = cols[k]
            break
    if C_col is None:
        raise ValueError("No coherence-like column found (expected one of: C, coherence, R_combo)")
    if C_col != "C":
        out = out.rename(columns={C_col: "C"})

    # dphi_rad
    dphi_col = None
    for k in ["dphi_rad", "dphi"]:
        if k in cols:
            dphi_col = cols[k]
            break
    if dphi_col is None and "dphi_deg" in cols:
        out["dphi_rad"] = out[cols["dphi_deg"]].astype(float) * (3.141592653589793/180.0)
    elif dphi_col is not None and dphi_col != "dphi_rad":
        out = out.rename(columns={dphi_col: "dphi_rad"})
    elif dphi_col is None:
        raise ValueError("No dphi column found (need dphi_rad, dphi, or dphi_deg)")

    # Qhat
    if "qhat" in cols:
        if cols["qhat"] != "Qhat":
            out = out.rename(columns={cols["qhat"]:"Qhat"})
    elif "qhat_norm" in cols:
        out = out.rename(columns={cols["qhat_norm"]:"Qhat"})
    elif "q_eff" in cols:
        out["Qhat"] = out[cols["q_eff"]].astype(float) / (1.0 + out[cols["q_eff"]].astype(float))
    else:
        raise ValueError("No Q-like column found (need Qhat, Qhat_norm, or Q_eff to derive Qhat)")

    # tau_lock
    if "tau_lock" in cols:
        if cols["tau_lock"] != "tau_lock":
            out = out.rename(columns={cols["tau_lock"]:"tau_lock"})
        out["tau_lock"] = out["tau_lock"].astype(bool)
    else:
        out["tau_lock"] = True

    return out[["time", "C", "dphi_rad", "Qhat", "tau_lock"]]

def detect_f_intervals(df, C_lt=0.2, dphi_ge_rad=0.01745, Qwin=(0.2,0.3), require_tau=True, slope_window=5):
    """Return list of (t_start, t_end) F-phase intervals."""
    import numpy as np
    import pandas as pd
    d = _map_columns(df)
    mask_C = d["C"].astype(float) < C_lt
    mask_phi = d["dphi_rad"].abs() >= dphi_ge_rad
    qmin, qmax = Qwin
    mask_Qwin = (d["Qhat"].astype(float) >= qmin) & (d["Qhat"].astype(float) <= qmax)

    dq = d["Qhat"].astype(float).diff()
    if slope_window and slope_window > 1:
        dq = dq.rolling(slope_window, min_periods=1).mean()
    mask_Qdown = dq < 0

    mask_tau = d["tau_lock"].astype(bool) if require_tau else True
    mask = mask_C & mask_phi & mask_Qwin & mask_Qdown & mask_tau

    events = []
    if mask.any():
        idx = mask[mask].index.to_numpy()
        # find runs
        gaps = (idx[1:] - idx[:-1]) > 1
        split_idx = [0] + (list((gaps.nonzero()[0] + 1))) + [len(idx)]
        for a, b in zip(split_idx[:-1], split_idx[1:]):
            seg = idx[a:b]
            t0 = float(d.loc[seg[0], "time"])
            t1 = float(d.loc[seg[-1], "time"])
            events.append((t0, t1))
    return events

def run_f_detection_on_csv(csv_path, out_path="events_f.csv", **kwargs):
    import pandas as pd
    df = pd.read_csv(csv_path)
    events = detect_f_intervals(df, **kwargs)
    out_df = pd.DataFrame(events, columns=["t_start", "t_end"])
    out_df.to_csv(out_path, index=False)
    return out_df

def cli_detect_f(args):
    """CLI hook: --detect-f CSV [--out events_f.csv]"""
    csv_path = None
    out_path = "events_f.csv"
    if "--detect-f" in args:
        i = args.index("--detect-f")
        if i+1 < len(args):
            csv_path = args[i+1]
    if "--out" in args:
        j = args.index("--out")
        if j+1 < len(args):
            out_path = args[j+1]
    if csv_path:
        df = run_f_detection_on_csv(csv_path, out_path=out_path,
                                    C_lt=0.2, dphi_ge_rad=0.01745,
                                    Qwin=(0.2,0.3), require_tau=True, slope_window=5)
        print(f"[F-phase] {len(df)} event(s) written to {out_path}")
    return 0

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Provide a CLI entry point for F-detection without changing existing behavior.
    try:
        import sys
        cli_detect_f(sys.argv[1:])
    except Exception as e:
        # Fail-safe: do not break existing runs if detection is irrelevant
        print(f"[F-phase] detection hook error: {e}")


# === BEGIN Q_PRE_F_ANNOTATOR ===
# Built-in post-run annotator for Q_pre (3° pre-gate) and F-phase (TSM-150).
# Usage examples:
#   python tsmgr_v02.py --annotate --in trajectory.csv --out trajectory_annotated.csv
#   python tsmgr_v02.py --annotate --in trajectory.csv --out trajectory_annotated.csv --no-f
# --------------------------------------------------------------------
# TSM-166 / 136D-Hinweis zur Spaltenbehandlung (Kn, tau_eff, kappa_density, C_hat,
# Ethics- und Experience-Layer)
# --------------------------------------------------------------------
# Der eingebaute Annotator (_tsm_map_columns_for_flags / tsm_cli_qpre_annotate)
# arbeitet minimal-invasiv:
#   - er normalisiert nur die für Q_pre/F-Phase nötigen Spalten
#     (time/t, C, dphi_*, Qhat, tau_lock)
#   - alle anderen Spalten bleiben unverändert im DataFrame erhalten.
#
# Für die Kopplung an TSM-136D / TSM-166 gilt:
#   • Folgende Spaltennamen werden (falls vorhanden) einfach durchgereicht
#     und später vom 136D-Analyzer verwendet:
#         - "Kn"            → Medien-Kohärenzachse (Kₙ = λ / L)
#         - "tau_eff"       → effektive Zeitdichte (Achse τ)
#         - "kappa_density" → Dichte der Tunnelkrümmung (Achse κ)
#         - "C_hat"         → empirische Kohärenzschätzung (≈ C_eff(Kₙ))
#         - "ethics_mode"   → observe | intervene (TSM-118 Rahmen)
#         - "ethics_context"→ Kurzbeschreibung des Kontexts
#         - "consent_ok"    → bool, explizite Einwilligung ja/nein
#         - "E_valence"     → Erleben-Achse: angenehm ↔ unangenehm
#         - "E_clarity"     → Erleben-Achse: klar ↔ diffus
#         - "E_load"        → Erleben-Achse: leicht ↔ überlastet
#         - "E_connected"   → Erleben-Achse: verbunden ↔ isoliert
#
#   • Der Runner/Annotator berechnet diese Größen NICHT selbst, sondern
#     liest sie – falls vorhanden – aus trajectory.csv / zones.csv und
#     lässt sie unverändert stehen.
#
# Damit bleibt tsmgr_v02:
#   - vollständig rückwärtskompatibel
#   - aber kompatibel zur 136D-/TSM-166-Auswertung, sobald diese Spalten
#     im CSV auftauchen.
# --------------------------------------------------------------------
def _tsm_map_columns_for_flags(df):
    import numpy as np
    import pandas as pd
    cols = {c.lower(): c for c in df.columns}
    out = df.copy()

    # time
    time_col = None
    for k in ["time","t"]:
        if k in cols:
            time_col = cols[k]; break
    if time_col is None:
        out["time"] = np.arange(len(out), dtype=float)
    elif time_col != "time":
        out = out.rename(columns={time_col:"time"})

    # C
    for k in ["c","coherence","r_combo"]:
        if k in cols:
            if cols[k] != "C": out = out.rename(columns={cols[k]:"C"})
            break
    if "C" not in out.columns:
        out["C"] = float("nan")

    # dphi
    import math
    if "dphi_rad" in cols:
        if cols["dphi_rad"] != "dphi_rad":
            out = out.rename(columns={cols["dphi_rad"]:"dphi_rad"})
    elif "dphi" in cols:
        out = out.rename(columns={cols["dphi"]:"dphi_rad"})
    elif "dphi_deg" in cols:
        out["dphi_rad"] = out[cols["dphi_deg"]].astype(float) * (math.pi/180.0)
    else:
        raise ValueError("No dphi column found")

    # Qhat
    if "qhat" in cols:
        if cols["qhat"] != "Qhat": out = out.rename(columns={cols["qhat"]:"Qhat"})
    elif "qhat_norm" in cols:
        out = out.rename(columns={cols["qhat_norm"]:"Qhat"})
    elif "q_eff" in cols:
        out["Qhat"] = out[cols["q_eff"]].astype(float) / (1.0 + out[cols["q_eff"]].astype(float))
    else:
        out["Qhat"] = float("nan")

    # tau_lock
    if "tau_lock" in cols:
        if cols["tau_lock"] != "tau_lock":
            out = out.rename(columns={cols["tau_lock"]:"tau_lock"})
        out["tau_lock"] = out["tau_lock"].astype(bool)
    else:
        out["tau_lock"] = False

    return out[["time","C","dphi_rad","Qhat","tau_lock"]]

def tsm_compute_qpre_f_flags(df, enable_f=True):
    import math, numpy as np, pandas as pd
    d = _tsm_map_columns_for_flags(df)

    # Q_pre (3°) with hysteresis: need ≥3 consecutive hits to set; drop after ≥2 misses
    eps_pre = math.radians(3.0)
    plv_pre = math.cos(eps_pre)
    qpre = (d["dphi_rad"].abs() <= eps_pre) & (np.cos(d["dphi_rad"].abs()) >= plv_pre)

    qpre_count, miss_count = 0, 0
    qpre_flag = []
    for ok in qpre.values:
        if ok:
            qpre_count += 1
            if qpre_count >= 3:
                qpre_flag.append(1)
            else:
                qpre_flag.append(0)
            miss_count = 0
        else:
            miss_count += 1
            if miss_count >= 2:
                qpre_count = 0
            qpre_flag.append(0)

    # F-phase (TSM-150): C<0.2, |Δϕ|≥1°, Q̂∈[0.2,0.3]↓, τ-lock=True
    F_flag = [0]*len(d)
    if enable_f:
        C_lt = 0.2
        dphi_ge = math.radians(1.0)
        qmin, qmax = 0.2, 0.3
        slope = d["Qhat"].diff().rolling(5, min_periods=1).mean()
        mask = (d["C"] < C_lt) & (d["dphi_rad"].abs() >= dphi_ge) &                (d["Qhat"].between(qmin, qmax)) & (slope < 0) & (d["tau_lock"]==True)
        F_flag = mask.astype(int).tolist()

    out = df.copy()
    out["Q_pre_flag"] = qpre_flag
    out["F_flag"] = F_flag
    return out

def tsm_cli_qpre_annotate(argv):
    # Parses: --annotate --in <csv> --out <csv> [--no-f]
    if "--annotate" not in argv:
        return False
    try:
        inp = None; outp = None; enable_f = True
        if "--in" in argv:
            i = argv.index("--in")
            inp = argv[i+1]
        if "--out" in argv:
            i = argv.index("--out")
            outp = argv[i+1]
        if "--no-f" in argv:
            enable_f = False
        if not inp or not outp:
            print("[annotate] Please provide --in <csv> and --out <csv>")
            return True
        import pandas as pd
        df = pd.read_csv(inp)
        ann = tsm_compute_qpre_f_flags(df, enable_f=enable_f)
        ann.to_csv(outp, index=False)
        print(f"[annotate] wrote {outp} with columns: {list(ann.columns)}")
        return True
    except Exception as e:
        print(f"[annotate] error: {e}")
        return True

# Hook into __main__ without breaking existing CLI.
def _tsm_try_cli_hooks():
    try:
        import sys
        handled = tsm_cli_qpre_annotate(sys.argv[1:])
        return handled
    except Exception as _e:
        return False
# === END Q_PRE_F_ANNOTATOR ===


if __name__ == "__main__":
    # Non-invasive hook: run annotator if '--annotate' is present; otherwise keep existing behavior intact.
    _tsm_try_cli_hooks()
