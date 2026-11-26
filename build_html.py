"""Genera docs/index.html: un solo archivo HTML que funciona sin servidor ni internet."""
import base64
import re
from pathlib import Path

from latex2mathml.converter import convert

RAIZ = Path(__file__).parent

ECUACIONES = {
    "nl_R": r"\frac{dR}{dt} = r\left(\frac{N}{K_N+N}\right)R\left(1-\frac{R}{R_{max}}\right) - \mu R - H_{cos}\left(\frac{R}{h+R}\right)",
    "nl_N": r"\frac{dN}{dt} = L_{ext} + \delta c \mu R - c\,r\left(\frac{N}{K_N+N}\right)R\left(1-\frac{R}{R_{max}}\right) - \sigma_{sed} N",
    "nl_O": r"\frac{dO}{dt} = A_{nat} - \alpha R - \beta N - k_o O",
    "lin_R": r"\frac{dR}{dt} = r_{ef} N - (\mu+\eta) R",
    "lin_N": r"\frac{dN}{dt} = L_{ext} + \delta c \mu R - \sigma_{ef} N",
    "lin_O": r"\frac{dO}{dt} = A_{nat} - \alpha R - \beta N - k_o O",
    "sigma_ef": r"\sigma_{ef} = \sigma_{sed} + c\,r_{ef}",
    "A_nat": r"A_{nat} = k_o\,O_{sat}",
    "matricial": r"\frac{dY}{dt} = \left(\begin{matrix} -(\mu+\eta) & r_{ef} & 0 \\ \delta c \mu & -\sigma_{ef} & 0 \\ -\alpha & -\beta & -k_o \end{matrix}\right) Y + \left(\begin{matrix} 0 \\ L_{ext} \\ A_{nat} \end{matrix}\right)",
    "carac": r"\det(A-\lambda I) = (\lambda + k_o)\left[\lambda^2 + (\mu+\eta+\sigma_{ef})\lambda + (\mu+\eta)\sigma_{ef} - r_{ef}\,\delta c \mu\right]",
    "Np": r"N_p = \frac{L_{ext}}{\sigma_{ef} - \frac{r_{ef}\,\delta c \mu}{\mu+\eta}}",
    "Rp": r"R_p = \frac{r_{ef}\,N_p}{\mu+\eta}",
    "Op": r"O_p = \frac{A_{nat} - \alpha R_p - \beta N_p}{k_o}",
    "vec": r"v_j = \left(1,\; \frac{\mu+\eta+\lambda_j}{r_{ef}},\; -\frac{\alpha+\beta v_N}{k_o+\lambda_j}\right)^T, \qquad v_3 = (0, 0, 1)^T",
    "general": r"Y(t) = Y_p + C_1 v_1 e^{\lambda_1 t} + C_2 v_2 e^{\lambda_2 t} + C_3 v_3 e^{\lambda_3 t}",
}


def main():
    plantilla = (RAIZ / "web" / "index.html").read_text(encoding="utf-8")

    def sustituir(m):
        clave, modo = m.group(1), m.group(2) or "block"
        mathml = convert(ECUACIONES[clave], display=modo)
        return f'<div class="eqb">{mathml}</div>' if modo == "block" else mathml

    html = re.sub(r"<!--MATH:(\w+)(?::(inline|block))?-->", sustituir, plantilla)
    html = re.sub(r"__IMG_(\w+)__", lambda m: "data:image/jpeg;base64," + base64.b64encode((RAIZ / "web" / "img" / f"{m.group(1)}.jpg").read_bytes()).decode(), html)
    salida = RAIZ / "docs" / "index.html"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(html, encoding="utf-8")
    print(f"{salida} ({salida.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
