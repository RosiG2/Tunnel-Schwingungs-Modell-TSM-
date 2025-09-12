#!/usr/bin/env python3
"""
TSM–GR Runner v0.2 — Ein‑Datei‑Runner (Sim, Zonen, Sweeps)
-----------------------------------------------------------

Funktionen:
  • run      – Einzellauf mit Defaults/Overrides
  • sweep    – Parameter-Sweeps (eingebaute Grids + optionales grid.json)
  • taucheck – τ‑Reparametrisations‑Check
  • stabcheck– Stabilitätsprüfung (ε‑Abbau‑Guard, Robustheit)

Ziele / Design:
  • Keine externen Abhängigkeiten (nur Python 3.9+)
  • Reproduzierbar (seed, Param‑Snapshot)
  • Robuste Zonenlogik (Hysterese, Dwell, Prioritäts‑Guards)
  • Ausgaben als CSV + JSONL für nachgelagerte Analyse

Lizenz: CC‑BY‑4.0
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional, Iterable
import json, math, random, argparse, csv, sys
from pathlib import Path

# -----------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sigmoid(z: float) -> float:
    # numerisch stabile Sigmoid
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            pass
        return
    cols = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def cartesian_grid(spec: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    # spec: {"alpha": [0.5,1.0], "lambda_": [0.5,1.0]}
    keys = list(spec.keys())
    values = [spec[k] if isinstance(spec[k], list) else [spec[k]] for k in keys]
    grids: List[Dict[str, Any]] = []
    def rec(i: int, cur: Dict[str, Any]):
        if i == len(keys):
            grids.append(cur.copy())
            return
        for v in values[i]:
            cur[keys[i]] = v
            rec(i+1, cur)
    rec(0, {})
    return grids

# -----------------------------------------------------------
# Parameter & Defaults
# -----------------------------------------------------------

def default_params() -> Dict[str, Any]:
    return {
        "version": "tsm-gr-v0.2",
        "alpha": 1.0,
        "lambda_": 1.0,
        "delta": 0.1,
        "gamma0": 0.0,
        "gamma1": 1.0,

        "B_hi": 0.8,
        "S_lo": 0.3,
        "eps_phi": 0.087266,  # ~5°
        "hK": 0.02,
        "N_dwell": 3,

        "dtau": 0.1,
        "steps": 300,
        "seed": 0,

        "omega_phi": 0.0,
        "mode": "potential",  # oder "residual"

        # Potential-Modus
        "kappa": 1.0,
        "x_star": [0.0, 0.0, 0.0],

        # Residual-Modus
        "a_tau": 0.0,
        "xi_sigma": 1.0,
        "xi_center": [0.0, 0.0, 0.0],
        "xi_k": [0.5, 0.0, 0.0],
        "xi_omega": 0.2,

        # numerik
        "fd_h": 0.001,
    }


# -----------------------------------------------------------
# Dynamik / Modellgleichungen (vereinfachtes Feldmodell)
# -----------------------------------------------------------
@dataclass
class State:
    tau: float
    x: Tuple[float, float, float]
    v: Tuple[float, float, float]
    eps: float
    phi: float


def potential_energy(x: Tuple[float, float, float], x_star: Tuple[float, float, float], kappa: float) -> float:
    dx = (x[0]-x_star[0], x[1]-x_star[1], x[2]-x_star[2])
    return 0.5 * kappa * (dx[0]*dx[0] + dx[1]*dx[1] + dx[2]*dx[2])


def grad_potential(x: Tuple[float, float, float], x_star: Tuple[float, float, float], kappa: float) -> Tuple[float, float, float]:
    return (kappa*(x[0]-x_star[0]), kappa*(x[1]-x_star[1]), kappa*(x[2]-x_star[2]))


def K_potential(x: Tuple[float, float, float], phi: float, params: Dict[str, Any]) -> float:
    # χ = -U(x) - η_phase(1-cos φ)  → hier η_phase := delta (Wiederverwendung des Symbols)
    U = potential_energy(x, tuple(params.get("x_star", [0.0,0.0,0.0])), float(params.get("kappa", 1.0)))
    eta_phase = float(params.get("delta", 0.1))
    chi = -U - eta_phase * (1.0 - math.cos(phi))
    z = float(params.get("gamma0", 0.0)) + float(params.get("gamma1", 1.0)) * chi
    return sigmoid(z)


def Xi_field(x: Tuple[float,float,float], phi: float, tau: float, params: Dict[str, Any]) -> float:
    # gauss. Feld + leichte Rotation über φ (residual mode)
    xc = tuple(params.get("xi_center", [0.0,0.0,0.0]))
    sig = float(params.get("xi_sigma", 1.0))
    kx, ky, kz = tuple(params.get("xi_k", [0.5, 0.0, 0.0]))
    om = float(params.get("xi_omega", 0.2))
    dx = (x[0]-xc[0], x[1]-xc[1], x[2]-xc[2])
    r2 = dx[0]*dx[0] + dx[1]*dx[1] + dx[2]*dx[2]
    base = math.exp(-0.5*r2/(sig*sig))
    osc = math.cos(kx*x[0] + ky*x[1] + kz*x[2] + om*phi)
    return base * osc


def K_residual(x: Tuple[float,float,float], phi: float, tau: float, params: Dict[str, Any]) -> float:
    # R = ∂τΞ + Aτ Ξ ≈ finite diff + Drift a_tau
    h = float(params.get("fd_h", 0.001))
    a_tau = float(params.get("a_tau", 0.0))
    Xi0 = Xi_field(x, phi, tau, params)
    Xi1 = Xi_field(x, phi, tau+h, params)
    dXi = (Xi1 - Xi0) / h
    R = dXi + a_tau * Xi0
    z = float(params.get("gamma0", 0.0)) - float(params.get("gamma1", 1.0)) * (R*R)
    return sigmoid(z)


def K_value(x: Tuple[float,float,float], phi: float, tau: float, params: Dict[str, Any]) -> float:
    mode = str(params.get("mode", "potential"))
    if mode == "residual":
        return K_residual(x, phi, tau, params)
    return K_potential(x, phi, params)


# -----------------------------------------------------------
# Zonenlogik mit Hysterese & Dwell
# -----------------------------------------------------------
ZONES = ["F+", "F", "R↑", "R↓", "K", "K+", "U"]

@dataclass
class ZoneState:
    zone: str
    dwell: int


def zone_update(prev: ZoneState, K: float, eps: float, phi: float, params: Dict[str, Any]) -> ZoneState:
    B_hi = float(params.get("B_hi", 0.8))
    S_lo = float(params.get("S_lo", 0.3))
    hK   = float(params.get("hK", 0.02))
    N_dw = int(params.get("N_dwell", 3))

    # Hysterese-Bänder
    B1 = clamp(B_hi - hK, 0.0, 1.0)
    S1 = clamp(S_lo + hK, 0.0, 1.0)

    # Priorität: K+ > F+ > K > F > R↑ > R↓ > U (Beispielordnung)
    z = prev.zone

    # Guards
    if K >= (B1 + hK):
        z_new = "K+"
    elif K >= B1:
        z_new = "K"
    elif K >= 0.5*(B1+S1):
        z_new = "F+"
    elif K >= S1:
        z_new = "F"
    elif eps > float(params.get("eps_phi", 0.087266)) and math.sin(phi) >= 0.0:
        z_new = "R↑"
    elif eps > float(params.get("eps_phi", 0.087266)):
        z_new = "R↓"
    else:
        z_new = "U"

    # Dwell: nur wechseln, wenn N_dw erfüllt
    if z_new != z:
        if prev.dwell+1 >= N_dw:
            return ZoneState(z_new, 0)
        else:
            return ZoneState(z, prev.dwell+1)
    return ZoneState(z, min(prev.dwell+1, N_dw))


# -----------------------------------------------------------
# Integrator (einfacher expliziter Schritt in τ)
# -----------------------------------------------------------

def step(state: State, params: Dict[str, Any]) -> State:
    dt = float(params.get("dtau", 0.1))
    alpha = float(params.get("alpha", 1.0))
    lam = float(params.get("lambda_", 1.0))
    om = float(params.get("omega_phi", 0.0))

    K = K_value(state.x, state.phi, state.tau, params)

    # effektive Geodäsie entlang -∇U (Potential) oder -∇K (Residual approximiert)
    if str(params.get("mode", "potential")) == "potential":
        gx, gy, gz = grad_potential(state.x, tuple(params.get("x_star", [0.0,0.0,0.0])), float(params.get("kappa", 1.0)))
    else:
        # numerischer Grad von K in Raumkoordinaten (Zentraldifferenzen)
        h = float(params.get("fd_h", 0.001))
        x0 = state.x
        def Kx(dx: Tuple[float,float,float]) -> float:
            xx = (x0[0]+dx[0], x0[1]+dx[1], x0[2]+dx[2])
            return K_value(xx, state.phi, state.tau, params)
        gx = (Kx((h,0,0)) - Kx((-h,0,0))) / (2*h)
        gy = (Kx((0,h,0)) - Kx((0,-h,0))) / (2*h)
        gz = (Kx((0,0,h)) - Kx((0,0,-h))) / (2*h)

    # Bewegung: x' = v, v' = -alpha * grad, eps' = -lambda * K * eps, phi' = om
    vx = state.v[0] - alpha * gx * dt
    vy = state.v[1] - alpha * gy * dt
    vz = state.v[2] - alpha * gz * dt

    x = (state.x[0] + vx * dt, state.x[1] + vy * dt, state.x[2] + vz * dt)

    eps = max(0.0, state.eps - lam * K * state.eps * dt)
    phi = (state.phi + om * dt) % (2*math.pi)

    return State(state.tau + dt, x, (vx,vy,vz), eps, phi)


# -----------------------------------------------------------
# Simulation / Run
# -----------------------------------------------------------

def simulate(params: Dict[str, Any]) -> Dict[str, Any]:
    steps = int(params.get("steps", 300))
    random.seed(int(params.get("seed", 0)))

    st = State(
        tau=0.0,
        x=(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)),
        v=(0.0, 0.0, 0.0),
        eps=1.0,
        phi=0.0,
    )

    zone = ZoneState("U", 0)

    traj: List[Dict[str, Any]] = []
    zones: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []

    tt_null: Optional[float] = None
    transitions = 0

    for i in range(steps):
        K = K_value(st.x, st.phi, st.tau, params)
        zn_prev = zone.zone
        zone = zone_update(zone, K, st.eps, st.phi, params)
        if zone.zone != zn_prev:
            transitions += 1

        row = {
            "tau": st.tau,
            "x0": st.x[0], "x1": st.x[1], "x2": st.x[2],
            "v0": st.v[0], "v1": st.v[1], "v2": st.v[2],
            "eps": st.eps,
            "phi": st.phi,
            "K": K,
            "zone": zone.zone,
            "dwell": zone.dwell,
        }
        traj.append(row)
        zones.append({"tau": st.tau, "zone": zone.zone, "dwell": zone.dwell})

        logs.append({
            "step": i,
            "tau": st.tau,
            "K": K,
            "zone": zone.zone,
            "eps": st.eps,
        })

        if tt_null is None and abs(math.sin(st.phi)) < 1e-6:
            tt_null = st.tau

        st = step(st, params)

    # Kennzahlen
    def pct(name: str) -> float:
        n = len(traj)
        if n == 0:
            return 0.0
        return sum(1 for r in traj if r.get("zone") == name) / n

    metrics = {
        "tt_null": tt_null if tt_null is not None else float('nan'),
        "pct_F+": pct("F+"),
        "pct_F": pct("F"),
        "transitions": transitions,
        "eps_increase_steps": sum(1 for i in range(1,len(traj)) if traj[i]["eps"] > traj[i-1]["eps"]),
    }

    return {
        "trajectory": traj,
        "zones": zones,
        "logs": logs,
        "metrics": metrics,
        "params": params,
    }


# -----------------------------------------------------------
# I/O und Sweeps
# -----------------------------------------------------------

def save_run(out_dir: Path, res: Dict[str, Any]) -> None:
    ensure_dir(out_dir)
    write_csv(out_dir/"trajectory.csv", res["trajectory"])
    write_csv(out_dir/"zones.csv", res["zones"])
    write_jsonl(out_dir/"run.log.jsonl", res["logs"])
    with open(out_dir/"metrics.json", 'w', encoding='utf-8') as f:
        json.dump(res["metrics"], f, indent=2)
    with open(out_dir/"params.snapshot.json", 'w', encoding='utf-8') as f:
        json.dump(res["params"], f, indent=2)


def load_overrides(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_params(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    out = base.copy()
    for k, v in over.items():
        key = "lambda_" if k == "lambda" else k
        out[key] = v
    return out


def cmd_run(args: argparse.Namespace) -> None:
    base = default_params()
    over = {}
    if args.params and Path(args.params).exists():
        over = load_overrides(Path(args.params))
    params = merge_params(base, over)

    res = simulate(params)
    save_run(Path(args.out), res)
    print(f"OK – results in {args.out}")


def built_in_grids() -> Dict[str, Dict[str, List[Any]]]:
    return {
        "potential": {
            "mode": ["potential"],
            "alpha": [0.5, 1.0, 2.0],
            "lambda_": [0.5, 1.0, 2.0],
            "gamma1": [0.5, 1.0, 2.0],
            "dtau": [0.05],
            "steps": [300],
        },
        "residual": {
            "mode": ["residual"],
            "a_tau": [0.0, 0.2],
            "xi_sigma": [0.8, 1.2],
            "xi_omega": [0.0, 0.2],
            "alpha": [0.5, 1.0],
            "lambda_": [0.5, 1.0],
            "dtau": [0.05],
            "steps": [300],
        }
    }


def load_grid(path: Optional[Path]) -> Dict[str, Dict[str, List[Any]]]:
    if path and path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return built_in_grids()


def cmd_sweep(args: argparse.Namespace) -> None:
    grid = load_grid(Path(args.grid) if args.grid else None)
    out_root = Path(args.out)
    ensure_dir(out_root)

    case_id = 0
    summary_rows: List[Dict[str, Any]] = []

    for name, spec in grid.items():
        cases = cartesian_grid(spec)
        sw_dir = out_root / f"{name}"
        ensure_dir(sw_dir)
        for c in cases:
            case_id += 1
            params = merge_params(default_params(), c)
            res = simulate(params)
            # save
            run_dir = sw_dir / f"case_{case_id:04d}"
            save_run(run_dir, res)
            m = res["metrics"].copy()
            m["case"] = case_id
            # Zusatz: packe die variierten Felder mit in summary
            for k,v in c.items():
                m[k] = v
            summary_rows.append(m)

        # Schreibe pro Sweep einen Summary‑CSV
        write_csv(sw_dir/"sweep_summary.csv", summary_rows)
        summary_rows.clear()

    print(f"OK – sweeps in {out_root}")


def cmd_taucheck(args: argparse.Namespace) -> None:
    # prüft qualitativ ähnliche Zonenfolgen bei τ‑Skalierung (λ‑Anpassung)
    base = default_params()
    scales = [0.5, 1.0, 2.0]
    rows: List[Dict[str, Any]] = []
    for a in scales:
        p = base.copy()
        p["dtau"] = base["dtau"] * a
        p["lambda_"] = base["lambda_"] / a
        res = simulate(p)
        rows.append({
            "scale": a,
            "pct_F+": res["metrics"]["pct_F+"],
            "pct_F": res["metrics"]["pct_F"],
            "transitions": res["metrics"]["transitions"],
        })
    ensure_dir(Path(args.out))
    write_csv(Path(args.out)/"taucheck.csv", rows)
    print(f"OK – taucheck in {args.out}")


def cmd_stabcheck(args: argparse.Namespace) -> None:
    base = default_params()
    rows: List[Dict[str, Any]] = []
    for dt in [0.2, 0.1, 0.05, 0.02]:
        p = base.copy()
        p["dtau"] = dt
        res = simulate(p)
        rows.append({
            "dtau": dt,
            "eps_increase_steps": res["metrics"]["eps_increase_steps"],
            "transitions": res["metrics"]["transitions"],
        })
    ensure_dir(Path(args.out))
    write_csv(Path(args.out)/"stabcheck.csv", rows)
    print(f"OK – stabcheck in {args.out}")


# -----------------------------------------------------------
# CLI
# -----------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="TSM–GR Runner v0.2")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("run", help="Einzellauf")
    p1.add_argument("--out", default="./out", help="Ausgabeverzeichnis")
    p1.add_argument("--params", default="params.json", help="Overrides JSON (optional)")

    p2 = sub.add_parser("sweep", help="Parameter‑Sweeps")
    p2.add_argument("--out", default="./out_sweeps", help="Ausgabewurzel")
    p2.add_argument("--grid", default="grid.json", help="Grid‑Spezifikation (optional)")

    p3 = sub.add_parser("taucheck", help="τ‑Reparametrisations‑Check")
    p3.add_argument("--out", default="./out_checks", help="Ausgabeverzeichnis")

    p4 = sub.add_parser("stabcheck", help="Stabilitäts‑Check")
    p4.add_argument("--out", default="./out_checks", help="Ausgabeverzeichnis")

    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    if args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "sweep":
        cmd_sweep(args)
    elif args.cmd == "taucheck":
        cmd_taucheck(args)
    elif args.cmd == "stabcheck":
        cmd_stabcheck(args)
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
