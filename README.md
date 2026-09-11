# Fitting_Code_Lab_3.0 (use claude code to improve the script)

Power-sweep fitting pipeline for superconducting coplanar-waveguide (CPW) resonators. Given raw VNA S21 sweeps at a series of drive powers, the code fits each sweep with the Diameter Correction Method (DCM), extracts $Q_i$, $Q_c$, $Q$, and $f_c$ vs. power/photon number, and fits the resulting $Q_i(\langle n \rangle)$ curve to the standard two-level-system (TLS) loss model.

This is an update of `Fitting_Code_Lab_2.0`, making the data handling more functional, DCM fitting is cited from CU Boulder Cryogenic Quantum Testbed's [`scresonators`](https://github.com/Boulder-Cryogenic-Quantum-Testbed/scresonators) library and do some improvement.

## Structure

```
Fitting_Code_Lab_3.0/
├── UserFile_Analyze_Wei_Ren.py   # main entry — edit paths/settings here and run
├── helper_scripts/
│   ├── helper_fit.py             # fitting pipeline: single-file fit, power sweep, TLS loss fit
│   ├── helper_misc.py            # filename/path parsing utilities
│   └── __init__.py
├── scresonators/                 
│   └── fit_resonator/
│       ├── resonator.py          # Resonator container, data loading, fit configuration
│       ├── fit.py                # core DCM fit routine
│       ├── cavity_functions.py   # DCM model function
│       └── plot.py               # per-resonance fit plot
├── example/                      # example VNA data (Ta a-plane sapphire resonators, T = 13/30/45 mK)
│   ├── T_13mK/
│   ├── T_30mK/
│   └── T_45mK/
├── MIT LICENSE
└── README.md
```

## What the pipeline does

For each resonator found under a data directory, `UserFile_Analyze_Wei_Ren.py` calls `helper_fit.power_sweep_fit_drv`, which:

1. **Fit each power point independently** to the DCM model (`fit_single_power_list` → `fit_single_res`), using Monte Carlo–refined least squares via `scresonators`.
2. **Compute $Q_i$, $Q_c$, $Q$, $f_c$** (with uncertainties) at every power, and converts applied power to average intracavity photon number $\langle n \rangle$ (`power_to_navg`, citing *Burnett, Jonathan, et al. "Noise and loss of superconducting aluminium resonators at single photon energies." Journal of Physics: Conference Series. Vol. 969. No. 1. IOP Publishing, 2018* Eq. 1).
3. **Fit the loss tangent** $1/Q_i$ vs. $\langle n \rangle$ to the TLS model
   $$\delta_{TLS} = F\delta^0_{TLS}\tanh\!\left(\frac{\hbar\omega_0}{2k_BT}\right)\left(1+\frac{\langle n \rangle}{n_c}\right)^{-\beta} + \frac{1}{Q_{HP}}$$
   via `fit_delta_tls`, either fixing $Q_{HP}$ to the highest-power measured $Q_i$ (`QHP_fix=True`) or leaving it free.
4. **Save results**: a per-resonator CSV (`qiqcfc_vs_power_<timestamp>.csv`) and five diagnostic plots in an `all_fit_plots/` subfolder — $f_c$, $Q_c$, $Q_i$, $Q_i$&$Q_c$, and loss tangent, each vs. power/photon number, with the TLS fit overlaid on the loss tangent plot.

## Input data format

- A top-level data directory, conventionally named `<line_num>-<sample_name>` (e.g. `Cooldown_76_Line6-Tony_Ta_r_plane_02`); `helper_misc.parse_sample_info` splits this into line number and sample name.
- Resonator folders anywhere underneath, named exactly `Resonator_<n>_<freq>GHz` (e.g. `Resonator_2_6p027GHz`) — found recursively (`find_resonator_dirs`), so they can sit directly under the data directory or be stored under temperature folders.
- Temperature is inferred from a `T_<value>mK` ancestor folder (`get_temperature_from_path`); if none is found, `default_temperature_mK` is used.
- One CSV per power point inside each resonator folder, filename containing frequency and power, e.g. `SampleName_6p027GHz_-60dBm_30mK.csv`. Power is parsed from the `<value>dBm` taken in the filename.
- CSV columns, no header: **frequency [Hz], magnitude [dB], phase [deg]**.

## Requirements

Python ≥ 3.9.:

```
lmfit, matplotlib, numpy, pandas, scipy, sympy, scikit-rf, uncertainties,
gitpython, attrs, inflect, pytest
```

Plus `regex`, used directly by `helper_misc.py`.

```bash
pip install -r scresonators/requirements.txt
pip install regex
```

## Usage

1. Open `UserFile_Analyze_Wei_Ren.py` and set, near the top:
   - `data_dir` — path to your cooldown's data folder (currently hardcoded to a personal path; update this before running).
   - `default_temperature_mK` — fallback temperature if no `T_<x>mK` folder is present.
   - `external_attenuation`, `internal_attenuation` — line attenuation in dB, used to convert VNA-applied power to power at the device for the photon-number conversion.
   - `TLS_FIT_CONFIGS` — per-sample-name dict of custom TLS fit initial guesses (`tls_fit_init`) and bounds (`tls_fit_bounds`); anything not listed falls back to `"default"`.
   - `init_conds` — optionally uncomment and set a manual DCM initial guess `[Q, Qc, f_c, phi]` for specific files where automatic fitting struggles.
2. Run:
   ```bash
   python UserFile_Analyze_Wei_Ren.py
   ```
3. The script walks every resonator folder it finds, fits every power point in it, prints per-power $\bar n$/$Q$/$Q_i$/$Q_c$/$f_c$ to the console, and writes the summary CSV + plots into that same resonator folder. A failure on one resonator (caught and traceback-printed) doesn't stop the rest of the run.

## Key options (`power_sweep_fit_drv` / `fit_single_res`)

| Parameter | Purpose |
|---|---|
| `preprocess_method` | `'circle'` (default, circle-fit normalization) or `'linear'` |
| `atten` | `[external_attenuation, internal_attenuation]` in dB, summed to convert VNA power to power at the device |
| `phi0` | Impedance-mismatch phase offset applied when computing $Q_i$ from $Q$, $Q_c$, $\phi$ |
| `QHP_fix` | Fix $Q_{HP}$ in the TLS fit to the highest measured $Q_i$ (needs ≥ 4 power points) |
| `loss_scale` | Display scale factor for the $Q_i^{-1}$ axis (e.g. `1e-6`) |
| `manual_init_list` | Per-file manual DCM initial guesses `[Q, Qc, f_c, phi]` |
| `save_dcm_plot`, `show_plots`, `plot_extra` | Control saving/showing of individual per-power DCM fit plots |
| `use_error_bars`, `show_dbm`, `plot_twinx` | Cosmetic options for the summary plots |

## Output

- `qiqcfc_vs_power_<YYMMDD_HH_MM_SS>.csv` in each resonator folder, columns: `Power [dBm], navg, fc [GHz], fc error, Qi, Qi error, Qc, Qc error, Q, Q error`.
- `all_fit_plots/` in each resonator folder:
  - `fc_vs_power_<freq>GHz_<T>mK_<date>.png`
  - `qc_vs_power_..._.png`
  - `qi_vs_power_..._.png`
  - `qiqc_vs_power_..._.png`
  - `tand_vs_power_..._.png` (loss tangent, with the TLS fit curve and fitted $F\delta^0_{TLS}$, $n_c$, $Q_{HP}$, $\beta$ annotated)

## Notes

- The TLS fit requires at least 4 valid power points per resonator; resonators with fewer are skipped with a console warning.
- Bad fits (non-finite or non-positive $Q_i$/$Q_c$) are marked `NaN` in the summary rather than dropped, so the CSV always has one row per input power file.
