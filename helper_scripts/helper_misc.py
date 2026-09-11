'''
    helper_misc.py
'''

from pathlib import Path
import regex as re

def check_and_make_dir(directory_name):
    """
    Create directory if it does not exist.
    Accepts str or Path. If a file-like path is passed, uses its parent folder.
    Returns the directory Path object.
    """
    path = Path(directory_name)

    # If user passed something like ".../file.csv", create the parent directory instead
    if path.suffix in ['.csv', '.pdf', '.png', '.txt']:
        path = path.parent

    if not path.exists():
        print(f'      target directory: {path}')
        print(f'      directory does not exist. now creating...')
        path.mkdir(parents=True, exist_ok=True)
    else:
        print(f'      directory already exists.')

    print(f'      absolute path: {path.resolve()}\n')
    return path
     
def get_power_from_filename(filename):
    """
    Extract power in dBm from filename.

    Supports patterns like:
    - 25dB   -> returns -25.0  (legacy behavior)
    - -25dBm -> returns -25.0
    - 25dBm  -> returns 25.0
    """
    filename = str(filename)

    # First try explicit dBm pattern
    match_dbm = re.search(r'(-?\d+(?:\.\d+)?)dBm', filename)
    if match_dbm:
        return float(match_dbm.group(1))

    # Fallback to legacy pattern like "25dB" meaning -25 dBm
    match_db = re.search(r'(\d{1,3}(?:\.\d+)?)dB', filename)
    if match_db:
        return -float(match_db.group(1))

    raise ValueError(f"Could not extract power from filename: {filename}")

RESONATOR_DIR_PATTERN = re.compile(r"Resonator_\d+_.*GHz")
TEMPERATURE_DIR_PATTERN = re.compile(r"T_(\d+(?:\.\d+)?)mK", re.IGNORECASE)


def parse_sample_info(data_dir):
    """
    Parse the line number and sample name out of a data directory name.

    Expected format: "<line_num>-<sample_name>", e.g.
    "Cooldown_72_Line5-Tony_Ta_a_plane_01" -> ("Cooldown_72_Line5", "Tony_Ta_a_plane_01").

    If the folder name has no "-" separator, line_num is returned as None and
    the whole folder name is used as sample_name.
    """
    name = Path(data_dir).name
    parts = re.split(r"-", name, maxsplit=1)

    if len(parts) == 2:
        return parts[0], parts[1]

    return None, name


def find_resonator_dirs(root_dir):
    """
    Recursively find every resonator folder under root_dir.

    A resonator folder is one whose name matches "Resonator_<n>_<freq>GHz".
    Searching recursively means root_dir can point at a top-level data
    directory that stores resonator folders directly, under a single
    "most_recent_data" folder, under multiple temperature folders
    (e.g. "T_13mK", "T_30mK", ...), or under any other nesting -- all of
    them are found and returned.
    """
    root_dir = Path(root_dir)
    return sorted(
        p for p in root_dir.rglob("*")
        if p.is_dir() and RESONATOR_DIR_PATTERN.fullmatch(p.name)
    )


def get_temperature_from_path(resonator_path, default_mK=None):
    """
    Infer the temperature (in mK) for a resonator folder from its ancestor
    folder names, looking for a pattern like "T_13mK" -> 13.0.

    Falls back to default_mK if no temperature folder is found in the path.
    Raises ValueError if no temperature folder is found and default_mK is None.
    """
    for part in Path(resonator_path).parts:
        match = TEMPERATURE_DIR_PATTERN.fullmatch(part)
        if match:
            return float(match.group(1))

    if default_mK is None:
        raise ValueError(
            f"Could not infer temperature from path: {resonator_path}, "
            "and no default_mK was provided."
        )

    return default_mK


def get_frequency_from_filename(filename):
    """
    Extract resonator frequency in GHz from filename.

    Example:
    - '_5p932GHz_' -> 5.932
    - '_12p3456GHz_' -> 12.3456
    """
    filename = str(filename)
    match = re.search(r'_(\d+)p(\d{1,6})GHz_', filename)

    if not match:
        raise ValueError(f"Could not extract frequency from filename: {filename}")

    whole = match.group(1)
    frac = match.group(2)
    return float(f"{whole}.{frac}")