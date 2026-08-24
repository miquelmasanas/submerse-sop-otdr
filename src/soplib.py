# ══════════════════════════════════════════════════════════════════════════════
#  soplib.py
#  SOP Telemetry Analysis Library
#  Blue / Ionian Sea Deployment
#
#  __description__ = "Clean analysis library for State of Polarization
#  telemetry from submarine cable optical transponders. Covers HDF5 I/O,
#  spherical geometry, signal processing, seismology, and plotting."
#  __author__       = "Miquel Masanas (v1)"
#  __author_email__ = "miquel.1.masanas@nokia.com"
#  __date_created__ = "March 2026"
# ══════════════════════════════════════════════════════════════════════════════

import os
import json
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from scipy.signal import welch, spectrogram, butter, filtfilt
from scipy.ndimage import uniform_filter1d
from geopy.distance import geodesic
from obspy.taup import TauPyModel
from typing import Dict, Tuple, Any, List, Optional
from scipy.signal import decimate
import plotly.graph_objects as go
from scipy import signal
from matplotlib.ticker import LogLocator
import seaborn as sns
from scipy.signal import butter, sosfiltfilt
import glob
from scipy.interpolate import interp1d
from scipy.signal import decimate

# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

TAUP_MODEL    = TauPyModel(model="iasp91")
PHASE_COLORS  = {
    "P":         "steelblue",
    "S":         "darkorange",
    "Surf_fast": "green",
    "Surf_slow": "limegreen",
}

from matplotlib.colors import LinearSegmentedColormap
colors = ["#FFFFFF", "#7A99FF","#5900FF", "#DBFF4A", "#FF0400"] # White, Blue, Deep Red
cmap_name = "white_blue_red"
# custom_cmap = LinearSegmentedColormap.from_list(cmap_name, colors)

stops = [
    ("#FFFFFF"),
    ("#D6E8FF"),  
    ("#6BA3E8"),
    ("#7A99FF"),
    ("#5900FF"),
    ("#DBFF4A"),
    ("#FFB347"),   # orange
    ("#FF6B35"),
    ("#FF0400"),
]
custom_cmap = LinearSegmentedColormap.from_list(cmap_name, stops)
# ══════════════════════════════════════════════════════════════════════════════
#  1. DATA I/O
# ══════════════════════════════════════════════════════════════════════════════

def hdf5_path_sop(hdf5_dir: str, date_str: str) -> str:
    return os.path.join(hdf5_dir, r"sops", f'ellalink_sops_{date_str}.h5')



def hdf5_path_phase(hdf5_dir: str, date_str: str) -> str:
    return os.path.join(hdf5_dir, r"phase", f'ellalink_phase_{date_str}.h5')


# ══════════════════════════════════════════════════════════════════════════════
#  LOADERS  (import these in your analysis notebooks)
# ══════════════════════════════════════════════════════════════════════════════

def print_hdf5_structure(path):
    """Print HDF5 group/dataset tree with shapes and attributes."""
    def visitor(name, obj):
        indent = '  ' * name.count('/')
        if isinstance(obj, h5py.Dataset):
            print(f"{indent}📊 {name.split('/')[-1]}: "
                  f"shape={obj.shape}, dtype={obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"{indent}📁 {name.split('/')[-1]}/")
        # Print attributes
        for k, v in obj.attrs.items():
            print(f"{indent}   • {k}: {v}")

    with h5py.File(path, 'r') as f:
        print(f"File: {os.path.basename(path)}\n")
        print("── Root attributes:")
        for k, v in f.attrs.items():
            print(f"   • {k}: {v}")
        print("\n── Structure:")
        f.visititems(visitor)

# def load_sops(hdf5_dir: str, start: str, end: str) -> dict:
#     """
#     Load SOP data for a date range.
#     Returns dict {repeater_index: DataFrame(S0, S1, S2, S3, UTC index)}.
#     Drop-in replacement for create_SOP_df_dict output.

#     Example
#     -------
#     sop = load_sops('/data/hdf5', '2025-01-01', '2025-01-31')
#     sop[40]['S1'].plot()
#     """
#     dates = pd.date_range(start, end, freq='D').strftime('%Y-%m-%d')
#     frames_per_repeater = {}

#     for date_str in dates:
#         path = hdf5_path_sop(hdf5_dir, date_str)
#         if not os.path.exists(path):
#             continue
#         with h5py.File(path, 'r') as f:
#             unix_ns   = f['timing/unix_ns'][:]
#             ts        = pd.to_datetime(unix_ns, unit='ns', utc=True)
#             dim_names = f['header'].attrs['dimensionNames'].split(',')
#             mag       = f['data/magnitudes'][:]

#             r_indices = sorted({int(n.split('_r')[1])
#                                  for n in dim_names if '_r' in n})
#             for r in r_indices:
#                 row = {s: mag[f'{s}_r{r:02d}'] for s in ['S0', 'S1', 'S2', 'S3']}
#                 frames_per_repeater.setdefault(r, []).append(
#                     pd.DataFrame(row, index=ts))

#     if not frames_per_repeater:
#         raise FileNotFoundError(
#             f"No SOP HDF5 files found in {hdf5_dir}/sops "
#             f"between {start} and {end}.")

#     return {r: pd.concat(frames).sort_index()
#             for r, frames in frames_per_repeater.items()}

def load_sops(hdf5_dir: str, start: str, end: str, suffix: str = "") -> dict:
    """
    Load SOP data for a date range with an optional suffix (e.g., "_derotated").
    """
    dates = pd.date_range(start, end, freq='D').strftime('%Y-%m-%d')
    frames_per_repeater = {}

    for date_str in dates:
        # Construct path manually or update hdf5_path_sop to handle suffixes
        # Assuming hdf5_path_sop returns ".../ellalink_sops_2025-01-20.h5"
        base_path = hdf5_path_sop(hdf5_dir, date_str)
        
        # Apply suffix if provided
        if suffix:
            path = base_path.replace(".h5", f"{suffix}.h5")
        else:
            path = base_path

        if not os.path.exists(path):
            print(f"Warning: File not found {path}")
            continue
            
        with h5py.File(path, 'r') as f:
            unix_ns   = f['timing/unix_ns'][:]
            ts        = pd.to_datetime(unix_ns, unit='ns', utc=True)
            dim_names = f['header'].attrs['dimensionNames'].split(',')
            mag       = f['data/magnitudes'][:]

            r_indices = sorted({int(n.split('_r')[1])
                                 for n in dim_names if '_r' in n})
            for r in r_indices:
                row = {s: mag[f'{s}_r{r:02d}'] for s in ['S0', 'S1', 'S2', 'S3']}
                frames_per_repeater.setdefault(r, []).append(
                    pd.DataFrame(row, index=ts))

    if not frames_per_repeater:
        raise FileNotFoundError(f"No SOP HDF5 files found in {hdf5_dir} with suffix '{suffix}'")

    return {r: pd.concat(frames).sort_index()
            for r, frames in frames_per_repeater.items()}


def load_phase(hdf5_dir: str, start: str, end: str) -> pd.DataFrame:
    """
    Load Phase data for a date range.
    Returns DataFrame(UTC index, columns=0..R-1 repeater index).

    Example
    -------
    phase = load_phase('/data/hdf5', '2025-01-01', '2025-01-31')
    phase[40].plot()
    """
    dates  = pd.date_range(start, end, freq='D').strftime('%Y-%m-%d')
    frames = []

    for date_str in dates:
        path = hdf5_path_phase(hdf5_dir, date_str)
        if not os.path.exists(path):
            continue
        with h5py.File(path, 'r') as f:
            unix_ns   = f['timing/unix_ns'][:]
            ts        = pd.to_datetime(unix_ns, unit='ns', utc=True)
            dim_names = f['header'].attrs['dimensionNames'].split(',')
            mag       = f['data/magnitudes'][:]
            n_rep     = len(dim_names)
            data      = {r: mag[f'phase_r{r:02d}'] for r in range(n_rep)}
            frames.append(pd.DataFrame(data, index=ts))

    if not frames:
        raise FileNotFoundError(
            f"No Phase HDF5 files found in {hdf5_dir}/phase "
            f"between {start} and {end}.")

    return pd.concat(frames).sort_index()

def load_sensor_mapping(config_path: str) -> dict:
    """
    Load sensor_mapping.json. Returns the full mapping dict.
    Raises FileNotFoundError with a helpful message if missing.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"sensor_mapping.json not found at {config_path}. "
            f"Copy sensor_mapping.json.example and fill in your deployment details.")
    with open(config_path, 'r') as f:
        return json.load(f)


def get_cable_specs(mapping: dict, link: str) -> dict:
    """Return CableSpecs entry for a given link name."""
    return mapping.get("CableSpecs", {}).get(link, {})


def load_OBS_h5_smart(file_path, **kwargs):
    """
    Loads a dataset from the 'waveforms' group that matches all provided criteria.
    Example: load_h5_smart(file, channel='CH1', station='SUB01')
    """
    with h5py.File(file_path, 'r') as f:
        wf_group = f['waveforms']
        
        for name in wf_group.keys():
            ds = wf_group[name]
            attrs = ds.attrs
            
            # Check if this dataset matches ALL provided keyword arguments
            # e.g., if kwargs is {'channel': 'CH1'}, it checks attrs['channel'] == 'CH1'
            if all(attrs.get(k) == v for k, v in kwargs.items()):
                data = ds[:]
                
                # Reconstruct time index
                start_ts = pd.to_datetime(attrs['starttime'], utc=True)
                delta = attrs['delta']
                time_index = start_ts + pd.to_timedelta(np.arange(len(data)) * delta, unit='s')
                channel = attrs.get('channel')
                station = attrs.get('station')
                return pd.Series(data, index=time_index, name="_".join([station,channel]))
        
        raise ValueError(f"No dataset found matching criteria: {kwargs}")

def load_all_OBS_h5_recursive(root_path: str, **kwargs):
    """
    Finds all .h5 files recursively and loads them into a list.
    
    Parameters
    ----------
    root_path : str, e.g., "data/2025/**"
    **kwargs  : filters for load_h5_smart (e.g., channel='CH1')
    """
    # Use recursive=True and the ** pattern
    files = glob.glob(root_path, recursive=True)
    
    all_waveforms = []
    
    for f_path in files:
        try:
            # Reusing the smart loader logic from before
            series = load_OBS_h5_smart(f_path, **kwargs)
            all_waveforms.append(series)
        except Exception as e:
            print(f"Skipping {f_path}: {e}")
            
    return all_waveforms



def bandpass_filter_sos(data: np.ndarray, lowcut: float, highcut: float, 
                        fs: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    # Ensure the frequencies are within the valid (0, 1) range for Nyquist
    low = lowcut / nyq
    high = highcut / nyq
    
    # Use 'sos' instead of 'ba'
    sos = butter(order, [low, high], btype='band', output='sos')
    
    # Use sosfiltfilt for zero-phase filtering
    return sosfiltfilt(sos, data)

def lowpass_filter_sos(data: np.ndarray, highcut: float, 
                        fs: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    # Ensure the frequencies are within the valid (0, 1) range for Nyquist
    high = highcut / nyq
    
    # Use 'sos' instead of 'ba'
    sos = butter(order, high, btype='low', output='sos')
    
    # Use sosfiltfilt for zero-phase filtering
    return sosfiltfilt(sos, data)


# ══════════════════════════════════════════════════════════════════════════════
#  2. SPHERICAL GEOMETRY
# ══════════════════════════════════════════════════════════════════════════════


def sop_angular_rate(S: np.ndarray, dt: float) -> np.ndarray:
    """
    Geodesic angular rate between consecutive SOP vectors on the Poincaré sphere.

    v1 = S[n], v2 = S[n+1], each a full 3D Stokes vector [S1, S2, S3].
    Works for both unit and non-unit vectors.

    Parameters
    ----------
    S  : (N, 3) array of Stokes vectors
    dt : sample interval in seconds

    Returns
    -------
    (N-1,) angular rate in rad/s
    """
    v1, v2    = S[:-1], S[1:]
    cross     = np.cross(v1, v2)
    norm      = np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1)
    sin_theta = np.linalg.norm(cross, axis=1) / norm
    cos_theta = np.clip((v1 * v2).sum(axis=1) / norm, -1.0, 1.0)
    return np.arctan2(sin_theta, cos_theta) / dt


def spherical_mean(vectors: np.ndarray, max_iter: int = 10,
                   tol: float = 1e-6) -> np.ndarray:
    """
    Fréchet mean on S² via iterative Riemannian gradient descent.

    Parameters
    ----------
    vectors  : (N, 3) array of unit vectors
    max_iter : maximum iterations
    tol      : convergence tolerance on tangent vector norm

    Returns
    -------
    (3,) unit vector — intrinsic mean on the sphere
    """
    mu = vectors.mean(axis=0)
    mu = mu / np.linalg.norm(mu)

    for _ in range(max_iter):
        dots     = np.clip(vectors @ mu, -1.0, 1.0)
        tangents = vectors - dots[:, np.newaxis] * mu
        norms    = np.linalg.norm(tangents, axis=1, keepdims=True)
        angles   = np.arccos(dots)
        safe_n   = np.where(norms < 1e-10, 1.0, norms)
        log_vecs = (angles[:, np.newaxis] / safe_n) * tangents
        log_vecs[norms[:, 0] < 1e-10] = 0.0

        mean_t = log_vecs.mean(axis=0)
        norm_t = np.linalg.norm(mean_t)
        if norm_t < tol:
            break
        mu = np.cos(norm_t) * mu + np.sin(norm_t) * (mean_t / norm_t)
        mu = mu / np.linalg.norm(mu)

    return mu


def rolling_spherical_mean_vectorized(S: np.ndarray, window_samples: int,
                                       max_iter: int = 10,
                                       tol: float = 1e-6,
                                       max_windows_bytes: int = 256 * 1024 * 1024,
                                       ) -> np.ndarray:
    """
    Fully vectorized rolling Fréchet mean on S².
    Processes windows in time chunks so the (chunk, W, 3) tensor stays bounded.

    Parameters
    ----------
    S                  : (N, 3) array of unit vectors, uniform sampling assumed
    window_samples     : integer window size in samples (centered)
    max_iter           : Fréchet iterations
    tol                : convergence tolerance
    max_windows_bytes  : cap for the rolling ``windows`` array (chunk × W × 3 × itemsize).
                         Lower this if you still hit MemoryError.

    Returns
    -------
    (N, 3) array of unit vectors — rolling spherical mean

    Memory note
    -----------
    Unchunked size would be N × W × 3 × itemsize. Long SOP series with a large
    ``derotation_window_duration_seconds`` can exceed RAM (multi‑GB). Chunking
    keeps peak memory ~``max_windows_bytes`` plus a small pad slice. Process
    repeaters sequentially, not in parallel.
    """
    N    = len(S)
    W    = window_samples
    half = W // 2
    item = np.dtype(S.dtype).itemsize
    # Bytes for (chunk, W, 3) windows tensor only
    row_bytes = max(W * 3 * item, 1)
    chunk_n = max(1, int(max_windows_bytes // row_bytes))
    chunk_n = min(chunk_n, N)

    S_pad = np.pad(S, ((half, half), (0, 0)), mode='edge')
    mu_out = np.empty((N, 3), dtype=S.dtype)

    def _frechet_on_windows(windows: np.ndarray) -> np.ndarray:
        """windows: (C, W, 3) -> (C, 3) unit vectors."""
        mu = windows.mean(axis=1)
        norms = np.linalg.norm(mu, axis=1, keepdims=True)
        mu = mu / np.where(norms < 1e-10, 1.0, norms)
        for _ in range(max_iter):
            dots = np.clip(np.einsum('cwj,cj->cw', windows, mu), -1.0, 1.0)
            tangents = windows - dots[:, :, np.newaxis] * mu[:, np.newaxis, :]
            t_norms = np.linalg.norm(tangents, axis=2, keepdims=True)
            angles = np.arccos(dots)[:, :, np.newaxis]
            safe_t = np.where(t_norms < 1e-10, 1.0, t_norms)
            log_vecs = (angles / safe_t) * tangents
            log_vecs[t_norms[:, :, 0] < 1e-10] = 0.0

            mean_t = log_vecs.mean(axis=1)
            t_norm = np.linalg.norm(mean_t, axis=1, keepdims=True)
            converged = t_norm[:, 0] < tol
            step = mean_t / np.where(t_norm < 1e-10, 1.0, t_norm)
            mu = np.cos(t_norm) * mu + np.sin(t_norm) * step
            mu = mu / np.linalg.norm(mu, axis=1, keepdims=True)
            if converged.all():
                break
        return mu

    c_start = 0
    while c_start < N:
        c_end = min(c_start + chunk_n, N)
        C = c_end - c_start
        sl = S_pad[c_start : c_end + W - 1]
        idx = np.arange(W)[np.newaxis, :] + np.arange(C)[:, np.newaxis]
        windows = sl[idx]
        mu_out[c_start:c_end] = _frechet_on_windows(windows)
        c_start = c_end

    return mu_out


def derotate_df(ID: int, df: pd.DataFrame,
                params: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Derotate SOP time series to remove slow polarization drift.
    Uses rolling Fréchet mean on S² instead of Euclidean rolling mean
    to correctly handle the non-Euclidean geometry of the Poincaré sphere.

    Parameters
    ----------
    ID     : repeater identifier (passed through)
    df     : DataFrame with S1, S2, S3, S0 columns, UTC DatetimeIndex
    params : dict with key 'derotation_window_duration_seconds'

    Returns
    -------
    residual_df : DataFrame(S1, S2, S3, S0) — fast dynamics, mean mapped to north pole
    drift_df    : DataFrame(S1, S2, S3)     — slow Fréchet mean trajectory (tidal/thermal)
    """
    window_size_s  = params["derotation_window_duration_seconds"]
    S_vec          = df[['S1', 'S2', 'S3']].to_numpy(dtype=np.float32)
    dt             = get_dt(df)
    window_samples = max(1, int(window_size_s / dt))
    # using float32 to save memory, as I found memory limitations even in a very good machine
    M_vec          = rolling_spherical_mean_vectorized(S_vec, window_samples)

    x, y, z  = M_vec[:, 0], M_vec[:, 1], M_vec[:, 2]
    denom    = x**2 + y**2
    small    = denom < 1e-6
    safe_d   = np.where(small, 1.0, denom)
    N        = len(df)
    R        = np.zeros((N, 3, 3),dtype=np.float32)

    R[:, 0, 0] = (y**2 + z * x**2) / safe_d
    R[:, 0, 1] = x * y * (z - 1)   / safe_d
    R[:, 0, 2] = -x
    R[:, 1, 0] = x * y * (z - 1)   / safe_d
    R[:, 1, 1] = (x**2 + z * y**2) / safe_d
    R[:, 1, 2] = -y
    R[:, 2, 0] = x
    R[:, 2, 1] = y
    R[:, 2, 2] = z
    R[small]   = np.eye(3,dtype=np.float32)

    rotated     = np.matmul(R, S_vec[:, :, np.newaxis]).squeeze()
    residual_df = pd.DataFrame(rotated, columns=['S1', 'S2', 'S3'], index=df.index)
    # residual_df['S0'] = df['S0'].values

    drift_df = pd.DataFrame(M_vec, columns=['S1', 'S2', 'S3'], index=df.index)
    # drift_df['S0'] = df['S0'].values

    return residual_df, drift_df

def sop_angular_rate(S: np.ndarray, dt: float) -> np.ndarray:
    """
    Geodesic angular rate between consecutive SOP unit vectors on S².
    Uses arctan2(|S_{n+1} × S_n|, S_{n+1}·S_n) for full [0,π] range
    without singularities — robust for large polarization swings.

    Parameters
    ----------
    S  : (N, 3) array of unit vectors (already normalized, DOP=1)
    dt : sample interval in seconds

    Returns
    -------
    (N-1,) array of angular rates in rad/s
    """
    S1, S2   = S[:-1], S[1:]
    cross    = np.cross(S1, S2)
    sin_t    = np.linalg.norm(cross, axis=1)

    cos_t    = np.clip(np.einsum('ij,ij->i', S1, S2), -1.0, 1.0)
    return np.arctan2(sin_t, cos_t) / dt


def sop_angular_rate_signed(S: np.ndarray, dt: float, ref_axis=np.array([0, 0, 1])) -> np.ndarray:
    """
    Computes signed angular rate by projecting the rotation onto a reference axis.
    """
    S1, S2 = S[:-1], S[1:]
    cross  = np.cross(S1, S2)
    
    # Magnitude of the rotation (unsigned)
    sin_t = np.linalg.norm(cross, axis=1)
    cos_t = np.clip(np.einsum('ij,ij->i', S1, S2), -1.0, 1.0)
    theta = np.arctan2(sin_t, cos_t)

    # Determine sign: project cross product onto the reference axis
    # If the rotation 'swings' toward the ref_axis, it's positive.
    sign = np.sign(np.dot(cross, ref_axis))
    
    return (sign * theta) / dt

# ══════════════════════════════════════════════════════════════════════════════
#  3. SIGNAL PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def get_dt(df: pd.DataFrame) -> float:
    """Return median sample interval in seconds from a DatetimeIndex DataFrame."""
    return pd.Series(df.index).diff().median().total_seconds()


def bandpass_filter(data: np.ndarray, lowcut: float, highcut: float,
                    fs: float, order: int = 5) -> np.ndarray:
    """
    Zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    data   : 1D signal array
    lowcut : lower cutoff frequency in Hz
    highcut: upper cutoff frequency in Hz
    fs     : sampling frequency in Hz
    order  : filter order

    Returns
    -------
    Filtered signal, same shape as input
    """
    nyq  = 0.5 * fs
    low  = lowcut  / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)


def psd_db(x: np.ndarray, fs: float, nperseg: Optional[int] = None,
           noverlap: Optional[int] = None,
           smooth_size: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """
    Welch PSD in dB/Hz with optional log-space smoothing.

    Parameters
    ----------
    x           : 1D signal
    fs          : sampling frequency in Hz
    nperseg     : Welch segment length (default: min(N, 1 day of samples))
    noverlap    : overlap samples (default: 50% of nperseg)
    smooth_size : uniform filter size in log space (0 = no smoothing)

    Returns
    -------
    freqs : frequency array (Hz)
    psd   : power spectral density (dB/Hz)
    """
    nperseg  = nperseg  or min(len(x), int(fs * 86400))
    noverlap = noverlap or nperseg // 2
    f, p     = welch(x, fs=fs, nperseg=nperseg, noverlap=noverlap,
                     scaling='density')
    p_db = 10 * np.log10(np.maximum(p, 1e-30))
    if smooth_size > 1:
        p_db = uniform_filter1d(p_db, size=smooth_size)
    return f, p_db



def calculate_fs(timestamps):
    # Your robust fs calculation remains necessary
    try:
        if not isinstance(timestamps, pd.Series):
            timestamps = pd.Series(timestamps)
            
        time_diff_seconds = timestamps.diff().dt.total_seconds().dropna()
        
        if time_diff_seconds.empty:
            print("Cannot calculate fs: Need at least two timestamps.")
            return None
            
        fs = 1.0 / time_diff_seconds.median()
        return fs
    except AttributeError:
        print("Timestamps must be a pandas Series or list of datetime objects.")
    return None
    
def generateSpectrogram_scipy(sig, timestamps, windowSize, freqSpan, overlapPercentage=0.85,nfft_size = 2**13):
    
    fs = calculate_fs(timestamps)
    if fs is None:
        return None, None, None
        
    noverlap = int(windowSize * overlapPercentage)
    
    # Use the SciPy function for calculation
    # Pxx: spectrogram matrix, freqs: frequency axis, bins: time axis
    freqs, bins, Pxx = signal.spectrogram(
        x=sig, 
        fs=fs, 
        nperseg=windowSize, 
        noverlap=noverlap, 
        nfft = nfft_size,
        scaling='spectrum', # Use 'spectrum' for magnitude-squared
        mode='magnitude'    # Output magnitude (like your original FFT output)
    )

    # Convert magnitude to dB
    spectrogramData = Pxx + 1e-10
    
    # Pxx is (Freqs x Time), so transpose it to (Time x Freqs) for consistency 
    # with your original custom code output format.
    spectrogramData = spectrogramData.T
    
    # ----------------------------------------------------------------------
    # from the start, not DATETIME objects.
    # We must convert them back to DATETIME objects using the signal's start time.
    start_time = timestamps[0]
    timeAxis = pd.Series(start_time + pd.to_timedelta(bins, unit='s'))
    # ----------------------------------------------------------------------
    
    # ----------------------------------------------------------------------
    freq_mask = (freqs >= freqSpan[0]) & (freqs <= freqSpan[1])
    frequencyAxis = freqs[freq_mask]
    spectrogramData = spectrogramData[:, freq_mask] # Trim the data matrix
    # ----------------------------------------------------------------------
    
    # Return (Time x Freq) data and the trimmed axes
    return spectrogramData, timeAxis, frequencyAxis


def normalize_to_poincare(df: pd.DataFrame,
                           components: List[str] = ['S1', 'S2', 'S3']
                           ) -> pd.DataFrame:
    """
    Normalize Stokes vector to unit sphere (DOP = 1) using the L2 norm.
    Does not use the coherency matrix — simple geometric normalization.

    Parameters
    ----------
    df         : DataFrame with S1, S2, S3 columns
    components : list of column names to normalize

    Returns
    -------
    DataFrame with normalized components (in-place copy)
    """
    
    return df[components].div(np.sqrt(df[components].pow(2).sum(axis=1)))



# ══════════════════════════════════════════════════════════════════════════════
#  4. SEISMOLOGY
# ══════════════════════════════════════════════════════════════════════════════

def get_arrivals(distance_km: float, depth_km: float) -> Dict[str, float]:
    """
    Compute seismic wave arrival times in seconds from event origin.
    Body waves (P, S) from TauPy iasp91 model.
    Surface waves estimated from empirical velocity bounds.

    Parameters
    ----------
    distance_km : epicentral distance in km
    depth_km    : source depth in km

    Returns
    -------
    dict {phase_name: travel_time_seconds}
    """
    distance_deg = distance_km / 111.19
    result = {}

    try:
        taup = TAUP_MODEL.get_travel_times(
            source_depth_in_km=depth_km,
            distance_in_degree=distance_deg,
            phase_list=["P", "S"]
        )
        for arr in taup:
            if arr.name not in result:
                result[arr.name] = arr.time
    except Exception as e:
        print(f"TauPy error at {distance_km:.0f} km, depth {depth_km:.0f} km: {e}")

    # Surface wave window — empirical bounds
    # Fast Rayleigh ~3.9 km/s (short period, hard seafloor)
    # Slow Rayleigh ~3.0 km/s (long period, sedimentary paths)
    result["Surf_fast"] = distance_km / 3.9
    result["Surf_slow"] = distance_km / 3.0

    return result


def load_catalogue(file_path: str) -> List[dict]:
    """
    Load earthquake catalogue from USGS/EMSC/NOA CSV format.
    Expected columns: time, mag, place, latitude, longitude, depth.

    Parameters
    ----------
    file_path : path to CSV file

    Returns
    -------
    list of dicts with keys: id, timestamp, magnitude, location,
                              latitude, longitude, depth
    """
    required = ['time', 'mag', 'place', 'latitude', 'longitude', 'depth']
    df = pd.read_csv(file_path)

    if not all(col in df.columns for col in required):
        raise ValueError(f"Catalogue CSV must contain: {required}")

    df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
    df.dropna(subset=required, inplace=True)
    catalogue= [
        {
            'id':          i + 1,
            'timestamp':   row['time'],
            'magnitude':   row['mag'],
            'location':    row['place'],
            'latitude':    row['latitude'],
            'longitude':   row['longitude'],
            'depth':       row['depth'],
        }
        for i, (_, row) in enumerate(df.iterrows())
    ]
    catalogue = pd.DataFrame(catalogue)
    catalogue = catalogue.set_index("timestamp").sort_index()

    return catalogue


def filter_catalogue(df: pd.DataFrame, mag_min: float,
                     t_start: Optional[pd.Timestamp] = None,
                     t_end:   Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Filter the catalogue DataFrame using vectorized Pandas operations.
    """
    # 1. Filter by magnitude
    mask = df['magnitude'] >= mag_min
    
    # 2. Filter by time (using the index)
    if t_start:
        mask &= (df.index >= t_start)
    if t_end:
        mask &= (df.index <= t_end)
        
    return df.loc[mask]


def haversine_km(lat1: float, lon1: float,
                 lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two (lat, lon) points."""
    import math
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════════════════════
#  5. PLOTTING
# ══════════════════════════════════════════════════════════════════════════════

def add_event_lines(ax: plt.Axes, df_cat: pd.DataFrame,
                    mag_min: float = 3.5,
                    y_label: bool = True) -> None:
    
    # Use the new filtered DataFrame
    events = filter_catalogue(df_cat, mag_min)
    ymin, ymax = ax.get_ylim()

    # itertuples() returns an object where 'Index' is your timestamp
    for ev in events.itertuples():
        t = ev.Index  # This is the timestamp index
        ax.axvline(t, color='red', linewidth=0.8, linestyle='--', alpha=0.7)

        if y_label:
            # Access 'magnitude' column directly
            ax.text(t, ymax * 0.95, f"M{ev.magnitude}\n{ev.location}",
                    color='red', fontsize=8, rotation=90,
                    va='top', ha='right')
            
            

def plot_poincare_plotly(df: pd.DataFrame, title: str = "SOP Trajectory") -> go.Figure:
    """
    Generates an interactive Poincaré sphere plot from a DataFrame.
    Expects columns 'S1', 'S2', 'S3'.
    """
    # 1. Normalize the data to the unit sphere
    vals = df[['S1', 'S2', 'S3']].values
    norms = np.linalg.norm(vals, axis=1, keepdims=True)
    # Avoid division by zero
    normed = vals / np.where(norms == 0, 1, norms)
    # normed = vals

    scale = 1

    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 50)
    x = scale * np.outer(np.cos(u), np.sin(v))
    y = scale * np.outer(np.sin(u), np.sin(v))
    z = scale * np.outer(np.ones(np.size(u)), np.cos(v))
    sphere = go.Mesh3d(x=x.flatten(), y=y.flatten(), z=z.flatten(), color='blue', opacity=0.3, alphahull=0, showlegend=False) 

    meridian_lines = []
    for phi in np.linspace(0, 2 * np.pi, 24):  # Increase density
            x_meridian = scale * np.cos(phi) * np.sin(v)
            y_meridian = scale * np.sin(phi) * np.sin(v)
            z_meridian = scale * np.cos(v)
            meridian_lines.append(go.Scatter3d(x=x_meridian, y=y_meridian, z=z_meridian, mode='lines', line=dict(color='gray', width=1), showlegend=False))
    
    for theta in np.linspace(0, np.pi, 13):  # Increase density
            x_latitude = scale * np.cos(u) * np.sin(theta)
            y_latitude = scale * np.sin(u) * np.sin(theta)
            z_latitude = scale * np.ones(len(u)) * np.cos(theta)
            meridian_lines.append(go.Scatter3d(x=x_latitude, y=y_latitude, z=z_latitude, mode='lines', line=dict(color='gray', width=1), showlegend=False))
    
    
    # sphere = [sphere] + meridian_lines
    
    # 3. Create the SOP trajectory trace
    # Using a colorscale to represent time progression automatically
    trajectory = go.Scatter3d(
        x=normed[:, 0], y=normed[:, 1], z=normed[:, 2],
        mode='lines+markers',
        name='SOP',
        line=dict(color='rgba(100,100,100,0.3)', width=2),
        marker=dict(
            size=3,
            color=np.arange(len(normed)), # Color by index (time)
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Samples", thickness=15, x=0.9)
        )
    )
    
    # 4. Assemble and style
    fig = go.Figure(data=[sphere, trajectory] + meridian_lines)
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(title='S1', range=[-1.1, 1.1]),
            yaxis=dict(title='S2', range=[-1.1, 1.1]),
            zaxis=dict(title='S3', range=[-1.1, 1.1]),
            aspectmode='cube'
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=600
    )
    
    return fig

# Default colormap

SOP_CMAP = LinearSegmentedColormap.from_list(
    "sop_activity",
    ["#FFFFFF", "#7A99FF", "#5900FF", "#DBFF4A", "#FF0400"]
)


def plot_repeater_colormap(data_dict: dict,
                           quantity: str = None,
                           title: str = "SOP Activity",
                           cbar_label: str = "",
                           downsample: int = 10,
                           cmap=None,
                           noise_floor_percentile: float = 50,
                           clip_percentile: float = 96,
                           db_scale: bool = False,
                           catalogue: Optional[pd.DataFrame] = None,
                           mag_min: float = 3.5,
                           ax: Optional[plt.Axes] = None) -> plt.Axes:
    """
    Colorplot of any per-repeater time series across all repeaters.

    Parameters
    ----------
    data_dict   : dict {repeater_id: DataFrame or Series}
                  If DataFrame, `quantity` must specify which column to plot.
                  If Series, `quantity` is ignored.
    quantity    : column name to extract from DataFrame values
    title       : plot title
    cbar_label  : colorbar label
    downsample  : time axis downsampling factor
    cmap        : colormap (defaults to SOP_CMAP)
    noise_floor_percentile : percentile for vmin (default 50 = median)
    clip_percentile        : percentile for vmax (default 96)
    db_scale    : if True apply 10*log10 before plotting
    catalogue   : event catalogue DataFrame for annotation (optional)
    mag_min     : magnitude threshold for event lines
    ax          : existing Axes (creates new figure if None)

    Returns
    -------
    matplotlib Axes
    """
    from matplotlib.colors import LinearSegmentedColormap

    cmap = cmap or SOP_CMAP

    repeater_ids = sorted(data_dict.keys())
    ref_time     = (data_dict[repeater_ids[0]].index
                    if hasattr(data_dict[repeater_ids[0]], 'index')
                    else data_dict[repeater_ids[0]].index)

    # Build matrix
    matrix = np.zeros((len(repeater_ids), len(ref_time)))
    for i, key in enumerate(repeater_ids):
        obj = data_dict[key]
        series = obj[quantity] if quantity else obj
        matrix[i, :] = series.reindex(ref_time, method='nearest').values

    if db_scale:
        matrix = 10 * np.log10(np.abs(matrix) + 1e-30)

    # Downsample
    matrix_plot = matrix[:, ::downsample]
    time_plot   = ref_time[::downsample]

    # Smart color scaling
    flat       = matrix_plot.flatten()
    flat       = flat[np.isfinite(flat)]
    vmin       = np.percentile(flat, noise_floor_percentile)
    vmax       = np.percentile(flat, clip_percentile)

    if ax is None:
        _, ax = plt.subplots(figsize=(4, 6))

    # Show only every 2 repeater IDs on the y-axis
    repeater_ids_shown = [rid if i % 6 == 0 else '' for i, rid in enumerate(repeater_ids)]
    sns.heatmap(matrix_plot, ax=ax, cmap=cmap,
                xticklabels=False,
                yticklabels=repeater_ids_shown,
                cbar_kws={'label': cbar_label},
                vmin=vmin, vmax=vmax)

    # Time ticks
    n_ticks  = 24
    tick_pos = np.linspace(0, matrix_plot.shape[1]-1, n_ticks, dtype=int)
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(
        [time_plot[i].strftime('%m-%d %H:%M') for i in tick_pos],
        rotation=45, ha='right'
    )
    ax.yaxis.set_inverted(False)
    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel('Repeater ID')
    ax.set_title(title)

    # Event annotation
    if catalogue is not None:
        events = filter_catalogue(catalogue, mag_min)
        for ev in events.itertuples():
            idx = np.searchsorted(time_plot, ev.Index)
            if 0 <= idx < matrix_plot.shape[1]:
                ax.axvline(idx, color='cyan', linewidth=1.0,
                           linestyle='--', alpha=0.8)
                ax.text(idx, 0.5, f'M{ev.magnitude}',
                        color='cyan', fontsize=7, rotation=90,
                        va='bottom', ha='right')

    plt.tight_layout()
    return ax


def plot_psd(df: pd.DataFrame, component: str = 'S1',
             label: str = '', color: str = 'steelblue',
             nperseg: Optional[int] = None,
             smooth_size: int = 20,
             ax: Optional[plt.Axes] = None) -> plt.Axes:
    """
    Plot PSD in dB/Hz for a single Stokes component.

    Parameters
    ----------
    df          : DataFrame with DatetimeIndex and Stokes columns
    component   : column name to plot
    label       : legend label
    color       : line color
    nperseg     : Welch segment length
    smooth_size : log-space smoothing kernel size
    ax          : existing Axes (creates new if None)

    Returns
    -------
    matplotlib Axes
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(14, 5))

    dt = get_dt(df)
    fs = 1.0 / dt
    x  = df[component].dropna().values
    f, p = psd_db(x, fs, nperseg=nperseg, smooth_size=smooth_size)

    ax.plot(f, p, color=color, linewidth=0.9, label=label or component)
    ax.set_xscale('log')
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (dB / Hz)")
    ax.set_title(f"PSD — {component}")

    # Reference period lines
    for lbl, freq in [('24h', 1/86400), ('12h', 1/43200),
                       ('1h', 1/3600),  ('10min', 1/600)]:
        ax.axvline(freq, color='red', linewidth=0.5, linestyle=':', alpha=0.5)
        ax.text(freq, ax.get_ylim()[0] + 1, lbl, color='red',
                fontsize=7, rotation=90, va='bottom')

    return ax

def plot_spectrogram_results(spectrogramData, timeAxis, frequencyAxis, repeaterID: str,logplot = False, save = False, path = None, cmap = custom_cmap):
    """
    Args:
        spectrogramData (np.ndarray): Spectrogram data in dB (Time x Frequency).
        timeAxis (pd.Series): Time stamps for the spectrogram segments.
        frequencyAxis (np.ndarray): Frequency bins for the spectrogram.
        repeaterID (str): ID to include in the title.
    """
    
    figure_width = 9
    figure_height = 3
    
    # Calculate the midpoints between consecutive frequencies
    f_mid = (frequencyAxis[:-1] + frequencyAxis[1:]) / 2.0
    # Prepend the start edge and append the end edge
    df = frequencyAxis[1] - frequencyAxis[0]
    f_edges = np.concatenate(([frequencyAxis[0] - df/2.0], f_mid, [frequencyAxis[-1] + df/2.0]))

    # --- Changes for X-Axis Start Here ---
    # 1. Use original timeAxis. Convert to Matplotlib-friendly format if not already (e.g., if it's a pandas Series of datetime objects)
    #    Matplotlib can generally handle pandas datetime objects directly, but we need edges.

    # Calculate time *edges* based on timeAxis (time *centers*).
    # Assuming timeAxis is the *center* of the spectrogram segments.
    timeAxis_dt = timeAxis.diff().dt.total_seconds().mean() # Mean duration of a segment
    timeAxis_dt = pd.Timedelta(seconds=timeAxis_dt) if not pd.isna(timeAxis_dt) else pd.Timedelta(seconds=1) # Fallback if only 1 point

    # Calculate the edges of the time segments
    t_start_edge = timeAxis - timeAxis_dt / 2.0
    t_end_edge = timeAxis + timeAxis_dt / 2.0
    t_edges = np.concatenate((t_start_edge.to_numpy()[[0]], t_end_edge.to_numpy()))

    # Matplotlib's pcolormesh can use numpy array of datetimes (t_edges)
    # The original timeAxis for reference: timeAxis.to_numpy() 
    # --- Changes for X-Axis End Here ---

    fig, ax_spec = plt.subplots(figsize=(figure_width, figure_height))
    
    # 2. Spectrogram Plotting (surf/view(2) equivalent is pcolormesh/imshow)
    
    # Dynamic Color Limits
    all_data = spectrogramData.flatten()
    NF = np.median(all_data)*1.1  # Noise Floor estimate
    Cmax = np.percentile(all_data, 99)

    # Use t_edges directly as the X-axis for pcolormesh
    img = ax_spec.pcolormesh(
        t_edges,                # X: (L_segments + 1,) **USE EDGES**
        f_edges,                # Y: (L_masked_freq + 1,) **USE EDGES**
        spectrogramData.T,      # C: (L_masked_freq, L_segments)
        cmap=cmap,
        shading='flat',         # Use 'flat' with edges
        vmin=NF,
        vmax=Cmax
    )
    
    # 3. Apply Matplotlib Date Formatting
    # Set the x-axis label format (e.g., Hour:Minute:Second)
    # date_form = DateFormatter("%H:%M:%S")
    # ax_spec.xaxis.set_major_formatter(date_form)

    # Automatically adjust tick label rotation for better visibility
    fig.autofmt_xdate()

    # Set x-limits using the original time range's edges
    ax_spec.set_xlim(timeAxis.iloc[0], timeAxis.iloc[-1])
    ax_spec.set_xlabel('Timesamp')

    if logplot:
        ax_spec.set_yscale('log')
    # Set the minor ticks (2, 3, 4... between decades)
    # The 'subs' argument forces ticks at 2x, 3x, 4x, etc. the base power.
        ax_spec.yaxis.set_minor_locator(LogLocator(base=10.0, 
                                                subs=(2, 3, 4, 5, 6, 7, 8, 9), 
                                                numticks=100))
        
    # Optionally, you can turn off the labels for minor ticks if they cause clutter
    # ax_spec.yaxis.set_minor_formatter(NullFormatter()) 
    
    # A crucial line for small log ranges: setting the limits explicitly 
    # using the original data min/max values ensures the locator works in the tight range.
    if frequencyAxis.min() > 0:
         ax_spec.set_ylim(frequencyAxis.min() * 0.9, frequencyAxis.max() * 1.1)    
    ax_spec.set_ylabel('Frequency (Hz)')
    repeaterID_part2 = repeaterID.split("_")[1]
    ax_spec.set_title(f'Repeater: {repeaterID_part2}')
    
    # Add a color bar
    cbar = fig.colorbar(img, ax=ax_spec, pad=0.01)
    cbar.set_label('Power (dB)')
    separator = "\\"
    if save:
        if not os.path.isdir(path):
            os.mkdir(path)
        repeaterID_file = '.'.join([repeaterID,'jpg'])
        plt.savefig(separator.join([path, repeaterID_file]))
        plt.close()
    else:
        plt.show()

def event_legend_handles() -> List[Line2D]:
    """Return standard legend handles for seismic phase lines."""
    return [
        Line2D([0], [0], color='red',    linestyle='--', label='Event origin'),
        Line2D([0], [0], color=PHASE_COLORS['P'],         linestyle=':', label='P wave'),
        Line2D([0], [0], color=PHASE_COLORS['S'],         linestyle=':', label='S wave'),
        Line2D([0], [0], color=PHASE_COLORS['Surf_fast'], linestyle=':', label='Rayleigh fast'),
        Line2D([0], [0], color=PHASE_COLORS['Surf_slow'], linestyle=':', label='Rayleigh slow'),
    ]



# ══════════════════════════════════════════════════════════════════════════════
#  6. Data cleaning utils
# ══════════════════════════════════════════════════════════════════════════════

def clean_outliers_SOP(df: pd.DataFrame, params: dict) -> tuple:
    """
    Identify and remove outliers in SOP data using rolling MAD-based
    robust z-score on the magnitude of the Stokes vector derivative.

    Parameters
    ----------
    df     : DataFrame with S1, S2, S3 columns and DatetimeIndex
    params : dict with keys:
             - mad_factor: z-score threshold (typically 3-5)
             - outlier_sliding_window: rolling window in seconds

    Returns
    -------
    (df_clean, outlier_mask) — cleaned DataFrame with outliers set to NaN,
                                boolean mask where True = outlier
    """
    from pandas.api.types import is_datetime64_any_dtype

    if df.empty or not all(c in df.columns for c in ['S1', 'S2', 'S3']):
        return df, pd.Series(False, index=df.index)

    window = f'{params["outlier_sliding_window"]}s'

    diff_mag = np.sqrt(
        df['S1'].diff().fillna(0)**2 +
        df['S2'].diff().fillna(0)**2 +
        df['S3'].diff().fillna(0)**2
    )

    rolling   = diff_mag.rolling(window, center=True, min_periods=5)
    roll_med  = rolling.median()

    # Vectorized MAD — avoids slow .apply(calculate_mad)
    roll_mad  = (diff_mag - roll_med).abs().rolling(
                    window, center=True, min_periods=5).median()

    mad_zero  = roll_mad == 0
    SCALE     = 1.4826
    z_score   = (diff_mag - roll_med).abs() / (SCALE * roll_mad)

    mask = ((z_score > params["mad_factor"]) |
            (mad_zero & (diff_mag != roll_med))).values

    df_clean = df.copy()
    df_clean.loc[mask, ['S1', 'S2', 'S3']] = np.nan

    n = mask.sum()
    pct = 100 * n / len(df)
    print(f"  Outliers removed: {n} ({pct:.2f}%)")

    return df_clean, mask

def hybrid_resample(df: pd.DataFrame, q: int,
                    large_gap_threshold_samples: int = 7) -> pd.DataFrame:
    t_raw    = (df.index - df.index[0]).total_seconds().values
    dt_med   = np.median(np.diff(t_raw))
    t_uniform = np.arange(0, t_raw[-1], dt_med)

    # Vectorized gap mask
    idx       = np.clip(np.searchsorted(t_raw, t_uniform), 1, len(t_raw) - 1)
    gap_sizes = t_raw[idx] - t_raw[idx - 1]
    in_gap    = gap_sizes > (dt_med * large_gap_threshold_samples)

    # Report gaps found
    gap_starts = t_raw[idx - 1][in_gap]
    gap_ends   = t_raw[idx][in_gap]

    if len(gap_starts) > 0:
        # Merge contiguous flagged samples into discrete gap events
        gap_events = []
        g_start, g_end = gap_starts[0], gap_ends[0]
        for s, e in zip(gap_starts[1:], gap_ends[1:]):
            if s <= g_end + dt_med:  # contiguous
                g_end = e
            else:
                gap_events.append((g_start, g_end))
                g_start, g_end = s, e
        gap_events.append((g_start, g_end))

        # print(f"  Found {len(gap_events)} gap(s):")
    #     for s, e in gap_events:
    #         t_start = pd.to_datetime(df.index[0] ) + pd.to_timedelta(s, unit='s')
    #         t_end   = pd.to_datetime(df.index[0] ) + pd.to_timedelta(e, unit='s')
    #         duration = e - s
    #         print(f"    {t_start.strftime('%Y-%m-%d %H:%M:%S')} → "
    #             f"{t_end.strftime('%Y-%m-%d %H:%M:%S')} "
    #             f"({duration:.2f}s, {duration/dt_med:.0f} samples)")
    # else:
    #     print("  No large gaps found.")

    out = {}
    for col in df.columns:
        y         = df[col].values
        f_linear  = interp1d(t_raw, y, kind='linear',   bounds_error=False, fill_value=(y[0], y[-1]))
        f_cubic   = interp1d(t_raw, y, kind='cubic',    bounds_error=False, fill_value=(y[0], y[-1]))
        out[col]  = np.where(in_gap, f_linear(t_uniform), f_cubic(t_uniform))

    # Rebuild DatetimeIndex
    t0        = df.index[0]
    new_index = pd.to_datetime(t0) + pd.to_timedelta(t_uniform, unit='s')
    result    = pd.DataFrame(out, index=new_index)

    # Decimate after uniform resampling
    return result




def resample_and_decimate(df, q,large_gap_threshold_samples = 3):
    """
    1. Resample to a uniform grid based on median dt.
    2. Interpolate missing gaps.
    3. Decimate to lower fs.
    """
    # --- Step 1: Define the Uniform Grid ---
    # Convert index to seconds from start for interpolation
    t_raw = (df.index - df.index[0]).total_seconds().values
    
    # Calculate median dt (your current get_dt logic)
    dt_median = np.median(np.diff(t_raw))
       
    # --- Step 2: Interpolate onto the Grid ---
       
    df_uniform = hybrid_resample(df,q,large_gap_threshold_samples)

    # --- Step 3: Decimate the Uniform Signal ---
    decimated_dict = {
        col: decimate(df_uniform[col].values, q=q, ftype='iir', zero_phase=True)
        for col in df_uniform.columns
    }
    
    # --- Step 4: Reconstruct the DatetimeIndex ---
    new_dt = dt_median * q
    new_length = len(next(iter(decimated_dict.values())))
    
    new_index = pd.date_range(
        start=df.index[0],
        periods=new_length,
        freq=pd.Timedelta(seconds=new_dt)
    )
    
    return pd.DataFrame(decimated_dict, index=new_index)
