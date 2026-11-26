"""Modelo lineal R-N-O del Lago de Pátzcuaro (lirio, nutrientes, oxígeno)."""
from dataclasses import dataclass, replace

import numpy as np

AREA_HA = 9_000
DENSIDAD_T_HA = 200
VOLUMEN_M3 = 423e6
T_POR_MG_L = VOLUMEN_M3 / 1e6  # 1 mg/L equivale a 423 t de O2 en el lago

MATERIA_SECA = 0.083
SOLIDOS_VOLATILES = 0.8482
BIOGAS_M3_T_SV = 474.9
BIOGAS_M3_T_ST = 631


@dataclass(frozen=True)
class Parametros:
    mu: float = 0.45
    r_ef: float = 161.62
    c: float = 0.0018565
    delta: float = 0.70
    sigma_sed: float = 0.15
    L_ext: float = 261.3
    alpha: float = 0.0582
    beta: float = 23.24
    k_o: float = 36.5
    O_sat_mg_l: float = 7.5
    eta: float = 0.0

    @property
    def sigma_ef(self):
        return self.sigma_sed + self.c * self.r_ef

    @property
    def A_nat(self):
        return self.k_o * self.O_sat_mg_l * T_POR_MG_L

    def con(self, **cambios):
        return replace(self, **cambios)


Y0_DEFAULT = (360_000.0, 1_091.3, 1_903.5)


def sistema(p: Parametros):
    A = np.array([
        [-(p.mu + p.eta), p.r_ef, 0.0],
        [p.delta * p.c * p.mu, -p.sigma_ef, 0.0],
        [-p.alpha, -p.beta, -p.k_o],
    ])
    F = np.array([0.0, p.L_ext, p.A_nat])
    return A, F


def equilibrio(p: Parametros):
    A, F = sistema(p)
    return -np.linalg.solve(A, F)


def solucion(p: Parametros, y0=Y0_DEFAULT):
    """Devuelve (Yp, valores propios, vectores propios con v[0]=1, constantes C)."""
    A, _ = sistema(p)
    Yp = equilibrio(p)
    lam, V = np.linalg.eig(A)
    orden = np.argsort(-lam.real)
    lam, V = lam[orden], V[:, orden]
    for j in range(3):
        k = 0 if abs(V[0, j]) > 1e-12 else 2
        V[:, j] = V[:, j] / V[k, j]
    C = np.linalg.solve(V, np.asarray(y0) - Yp)
    return Yp, lam, V, C


def trayectoria(p: Parametros, t, y0=Y0_DEFAULT):
    Yp, lam, V, C = solucion(p, y0)
    Y = Yp[:, None] + (V * C) @ np.exp(np.outer(lam, t))
    return Y.real


def a_mg_l(O_t):
    return np.asarray(O_t) / T_POR_MG_L


def cobertura(R):
    return np.asarray(R) / DENSIDAD_T_HA / AREA_HA * 100


def biogas_millones_m3(cosecha_t):
    st = cosecha_t * MATERIA_SECA
    return st * SOLIDOS_VOLATILES * BIOGAS_M3_T_SV / 1e6, st * BIOGAS_M3_T_ST / 1e6
