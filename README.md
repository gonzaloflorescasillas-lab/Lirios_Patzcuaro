# Lirios Pátzcuaro

Gráficas interactivas del modelo dinámico de lirio acuático (R), nutrientes (N) y oxígeno disuelto (O) en el Lago de Pátzcuaro, con cosecha mecánica para biogás.

## Uso

```bash
pip install -r requirements.txt
streamlit run app.py
```

- `modelo.py`: sistema linealizado `Y' = AY + F`, equilibrio y solución por valores y vectores propios.
- `app.py`: app Streamlit con controles para η, L_ext, parámetros y condiciones iniciales.

## Versión HTML sin servidor

`docs/index.html` es un solo archivo autocontenido (ecuaciones, gráficas y simulador). Se abre con doble clic, sin servidor ni internet.

Para regenerarlo después de editar `web/index.html`:

```bash
pip install latex2mathml
python3 build_html.py
```
