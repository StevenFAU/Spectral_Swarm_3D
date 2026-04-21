"""Surrogate null testing for 3D swarm analysis (D1).

Phase 5 implementation target. See SpectralSwarm3DPhases.md §Phase 5 and D1.

Implements trajectory-shuffled surrogates: per-agent time series are independently
circularly shifted, destroying cross-agent temporal dependence while preserving
marginal distributions. If observed Phi_spectral exceeds the surrogate distribution,
the measured integration is real rather than an estimator artifact.

Run on one representative seed per scenario with 10 shuffle iterations (D1).

Standard practice in time-series MI analysis; analogous to sklearn's
mutual_info_regression tie-breaking noise convention.
"""
import numpy as np


def circular_shift_surrogate(telemetry, rng: np.random.Generator):
    """Produce one surrogate by independently circularly shifting each agent's time series.

    Phase 5. Destroys cross-agent temporal dependence while preserving marginal distributions.

    Parameters
    ----------
    telemetry : pd.DataFrame
        One run's telemetry.
    rng : np.random.Generator
        Random generator for shift amounts.

    Returns
    -------
    pd.DataFrame
        Shuffled telemetry with same shape and marginals as input.
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md D1")


def compute_surrogate_null(
    telemetry_path: str,
    config: dict,
    n_surrogates: int = 10,
    seed: int = 0,
) -> dict:
    """Compute observed vs. surrogate-null Phi_spectral and top TDA summaries. Phase 5.

    Parameters
    ----------
    telemetry_path : str
    config : dict
    n_surrogates : int
        Number of surrogate shuffles (D1 default: 10).
    seed : int
        Seed for shuffle RNG.

    Returns
    -------
    dict
        Keys: observed_phi, surrogate_phi_mean, surrogate_phi_std,
              observed_snap_TP_1, surrogate_snap_TP_1_mean, etc.
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md D1")
