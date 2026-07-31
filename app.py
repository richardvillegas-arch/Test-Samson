import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo 

import matplotlib.pyplot as plt
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def fmt(val):
    return f"{val:.1f}".replace(".", ",")

DESARROLLADOR_APP = "Richard Villegas Tejeda" 
LOGO_FILE = "logo.png" 

# Default values from Streamlit interface
tag_valvula = "FCV-101"
planta_area = "Planta Principal - Área 200"
supervisor_responsable = "Carlos Mendoza"
clase_fuga = "Clase IV"
tamano_pulgadas = 6.0
cv_valvula = 300.0
fuga_medida = 0.5
unidad_medida = "SFH (SCFH)"

if unidad_medida == "l/min":
    fuga_medida_sfh = fuga_medida * 2.11888
elif unidad_medida == "m3/h":
    fuga_medida_sfh = fuga_medida * 35.3147
else:
    fuga_medida_sfh = fuga_medida

q_rated_sfh = 2150 * cv_valvula

if clase_fuga == "Clase II":
    max_fuga_sfh = 0.005 * q_rated_sfh
elif clase_fuga == "Clase III":
    max_fuga_sfh = 0.001 * q_rated_sfh
elif clase_fuga == "Clase IV":
    max_fuga_sfh = 0.0001 * q_rated_sfh
elif clase_fuga == "Clase VI":
    tabla_clase_vi = {
        1.0: 0.15,
        1.5: 0.30,
        2.0: 0.45,
        2.5: 0.60,
        3.0: 0.90,
        4.0: 1.70,
        6.0: 4.00,
        8.0: 6.75,
    }
    tamano_cercano = min(
        tabla_clase_vi.keys(), key=lambda x: abs(x - tamano_pulgadas)
    )
    max_fuga_sfh = tabla_clase_vi[tamano_cercano] * 0.00211888

if unidad_medida == "l/min":
    max_fuga_usuario = max_fuga_sfh / 2.11888
elif unidad_medida == "m3/h":
    max_fuga_usuario = max_fuga_sfh / 35.3147
else:
    max_fuga_usuario = max_fuga_sfh

aprobado = fuga_medida_sfh <= max_fuga_sfh
porcentaje_usado = (fuga_medida_sfh / max_fuga_sfh) * 100
estado_texto = "APROBADO" if aprobado else "RECHAZADO"
color_hex = "#16a34a" if aprobado else "#dc2626"


# Grafico
fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150) # Aumentado ligeramente el alto
barras = ["Fuga Medida", "Límite Máximo"]
valores = [fuga_medida, max_fuga_usuario]

bars = ax.bar(
    barras,
    valores,
    color=[color_hex, "#334155"],
    width=0.45,
    edgecolor="black",
)

for bar in bars:
    h = bar.get_height()
    ax.annotate(
        f"{fmt(h)} {unidad_medida}",
        xy=(bar.get_x() + bar.get_width() / 2, h),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

ax.set_ylabel(f"Caudal ({unidad_medida})", fontsize=10, fontweight="bold")
ax.set_title(
    f"Comparativa de Fuga vs Límite FCI 70-2 ({clase_fuga})",
    fontsize=11,
    fontweight="bold",
    pad=15 # Separación extra para el título
)
ax.axhline(
    max_fuga_usuario,
    color="#dc2626",
    linestyle="--",
    linewidth=1.2,
    label="Límite Tolerado",
)

# AJUSTE DE LÍMITES PARA EVITAR CORTES EN LOS TEXTOS
if 0 < fuga_medida < (max_fuga_usuario * 0.05):
    ax.set_yscale("log")
    # En escala logarítmica, el límite superior debe ser multiplicativo
    ax.set_ylim(bottom=fuga_medida * 0.5, top=max_fuga_usuario * 3.5)
else:
    # En escala lineal, damos un 25% extra de espacio
    ax.set_ylim(bottom=0, top=max_fuga_usuario * 1.25)

ax.legend(loc="upper right", fontsize=8)

plt.tight_layout()

img_buf = io.BytesIO()
# bbox_inches="tight" asegura que nada quede fuera de los márgenes al guardar
fig.savefig(img_buf, format="png", dpi=200, bbox_inches="tight") 
img_buf.seek(0)

# PDF Generation
file_name = f"Informe_Prueba_Fuga_{tag_valvula}_Corregido.pdf"
doc = SimpleDocTemplate(
    file_name,
    pagesize=letter,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36,
)
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "T",
    parent=styles["Heading1"],
    fontSize=13,
    textColor=colors.HexColor("#0f172a"),
    alignment=0,
    spaceAfter=2,
)
sub_style = ParagraphStyle(
    "S",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.HexColor("#475569"),
    alignment=0,
    spaceAfter=4,
)
cell_b = ParagraphStyle(
    "CB",
    parent=styles["Normal"],
    fontSize=9,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#0f172a"),
)
cell_n = ParagraphStyle(
    "CN",
    parent=styles["Normal"],
    fontSize=9,
    textColor=colors.HexColor("#1e293b"),
)
cell_c = ParagraphStyle(
    "CC", parent=styles["Normal"], fontSize=8, alignment=1
)
res_style = ParagraphStyle(
    "R",
    parent=styles["Normal"],
    fontSize=12,
    fontName="Helvetica-Bold",
    textColor=colors.white,
    alignment=1,
)
footer_style = ParagraphStyle(
    "FS",
    parent=styles["Normal"],
    fontSize=7,
    textColor=colors.HexColor("#64748b"),
    alignment=1,
)

elements = []

titulos_header = [
    Paragraph(
        "<b>PROTOCOLO DE PRUEBA DE HERMETICIDAD DE ASIENTO</b>", title_style
    ),
    Paragraph(
        "Evaluación de Hermeticidad según Norma ANSI / FCI 70-2 (IEC 60534-4)",
        sub_style,
    ),
]
elements.extend(titulos_header)

elements.append(Spacer(1, 4))
elements.append(
    HRFlowable(
        width="100%",
        thickness=1.5,
        color=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
)

fecha_actual = datetime.now(ZoneInfo("America/Santiago")).strftime(
    "%d/%m/%Y %H:%M"
)

data_info = [
    [
        Paragraph("<b>TAG Válvula:</b>", cell_b),
        Paragraph(tag_valvula, cell_n),
        Paragraph("<b>Fecha / Hora:</b>", cell_b),
        Paragraph(fecha_actual, cell_n),
    ],
    [
        Paragraph("<b>Ubicación / Área:</b>", cell_b),
        Paragraph(planta_area, cell_n),
        Paragraph("<b>Aprobado / Revisado:</b>", cell_b),
        Paragraph(supervisor_responsable, cell_n),
    ],
]
t_info = Table(
    data_info, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch]
)
t_info.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
)
elements.append(t_info)
elements.append(Spacer(1, 6))

data_res = [[
    Paragraph(
        f"<b>RESULTADO DE EVALUACIÓN: {estado_texto}</b>", res_style
    )
]]
t_res = Table(data_res, colWidths=[7.0 * inch])
t_res.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color_hex)),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
)
elements.append(t_res)
elements.append(Spacer(1, 6))

data_param = [
    [
        Paragraph("<b>Parámetro</b>", cell_b),
        Paragraph("<b>Valor / Especificación</b>", cell_b),
        Paragraph("<b>Criterio / Tolerancia</b>", cell_b),
    ],
    [
        Paragraph("Diámetro Nominal", cell_n),
        Paragraph(f'{tamano_pulgadas}"', cell_n),
        Paragraph("Tamaño del cuerpo / puerto", cell_n),
    ],
    [
        Paragraph("Capacidad Nominal (Cv)", cell_n),
        Paragraph(f"{cv_valvula}", cell_n),
        Paragraph("Coeficiente del flujo nominal", cell_n),
    ],
    [
        Paragraph("Clase de Fuga Requerida", cell_n),
        Paragraph(clase_fuga, cell_n),
        Paragraph("Norma ANSI/FCI 70-2", cell_n),
    ],
    [
        Paragraph("Presión de Prueba Estándar", cell_n),
        Paragraph("50 psig / 3.5 barg", cell_n),
        Paragraph("Medio de prueba: Aire / N2", cell_n),
    ],
    [
        Paragraph("Fuga Máxima Permitida", cell_n),
        Paragraph(f"{fmt(max_fuga_usuario)} {unidad_medida}", cell_b),
        Paragraph("Límite superior normativo", cell_n),
    ],
    [
        Paragraph("Fuga Medida en Prueba", cell_n),
        Paragraph(f"<b>{fmt(fuga_medida)} {unidad_medida}</b>", cell_b),
        Paragraph("Valor obtenido en banco", cell_n),
    ],
    [
        Paragraph("Nivel de Fuga (% del Límite)", cell_n),
        Paragraph(f"{fmt(porcentaje_usado)} %", cell_b),
        Paragraph("< 100% indica aprobación", cell_n),
    ],
]
t_param = Table(data_param, colWidths=[2.3 * inch, 2.2 * inch, 2.5 * inch])
t_param.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])
)
elements.append(t_param)
elements.append(Spacer(1, 6))

elements.append(
    RLImage(img_buf, width=6.5 * inch, height=2.8 * inch)
)
elements.append(Spacer(1, 8))

data_firmas = [[
    Paragraph(
        f"__________________________________<br/><b>{supervisor_responsable}</b><br/>Aprobado y revisado",
        cell_c,
    )
]]
t_firmas = Table(data_firmas, colWidths=[7.0 * inch])
t_firmas.setStyle(
    TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ])
)
elements.append(t_firmas)
elements.append(Spacer(1, 10))

elements.append(
    HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor("#cbd5e1"),
        spaceAfter=4,
    )
)
elements.append(
    Paragraph(
        f"Sistema de Evaluación de Válvulas | Desarrollado por: <b>{DESARROLLADOR_APP}</b>",
        footer_style,
    )
)

doc.build(elements)
print(file_name)
