# RGN Bundle v0.2 (TSM → ART Bridge)


This bundle accompanies the RGN-Minimalstandard v0.1 one-pager. It provides precomputed state and metadata to enable web-usable, zero-edit consumption by the model.


## Files
- `RGN_state_v0.2.csv` — Row-wise join of `TSM-136D_zonen_recommended.csv` and `TSM-136D_R_estimates.csv` with mapped columns:
- `K` (from `R_combo_norm`), `varphi` (=`dphi` in radians), `varphi_deg`, `tau_rgn` (=`tau`),
- pass-through: `F_res`, `F_cap`, `B`, `S`, `zone`, plus the original R columns.
- `RGN_manifest_v0.2.json` — Reproducibility metadata: input/output md5, sizes, mapping, zone shares, baseline↔recommended agreement, correlations.
- `RGN_report_v0.2.md` — Human-readable summary (per-zone means/std, corr matrix).
- `RGN_online_patch_v0.2.json` — Patch snippet to merge into `tsm-online-bundle_v1.20.json` under `manifest`, `pipelines`, and `aliases`.


## Placement
Option A (recommended): commit all files into your GitHub repo root (or `out_rgn/`) and add the patch content into `tsm-online-bundle_v1.20.json` (merge keys; no removals).
Option B: upload these four as part of the 20-file corpus (note: you have 1 slot left). If so, prefer the three core files and skip the patch.


## Integrity (md5)
See `RGN_manifest_v0.2.json` for the exact hashes.


## Next
Once uploaded (GitHub), tell me the URLs (raw file paths). I will fetch them directly for downstream steps (sensitivity scan for α₁ and the MM/QM cross-check).