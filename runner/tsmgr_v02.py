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
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import argparse, csv, json, math, random, sys, statistics

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
    eps_phi: float = 0.087266   # ~5° (π/36)
    hK: float = 0.02            # Schwell‑Hysterese auf K / Kdot
    N_dwell: int = 3            # Mindestverweildauer pro Zone
    # Integration
    dtau: float = 0.1
    steps: int = 300
    seed: int = 0
    # Phasenlage / Modus
    omega_phi: float = 0.0
    mode: str = "potential"     # {"potential"|"residual"}
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

# -----------------------------
# Zonenlogik mit Hysterese & Dwell
# -----------------------------

ZONE_ORDER = ["F+", "F", "R↑", "R↓", "K", "K+"]

class ZoneTracker:
    def __init__(self, prm: Params):
        self.prm = prm
        self.current: Optional[str] = None
        self.dwell: int = 0
        self.entries: List[Dict[str, Any]] = []  # {zone, start, end, dwell}
        self.last_K: Optional[float] = None
        self.last_step: int = 0

    def _propose(self, K: float, Kdot: float) -> str:
        p = self.prm
        # Entscheidungsregeln (einfach, reproduzierbar)
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
            # erste Zone übernehmen
            self.current = prop
            self.dwell = 1
            self.last_step = step_idx
            self.last_K = K
            return self.current
        # Hysterese / Mindest‑Dwell
        if prop != self.current:
            # Wechsel nur, wenn Mindestverweildauer erreicht und Schwellwert eindeutig
            if self.dwell >= p.N_dwell:
                # Zusatz: bei Grenznähe K‑Hysterese erzwingen
                if self.current in ("K", "K+") and K >= (p.B_hi - p.hK):
                    # bleib gebunden bis klarer Abfall
                    pass
                elif self.current in ("F", "F+") and K <= (p.S_lo + p.hK):
                    # bleib frei bis klarer Anstieg
                    pass
                else:
                    # commit Wechsel
                    self.entries.append({
                        "zone": self.current,
                        "start": self.last_step - self.dwell + 1,
                        "end": self.last_step,
                        "dwell": self.dwell,
                    })
                    self.current = prop
                    self.dwell = 1
            else:
                # noch nicht lange genug → bleibe
                self.dwell += 1
        else:
            self.dwell += 1
        self.last_step = step_idx
        self.last_K = K
        return self.current

    def finalize(self):
        if self.current is not None:
            self.entries.append({
                "zone": self.current,
                "start": self.last_step - self.dwell + 1,
                "end": self.last_step,
                "dwell": self.dwell,
            })

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
    traj_writer.writerow([
        "step","tau",
        "x0","x1","x2","v0","v1","v2",
        "K","eps","phi","Kdot","zone"
    ])
    z_writer = csv.writer(open(z_path, "w", newline=""))
    z_writer.writerow(["zone","start","end","dwell"])
    log_f = open(log_path, "w", encoding="utf-8")

    for step in range(prm.steps):
        # Zonenlogik
        zone = zones.step(step, K, Kprev)

        # Log & Trajektorie schreiben
        traj_writer.writerow([
            step, tau,
            x[0], x[1], x[2], v[0], v[1], v[2],
            K, eps, phi, 0.0 if Kprev is None else (K - Kprev) / prm.dtau,
            zone
        ])
        log_f.write(json.dumps({
            "step": step, "tau": tau, "zone": zone,
            "x": x, "v": v, "K": K, "eps": eps, "phi": phi
        }, ensure_ascii=False) + "\n")

        states.append(State(tau, list(x), list(v), eps, phi, K,
                            0.0 if Kprev is None else (K - Kprev) / prm.dtau,
                            zone))

        # Dynamik: explizites Euler (bewusst einfach, reproduzierbar)
        # 1) ε' = −λ K ε
        deps = -prm.lambda_ * K * eps
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
    for e in zones.entries:
        z_writer.writerow([e["zone"], e["start"], e["end"], e["dwell"])

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

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="TSM–GR v0.2 Runner")
    sp = ap.add_subparsers(dest="cmd", required=True)

    ap.add_argument("--out", type=str, default="./out", help="Output‑Verzeichnis (default: ./out)")
    ap.add_argument("--root", type=str, default=".", help="Root/Arbeitsverzeichnis (default: .)")

    sp.add_parser("run", help="Einzellauf mit params.json (optional)")
    sp.add_parser("sweep", help="Sweep über Grid (grid.json optional; sonst eingebautes Grid)")
    sp.add_parser("taucheck", help="τ‑Reparametrisations‑Check")
    sp.add_parser("stabcheck", help="Stabilitäts‑Guard")

    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()

    if args.cmd == "run":
        prm = load_params(root)
        simulate(prm, out)
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
