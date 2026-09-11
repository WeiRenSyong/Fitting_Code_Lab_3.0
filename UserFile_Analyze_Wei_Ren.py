# %%
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR / "helper_scripts")) # custom module folder 1
sys.path.insert(0, str(BASE_DIR / "scresonators")) # custom module folder 2

import traceback

import helper_fit as hf
import helper_misc as hm
import matplotlib.pyplot as plt

print("helper_fit   ->", hf.__file__)
print("helper_misc  ->", hm.__file__)

# %%  Get sample name and device information
# Define data directory
data_dir = Path(r"C:\Users\user\OneDrive\Desktop\CU Boulder Life\博四上\Tony_Ta_acr_sapphire\Cooldown_76_Line6-Tony_Ta_r_plane_02\T_80mK")

# Safety check
if not data_dir.exists():
    raise FileNotFoundError(f"Data directory not found: {data_dir}")

line_num, sample_name = hm.parse_sample_info(data_dir)

# Debug print
print("=== Sample Info ===")
print(f"Data directory : {data_dir}")
print(f"Line number    : {line_num}")
print(f"Sample name    : {sample_name}")

# %% Find every resonator folder under the data directory
#
# Resonator folders may live directly under data_dir, under a single
# "most_recent_data" folder, under several temperature folders
# (e.g. "T_13mK", "T_30mK", "T_45mK"), or under any other nesting.
# find_resonator_dirs searches recursively so all of them get processed,
# and get_temperature_from_path infers each resonator's temperature from
# a "T_<value>mK" ancestor folder when present, falling back to
# default_temperature_mK otherwise.
default_temperature_mK = 15

chosen_resonators = hm.find_resonator_dirs(data_dir)

if not chosen_resonators:
    raise FileNotFoundError(f"No resonator folders found under: {data_dir}")

# Debug print
print("=== Resonator Folders ===")
print(f"Search root: {data_dir}")
print(f"Found {len(chosen_resonators)} resonators:")

for r in chosen_resonators:
    temp_mK = hm.get_temperature_from_path(r, default_mK=default_temperature_mK)
    print(f"  - {r.relative_to(data_dir)}  (T = {temp_mK} mK)")


# %% perform power sweep

TLS_FIT_CONFIGS = {
    "MQC_Ta_": {
        "tls_fit_init": [2.2e5, 1.0, 0.25],   # QHP_fix=True case
        "tls_fit_bounds": None,
    },
    "default": {
        "tls_fit_init": None,
        "tls_fit_bounds": None,
    }
}

tls_cfg = TLS_FIT_CONFIGS.get(sample_name, TLS_FIT_CONFIGS["default"])

external_attenuation = 0
internal_attenuation = -70

# manual_guess_res = [1640, 5830, 7.211780e9, -0.02] # [Q, Qc, f_c, phi]

for resonator_path in chosen_resonators:
    print("\n==============================")
    print(f"Processing resonator: {resonator_path.relative_to(data_dir)}")

    temperature_mK = hm.get_temperature_from_path(resonator_path, default_mK=default_temperature_mK)

    all_resonator_csvs_paths = sorted(
        [x for x in resonator_path.glob("*GHz*.csv") if "dBm" in x.name]
    )
    all_resonator_csvs_names = [x.name for x in all_resonator_csvs_paths]

    if len(all_resonator_csvs_paths) == 0:
        print(f"[WARNING] No valid CSV files found in {resonator_path}")
        continue

    all_powers = [hm.get_power_from_filename(fname) for fname in all_resonator_csvs_names]

    if len(all_resonator_csvs_paths) != len(all_powers):
        raise ValueError(f"Mismatch between CSV files and extracted powers in {resonator_path}")

    init_conds = [None] * len(all_resonator_csvs_paths)

    # for i, path in enumerate(all_resonator_csvs_paths):
    #     if "7p212GHz" in path.name:
    #         init_conds[i] = manual_guess_res

    save_fit_dirs = [str(resonator_path), str(resonator_path)]

    print(f"Temperature: {temperature_mK} mK")
    print(f"Number of files: {len(all_resonator_csvs_paths)}")
    for fname, pwr in zip(all_resonator_csvs_names, all_powers):
        print(f"  {fname} --> {pwr} dBm")

    try:
        hf.power_sweep_fit_drv(
            sample_name=sample_name,
            temperature=temperature_mK,
            powers_in=all_powers,
            all_paths=all_resonator_csvs_paths,
            atten=[external_attenuation, internal_attenuation],
            save_fit_dirs=save_fit_dirs,
            data_dir=resonator_path,

            plot_fit=True,
            plot_extra=False,
            save_dcm_plot=False,
            show_plots=False,

            use_error_bars=True,
            phi0=0.,
            loss_scale=1e-6,

            preprocess_method='circle',
            # preprocess_method=None,
            ds={'QHP': 1e5, 'nc': 1, 'Fdtls': 1e-4},
            plot_twinx=False,
            QHP_fix=True,   # Set QHP as the highest power Q first, which would make more accurate for S-curve fitting
            manual_init_list=init_conds,
            show_dbm=True,

            tls_fit_init=tls_cfg["tls_fit_init"],
            tls_fit_bounds=tls_cfg["tls_fit_bounds"],
        )
    except Exception as e:
        print(f"[ERROR] Failed on {resonator_path.name}: {e}")
        traceback.print_exc()
    finally:
        plt.close('all')

print(f'Analyzing is done.')
