import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modelo import (
    Y0_DEFAULT, Parametros, T_POR_MG_L, a_mg_l, biogas_millones_m3, cobertura,
    equilibrio, solucion, trayectoria,
)

st.set_page_config(page_title="Lirio en el Lago de Pátzcuaro", layout="wide")

UMBRAL_PECES = 5.0
UMBRAL_HIPOXIA = 2.5
COLOR_BASE = "#9e9e9e"
COLOR_ESC = "#1b7f5b"

st.title("Lirio acuático, nutrientes y oxígeno en el Lago de Pátzcuaro")
st.caption("Modelo dinámico R–N–O con cosecha mecánica para biogás. Mueve los controles de la izquierda para explorar el sistema.")

with st.sidebar:
    st.header("Escenario")
    eta = st.slider("η · intensidad de cosecha (año⁻¹)", 0.0, 1.0, 0.30, 0.01,
                    help="Fracción de la biomasa disponible que se cosecha cada año. 0 = sin proyecto.")
    L_ext = st.slider("L_ext · carga externa de nutrientes (t/año)", 100.0, 600.0, 261.3, 0.1)
    horizonte = st.slider("Horizonte (años)", 5, 100, 50)

    with st.expander("Parámetros del lirio y nutrientes"):
        mu = st.slider("μ · mortalidad natural (año⁻¹)", 0.10, 1.00, 0.45, 0.01)
        r_ef = st.slider("r_ef · conversión nutriente→biomasa (t t⁻¹ año⁻¹)", 50.0, 300.0, 161.62, 0.01)
        c = st.number_input("c · N+P por t de lirio fresco (t/t)", 0.0005, 0.005, 0.0018565, 0.0001, format="%.5f")
        delta = st.slider("δ · fracción reciclada", 0.0, 1.0, 0.70, 0.01)
        sigma_sed = st.slider("σ_sed · sedimentación (año⁻¹)", 0.0, 1.0, 0.15, 0.01)

    with st.expander("Parámetros del oxígeno"):
        alpha = st.number_input("α · pérdida de O₂ por lirio (t O₂ t⁻¹ año⁻¹)", 0.0, 0.5, 0.0582, 0.001, format="%.4f")
        beta = st.slider("β · demanda bioquímica (t O₂ t⁻¹ año⁻¹)", 0.0, 60.0, 23.24, 0.01)
        k_o = st.slider("k_o · reaireación (año⁻¹)", 5.0, 100.0, 36.5, 0.5)
        O_sat = st.slider("O_sat · saturación (mg/L)", 5.0, 10.0, 7.5, 0.1)

    with st.expander("Condiciones iniciales"):
        R0 = st.number_input("R(0) · biomasa de lirio (t)", 0.0, 1_500_000.0, Y0_DEFAULT[0], 10_000.0)
        N0 = st.number_input("N(0) · nutrientes (t)", 0.0, 5_000.0, Y0_DEFAULT[1], 10.0)
        O0_mg = st.number_input("O(0) · oxígeno (mg/L)", 0.0, 12.0, Y0_DEFAULT[2] / T_POR_MG_L, 0.1)

p = Parametros(mu=mu, r_ef=r_ef, c=c, delta=delta, sigma_sed=sigma_sed, L_ext=L_ext,
               alpha=alpha, beta=beta, k_o=k_o, O_sat_mg_l=O_sat, eta=eta)
base = p.con(eta=0.0)
y0 = (R0, N0, O0_mg * T_POR_MG_L)

Yp, lam, V, C = solucion(p, y0)
Yp_base = equilibrio(base)
cosecha_sost = eta * Yp[0]
bio_min, bio_max = biogas_millones_m3(cosecha_sost)

m = st.columns(5)
m[0].metric("Biomasa de equilibrio (t)", f"{Yp[0]:,.0f}", f"{(Yp[0] / Yp_base[0] - 1) * 100:+.1f} % vs sin proyecto", delta_color="inverse")
m[1].metric("Nutrientes de equilibrio (t)", f"{Yp[1]:,.0f}", f"{(Yp[1] / Yp_base[1] - 1) * 100:+.1f} %", delta_color="inverse")
m[2].metric("Oxígeno de equilibrio (mg/L)", f"{a_mg_l(Yp[2]):.2f}", f"{a_mg_l(Yp[2]) - a_mg_l(Yp_base[2]):+.2f} mg/L")
m[3].metric("Cosecha sostenible (t/año)", f"{cosecha_sost:,.0f}", f"{cosecha_sost / 365:,.0f} t/día", delta_color="off")
m[4].metric("Biogás (millones de m³/año)", f"{bio_min:.2f}–{bio_max:.2f}", "conservador – máximo", delta_color="off")

if np.any(Yp < 0):
    st.error("Con estos parámetros el equilibrio tiene valores negativos: el modelo lineal deja de ser válido.")
elif a_mg_l(Yp[2]) < UMBRAL_HIPOXIA:
    st.error(f"El oxígeno de equilibrio queda por debajo del umbral de hipoxia ({UMBRAL_HIPOXIA} mg/L).")
elif a_mg_l(Yp[2]) < UMBRAL_PECES:
    st.warning(f"El oxígeno de equilibrio queda por debajo de {UMBRAL_PECES} mg/L, referencia para peces de agua cálida.")
else:
    st.success(f"El oxígeno de equilibrio supera {UMBRAL_PECES} mg/L.")

tab_tray, tab_sens, tab_fase, tab_eig, tab_ec = st.tabs(
    ["Trayectorias", "Sensibilidad del equilibrio", "Plano de fase R–N", "Valores y vectores propios", "Ecuaciones"])

t = np.linspace(0, horizonte, 600)

with tab_tray:
    Y = trayectoria(p, t, y0)
    Yb = trayectoria(base, t, y0)
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("R(t) · biomasa de lirio (t)", "N(t) · nutrientes N+P (t)",
                                        "O(t) · oxígeno disuelto (mg/L)", "Cobertura del espejo de agua (%)"))
    series = [(Y[0], Yb[0], 1, 1), (Y[1], Yb[1], 1, 2),
              (a_mg_l(Y[2]), a_mg_l(Yb[2]), 2, 1), (cobertura(Y[0]), cobertura(Yb[0]), 2, 2)]
    for i, (esc, b, r, cc) in enumerate(series):
        fig.add_trace(go.Scatter(x=t, y=b, name="Sin proyecto (η = 0)", line=dict(color=COLOR_BASE, dash="dash"),
                                 legendgroup="b", showlegend=i == 0), row=r, col=cc)
        fig.add_trace(go.Scatter(x=t, y=esc, name=f"Escenario (η = {eta:.2f})", line=dict(color=COLOR_ESC, width=3),
                                 legendgroup="e", showlegend=i == 0), row=r, col=cc)
    fig.add_hline(y=UMBRAL_PECES, line=dict(color="orange", dash="dot"), annotation_text="5 mg/L peces", row=2, col=1)
    fig.add_hline(y=UMBRAL_HIPOXIA, line=dict(color="red", dash="dot"), annotation_text="2.5 mg/L hipoxia", row=2, col=1)
    fig.update_xaxes(title_text="t (años)", row=2)
    fig.update_layout(height=680, hovermode="x unified", margin=dict(t=90), legend=dict(orientation="h", y=1.14))
    st.plotly_chart(fig, width="stretch")

    hitos = [h for h in (0, 10, 25, 50, 100) if h <= horizonte]
    Yh = trayectoria(p, hitos, y0)
    st.dataframe(pd.DataFrame({
        "t (años)": hitos, "R (t)": Yh[0].round(0), "N (t)": Yh[1].round(1), "O (t)": Yh[2].round(0),
        "O (mg/L)": a_mg_l(Yh[2]).round(2), "Cobertura (%)": cobertura(Yh[0]).round(1),
    }), hide_index=True, width="stretch")

with tab_sens:
    col1, col2 = st.columns(2)
    etas = np.linspace(0, 1, 101)
    eq_eta = np.array([equilibrio(p.con(eta=e)) for e in etas]).T
    Ls = np.linspace(100, 600, 101)
    eq_L = np.array([equilibrio(p.con(L_ext=L)) for L in Ls]).T
    eq_L0 = np.array([equilibrio(base.con(L_ext=L)) for L in Ls]).T

    with col1:
        f = make_subplots(specs=[[{"secondary_y": True}]])
        f.add_trace(go.Scatter(x=etas, y=eq_eta[0], name="R_p (t)", line=dict(color=COLOR_ESC)))
        f.add_trace(go.Scatter(x=etas, y=etas * eq_eta[0], name="Cosecha sostenible (t/año)", line=dict(color="#8d6e63")))
        f.add_trace(go.Scatter(x=etas, y=a_mg_l(eq_eta[2]), name="O_p (mg/L)", line=dict(color="#1565c0")), secondary_y=True)
        f.add_hline(y=UMBRAL_PECES, line=dict(color="orange", dash="dot"), secondary_y=True)
        f.add_vline(x=eta, line=dict(color="black", dash="dash"), annotation_text="η elegido")
        f.update_layout(title="Equilibrio vs intensidad de cosecha η", height=450, hovermode="x unified",
                        legend=dict(orientation="h", y=-0.2))
        f.update_xaxes(title_text="η (año⁻¹)")
        f.update_yaxes(title_text="toneladas", secondary_y=False)
        f.update_yaxes(title_text="mg/L", secondary_y=True)
        st.plotly_chart(f, width="stretch")

    with col2:
        f = go.Figure()
        f.add_trace(go.Scatter(x=Ls, y=a_mg_l(eq_L0[2]), name="Sin proyecto", line=dict(color=COLOR_BASE, dash="dash")))
        f.add_trace(go.Scatter(x=Ls, y=a_mg_l(eq_L[2]), name=f"Con cosecha η = {eta:.2f}", line=dict(color=COLOR_ESC, width=3)))
        f.add_hline(y=UMBRAL_PECES, line=dict(color="orange", dash="dot"), annotation_text="5 mg/L")
        f.add_hline(y=UMBRAL_HIPOXIA, line=dict(color="red", dash="dot"), annotation_text="2.5 mg/L")
        f.add_vline(x=L_ext, line=dict(color="black", dash="dash"), annotation_text="L_ext elegido")
        f.update_layout(title="Oxígeno de equilibrio vs carga externa L_ext", height=450, hovermode="x unified",
                        xaxis_title="L_ext (t/año)", yaxis_title="O_p (mg/L)", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(f, width="stretch")

    tabla_eta = [0, 0.10, 0.20, 0.30, 0.50, 0.80]
    eqs = np.array([equilibrio(p.con(eta=e)) for e in tabla_eta]).T
    st.dataframe(pd.DataFrame({
        "η (año⁻¹)": tabla_eta, "R_p (t)": eqs[0].round(0), "N_p (t)": eqs[1].round(0),
        "O_p (mg/L)": a_mg_l(eqs[2]).round(2), "Cosecha sostenible (t/año)": (np.array(tabla_eta) * eqs[0]).round(0),
    }), hide_index=True, width="stretch")

with tab_fase:
    R_max = max(R0, Yp_base[0], Yp[0]) * 1.4
    N_max = max(N0, Yp_base[1], Yp[1]) * 1.4
    Rg, Ng = np.meshgrid(np.linspace(0, R_max, 18), np.linspace(0, N_max, 18))
    dR = p.r_ef * Ng - (p.mu + p.eta) * Rg
    dN = p.L_ext + p.delta * p.c * p.mu * Rg - p.sigma_ef * Ng
    mag = np.hypot(dR / R_max, dN / N_max) + 1e-12
    escala = 0.04
    f = go.Figure()
    for i in range(Rg.shape[0]):
        for j in range(Rg.shape[1]):
            x0, y0_ = Rg[i, j], Ng[i, j]
            x1 = x0 + escala * R_max * (dR[i, j] / R_max) / mag[i, j]
            y1 = y0_ + escala * N_max * (dN[i, j] / N_max) / mag[i, j]
            f.add_annotation(x=x1, y=y1, ax=x0, ay=y0_, xref="x", yref="y", axref="x", ayref="y",
                             showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="#b0bec5")
    tt = np.linspace(0, 40, 400)
    rng = np.random.default_rng(1)
    for k in range(8):
        y_ini = (rng.uniform(0, R_max), rng.uniform(0, N_max), y0[2])
        Yk = trayectoria(p, tt, y_ini)
        f.add_trace(go.Scatter(x=Yk[0], y=Yk[1], mode="lines", line=dict(color="#90a4ae", width=1), showlegend=False))
    Yk = trayectoria(p, tt, y0)
    f.add_trace(go.Scatter(x=Yk[0], y=Yk[1], mode="lines", name="Desde el estado actual", line=dict(color=COLOR_ESC, width=3)))
    f.add_trace(go.Scatter(x=[Yp[0]], y=[Yp[1]], mode="markers", name="Equilibrio", marker=dict(size=14, color=COLOR_ESC, symbol="star")))
    f.add_trace(go.Scatter(x=[Yp_base[0]], y=[Yp_base[1]], mode="markers", name="Equilibrio sin proyecto", marker=dict(size=12, color=COLOR_BASE, symbol="x")))
    f.update_layout(height=600, xaxis_title="R (t de lirio)", yaxis_title="N (t de N+P)",
                    xaxis_range=[0, R_max], yaxis_range=[0, N_max], title="Plano de fase del subsistema R–N")
    st.plotly_chart(f, width="stretch")

with tab_eig:
    A_df = pd.DataFrame([[-(p.mu + p.eta), p.r_ef, 0], [p.delta * p.c * p.mu, -p.sigma_ef, 0], [-p.alpha, -p.beta, -p.k_o]],
                        index=["R", "N", "O"], columns=["R", "N", "O"])
    c1, c2 = st.columns(2)
    c1.subheader("Matriz A")
    c1.dataframe(A_df.map(lambda x: f"{x:.4g}"), width="stretch")
    c2.subheader("Vector F")
    c2.dataframe(pd.DataFrame({"F": [f"{x:,.1f}" for x in (0, p.L_ext, p.A_nat)]}, index=["R", "N", "O"]), width="stretch")

    vida_media = [np.log(2) / -l.real / (1 if -l.real < 5 else 1 / 365) for l in lam]
    unidades = ["años" if -l.real < 5 else "días" for l in lam]
    st.subheader("Valores propios, vectores propios y constantes")
    st.dataframe(pd.DataFrame({
        "λ": [f"{l.real:.4f}" + (f" {l.imag:+.4f}i" if abs(l.imag) > 1e-9 else "") for l in lam],
        "Vida media": [f"{v:.2f} {u}" for v, u in zip(vida_media, unidades)],
        "v (R, N, O)": [f"({V[0, j].real:.4g}, {V[1, j].real:.4g}, {V[2, j].real:.4g})" for j in range(3)],
        "C": [f"{x.real:,.2f}" for x in C],
    }), hide_index=True, width="stretch")
    estable = np.all(lam.real < 0)
    st.markdown(f"**Estabilidad:** {'todas las partes reales son negativas, el equilibrio es estable.' if estable else 'hay valores propios con parte real ≥ 0, el equilibrio es inestable.'}")

    def termino(cn, l):
        return f"{cn.real:+,.2f}\\,e^{{{l.real:.4f}t}}"
    st.subheader("Solución explícita")
    for i, nombre in enumerate(["R", "N", "O"]):
        terms = " ".join(termino(C[j] * V[i, j], lam[j]) for j in range(3) if abs((C[j] * V[i, j]).real) > 1e-6)
        st.latex(f"{nombre}(t) = {Yp[i].real:,.1f} {terms}".replace(",", "{,}"))

with tab_ec:
    st.subheader("Forma no lineal")
    st.latex(r"\frac{dR}{dt} = r\left(\frac{N}{K_N+N}\right)R\left(1-\frac{R}{R_{max}}\right) - \mu R - H_{cos}\left(\frac{R}{h+R}\right)")
    st.latex(r"\frac{dN}{dt} = L_{ext} + \delta c \mu R - c\, r\left(\frac{N}{K_N+N}\right)R\left(1-\frac{R}{R_{max}}\right) - \sigma_{sed} N")
    st.latex(r"\frac{dO}{dt} = A_{nat} - \alpha R - \beta N - k_o O")
    st.subheader("Forma linealizada (la que se grafica)")
    st.latex(r"\frac{dR}{dt} = r_{ef} N - (\mu+\eta) R")
    st.latex(r"\frac{dN}{dt} = L_{ext} + \delta c \mu R - \sigma_{ef} N, \qquad \sigma_{ef} = \sigma_{sed} + c\, r_{ef}")
    st.latex(r"\frac{dO}{dt} = A_{nat} - \alpha R - \beta N - k_o O, \qquad A_{nat} = k_o O_{sat}")
    st.subheader("Equilibrio")
    st.latex(r"N_p = \frac{L_{ext}}{\sigma_{ef} - \dfrac{r_{ef}\,\delta c \mu}{\mu+\eta}}, \quad R_p = \frac{r_{ef} N_p}{\mu+\eta}, \quad O_p = \frac{A_{nat} - \alpha R_p - \beta N_p}{k_o}")
    st.latex(r"Y(t) = Y_p + C_1 v_1 e^{\lambda_1 t} + C_2 v_2 e^{\lambda_2 t} + C_3 v_3 e^{\lambda_3 t}")
    st.caption("Conversiones: O (mg/L) = O (t) / 423 (volumen de 423 millones de m³). Cobertura = R / (200 t/ha · 9,000 ha).")
