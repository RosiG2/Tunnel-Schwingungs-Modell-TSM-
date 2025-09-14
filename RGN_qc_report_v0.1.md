# RGN QC Report v0.1
**Generated (UTC):** 2025-09-14T15:37:28.548474+00:00

**Rows:** 10004  
**Zone shares:**
- regulativ: 0.600000
- kohärent: 0.200000
- fragmentiert: 0.200000

## Per-zone (mean ± std)
| zone | K_mean | K_std | phi_mean | phi_std | F_mean | F_std | B_mean | S_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fragmentiert | 0.020502 | 0.020052 | 1.128558 | 0.267530 | 0.054492 | 0.015852 | 0.100050 | 0.900050 |
| kohärent | 0.324721 | 0.238556 | 0.225003 | 0.127906 | 0.870837 | 0.643491 | 0.900050 | 0.100050 |
| regulativ | 0.054757 | 0.055963 | 0.840479 | 0.349070 | 0.170676 | 0.068638 | 0.500050 | 0.500050 |

## Correlations (subset)
```json
{
  "K": {
    "K": 1.0,
    "varphi": -0.706057,
    "F_res": 0.873019,
    "B": 0.628162,
    "S": -0.628213
  },
  "varphi": {
    "K": -0.706057,
    "varphi": 1.0,
    "F_res": -0.591263,
    "B": -0.780104,
    "S": 0.780095
  },
  "F_res": {
    "K": 0.873019,
    "varphi": -0.591263,
    "F_res": 1.0,
    "B": 0.65326,
    "S": -0.653378
  },
  "B": {
    "K": 0.628162,
    "varphi": -0.780104,
    "F_res": 0.65326,
    "B": 1.0,
    "S": -0.999999
  },
  "S": {
    "K": -0.628213,
    "varphi": 0.780095,
    "F_res": -0.653378,
    "B": -0.999999,
    "S": 1.0
  }
}
```
## φ plateau indicator (top histogram peaks)
```json
{
  "top_peaks": [
    {
      "bin_center": 0.5789635,
      "count": 501
    },
    {
      "bin_center": 0.33003950000000004,
      "count": 500
    },
    {
      "bin_center": 0.8278875000000001,
      "count": 500
    }
  ],
  "bin_edges_sample": [
    0.05,
    1.91693
  ]
}
```
## Baseline vs Recommended
```json
{
  "n_compared": 10000,
  "agreement": 0.9999
}
```

## Plots
- RGN_qc_plots_v0.1/hist_K.png
- RGN_qc_plots_v0.1/hist_varphi.png
- RGN_qc_plots_v0.1/scatter_K_vs_varphi.png
- RGN_qc_plots_v0.1/scatter_F_vs_K.png
