from __future__ import annotations

import json
import os
import re
import textwrap
import unicodedata
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(".tmp") / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# Approved five-page design from prose-nes-survey-toolkit/src/prose_survey/pdf.py.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets"


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

PAGE_SIZE = (8.27, 11.69)

DARK_BG = "#07172f"
DARK_PANEL = "#0d2444"
DARK_LINE = "#17385f"
LIGHT_BG = "#f7fafc"
SURFACE = "#ffffff"
BORDER = "#d7e0ea"
TEXT = "#181c1e"
TEXT_DARK = "#f8fafc"
MUTED = "#5b6472"
MUTED_DARK = "#b6c0d1"
NAVY = "#002045"
BLUE = "#1e5aa8"
CYAN = "#7cc7ff"
TEAL = "#13696a"
GREEN = "#18a874"
AMBER = "#f6a21a"
ORANGE = "#ea580c"
ROSE = "#e24a6a"
SLATE = "#64748b"

SPACE_COLORS = {
    "SPACE-W (Satisfaction & Well-Being)": ROSE,
    "SPACE-P (Performance)": ORANGE,
    "SPACE-C (Communication & Collaboration)": CYAN,
    "SPACE-E (Efficiency & Flow)": GREEN,
}

SPACE_SHORT = {
    "SPACE-W (Satisfaction & Well-Being)": "Satisfaction & Well-Being",
    "SPACE-P (Performance)": "Performance",
    "SPACE-C (Communication & Collaboration)": "Communication & Collaboration",
    "SPACE-E (Efficiency & Flow)": "Efficiency & Flow",
}

SPACE_PT = {
    "SPACE-W (Satisfaction & Well-Being)": "Bem-estar",
    "SPACE-P (Performance)": "Performance",
    "SPACE-C (Communication & Collaboration)": "Comunica\u00e7\u00e3o",
    "SPACE-E (Efficiency & Flow)": "Fluxo",
}

QUESTION_DIMENSION_RULES = [
    (r"satisfacao|frustracao|desanimo|tensoes|conflitos|motivacao|fatores externos|bem-estar", "SPACE-W - Satisfaction & Well-Being"),
    (r"cumprimento|cumprir|comprometeu a realizar|qualidade|formacao|engenharia de software|conhecimentos", "SPACE-P - Performance"),
    (r"comunicacao|colaboracao|informacoes|transparencia|intermediarios|participacao|solucao|proposta", "SPACE-C - Communication & Collaboration"),
    (r"foco|bloqueios|tarefas nao planejadas|distribuicao|distribuidas|fluxo", "SPACE-E - Efficiency & Flow"),
]

INVERSE_HINTS = [
    "dificuldades de comunicacao",
    "intermediarios",
    "ocultacao",
    "conflitos de transparencia",
    "tarefas nao planejadas",
    "bloqueios",
    "frustracao",
    "desanimo",
    "tensoes",
    "conflitos que prejudicaram",
    "fatores externos",
    "item inverso",
]

MOJIBAKE_MARKERS = ("\u00c3", "\u00e2\u20ac", "\u00c2")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fix_mojibake(value: object) -> str:
    text = "" if value is None else str(value)
    current = text
    for _ in range(3):
        try:
            candidate = current.encode("cp1252").decode("utf-8")
        except UnicodeError:
            break
        if sum(candidate.count(marker) for marker in MOJIBAKE_MARKERS) < sum(current.count(marker) for marker in MOJIBAKE_MARKERS):
            current = candidate
        else:
            break
    return current


def _canon(value: object) -> str:
    text = _fix_mojibake(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def _is_inverse_item(label: str) -> bool:
    normalized = _canon(label)
    return any(hint in normalized for hint in INVERSE_HINTS)


def _infer_question_dimension(label: str) -> str:
    normalized = _canon(label)
    if "transparencia" in normalized or "ocultacao" in normalized:
        return "SPACE-C - Communication & Collaboration"
    for pattern, dimension in QUESTION_DIMENSION_RULES:
        if re.search(pattern, normalized):
            return dimension
    return "Dimensao nao identificada"


def _score(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _score_text(value: object) -> str:
    if value is None:
        return "n/d"
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "n/d"
    return "n/d" if np.isnan(score) else f"{score:.2f}"


def _wrap(text: object, width: int) -> str:
    return "\n".join(textwrap.wrap(_fix_mojibake(text), width=width, break_long_words=False))


def _wrapped_lines(text: object, width: int, max_lines: int | None = None) -> list[str]:
    lines = textwrap.wrap(_fix_mojibake(text), width=width, break_long_words=False)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(" .") + "..."
    return lines


def _page(facecolor: str = LIGHT_BG) -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=PAGE_SIZE, facecolor=facecolor)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(facecolor)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _save(pdf: PdfPages, fig: plt.Figure, facecolor: str) -> None:
    pdf.savefig(fig, facecolor=facecolor, dpi=600, bbox_inches=None)
    plt.close(fig)


def _logo_image(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    image = plt.imread(path)
    if image.ndim == 3 and image.shape[2] == 4:
        alpha = image[:, :, 3]
        ys, xs = np.where(alpha > 0.02)
        if len(xs) and len(ys):
            image = image[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    return image


def _logo_box(image: np.ndarray, left: float, center_y: float, height: float) -> list[float]:
    ratio = image.shape[1] / image.shape[0]
    width = height * ratio * (PAGE_SIZE[1] / PAGE_SIZE[0])
    return [left, center_y - height / 2, width, height]


def _add_logo(ax: plt.Axes, path: Path, box: list[float], alpha: float = 1.0) -> None:
    image = _logo_image(path)
    if image is None:
        return
    logo_ax = ax.figure.add_axes(box)
    logo_ax.imshow(image, alpha=alpha, interpolation="lanczos")
    logo_ax.axis("off")


def _accent_stripes(ax: plt.Axes, x: float, width: float, top: float = 0.96, bottom: float = 0.0) -> None:
    colors = [SLATE, CYAN, ROSE, ORANGE, GREEN]
    heights = [0.64, 0.88, 0.58, 0.75, 0.48]
    bar_count = len(colors)
    gap = width * 0.125
    bar_w = (width - gap * (bar_count - 1)) / bar_count
    for idx, (color, height) in enumerate(zip(colors, heights)):
        y0 = bottom
        y1 = bottom + (top - bottom) * height
        ax.add_patch(
            plt.Rectangle(
                (x + idx * (bar_w + gap), y0),
                bar_w,
                y1 - y0,
                facecolor=color,
                edgecolor=color,
                alpha=0.78,
                linewidth=0,
            )
        )


def _page_header(ax: plt.Axes, title: str, subtitle: str, page_label: str, accent: str = BLUE) -> None:
    ax.add_patch(plt.Rectangle((0.07, 0.925), 0.86, 0.006, facecolor=accent, edgecolor=accent, linewidth=0))
    ax.text(0.07, 0.89, title, color=NAVY, fontsize=22, fontweight="bold", va="top")
    ax.text(0.07, 0.862, subtitle, color=MUTED, fontsize=9.5, va="top")
    ax.text(0.93, 0.888, page_label, color="#94a3b8", fontsize=8.5, fontweight="bold", ha="right", va="top")


def _footer(ax: plt.Axes, payload: dict[str, Any], page_label: str) -> None:
    ax.add_patch(plt.Rectangle((0.07, 0.075), 0.86, 0.0015, facecolor=BORDER, edgecolor=BORDER, linewidth=0))
    ax.text(0.07, 0.052, f"NES SPACE - {_fix_mojibake(payload.get('team'))} - Sprint {payload.get('sprint')}", color="#94a3b8", fontsize=7.5)
    ax.text(0.93, 0.052, page_label, color="#94a3b8", fontsize=7.5, ha="right")


def load_team_payloads(team_dir: str | Path) -> list[dict[str, Any]]:
    metrics = Path(team_dir) / "metrics"
    payloads = [_load_json(path) for path in metrics.glob("sprint_*.json")]
    return sorted(payloads, key=lambda item: int(item.get("sprint", 9999)))


def _load_peer_payloads(team_dir: Path, sprint: int) -> list[dict[str, Any]]:
    teams_root = team_dir.parent
    payloads: list[dict[str, Any]] = []
    for candidate in sorted(teams_root.glob("T*")):
        path = candidate / "metrics" / f"sprint_{sprint}.json"
        if path.exists():
            payloads.append(_load_json(path))
    return payloads


def export_team_pdf(team_dir: str | Path, sprint: int | None = None, out_dir: str | Path | None = None) -> Path:
    team_dir = Path(team_dir)
    payloads = load_team_payloads(team_dir)
    if not payloads:
        raise ValueError(f"Nenhum JSON de metricas encontrado em {team_dir / 'metrics'}")
    selected = payloads[-1] if sprint is None else next(item for item in payloads if int(item["sprint"]) == sprint)
    selected_sprint = int(selected["sprint"])
    history_payloads = [
        item for item in payloads if int(item.get("sprint", 9999)) <= selected_sprint
    ]
    peer_payloads = _load_peer_payloads(team_dir, int(selected["sprint"]))

    out_dir = ensure_dir(out_dir or team_dir / "exports")
    out_path = out_dir / f"relatorio_{selected['team']}_sprint_{selected['sprint']}.pdf"

    with PdfPages(out_path) as pdf:
        _cover_page(pdf, selected)
        _summary_page(pdf, selected, history_payloads)
        _space_evolution_page(pdf, selected, history_payloads, peer_payloads)
        _questions_page(pdf, selected, kind="top")
        _questions_page(pdf, selected, kind="bottom")
    return out_path


def _cover_page(pdf: PdfPages, payload: dict[str, Any]) -> None:
    fig, ax = _page(DARK_BG)
    ax.add_patch(plt.Rectangle((0.0, 0.0), 0.34, 1.0, facecolor="#051124", edgecolor="none", alpha=0.68))
    _accent_stripes(ax, 0.0825, 0.175, top=0.91, bottom=0.0)
    ax.text(0.43, 0.815, "RELAT\u00d3RIO\nNES SPACE", color=TEXT_DARK, fontsize=32, fontweight="bold", va="top", linespacing=0.9)
    ax.text(
        0.43,
        0.69,
        f"{_fix_mojibake(payload.get('team'))} - Sprint {payload.get('sprint')} - {_fix_mojibake(payload.get('artifact'))}",
        color=CYAN,
        fontsize=13,
        fontweight="bold",
        va="top",
    )
    ax.text(
        0.43,
        0.61,
        _wrap(
            "Material de apoio para conversa sobre produtividade, comunica\u00e7\u00e3o, fluxo de trabalho, satisfa\u00e7\u00e3o e melhoria cont\u00ednua.",
            62,
        ),
        color=MUTED_DARK,
        fontsize=11,
        va="top",
        linespacing=1.55,
    )

    ax.add_patch(plt.Rectangle((0.43, 0.50), 0.42, 0.0025, facecolor="#315b88", edgecolor="none"))
    ax.text(0.43, 0.455, "Professor(a)", color=MUTED_DARK, fontsize=8.5, fontweight="bold", va="top")
    ax.text(0.43, 0.43, _fix_mojibake(payload.get("professor") or "n/d"), color=TEXT_DARK, fontsize=13, va="top")
    ax.text(0.63, 0.455, "Per\u00edodo", color=MUTED_DARK, fontsize=8.5, fontweight="bold", va="top")
    ax.text(0.63, 0.43, _fix_mojibake(payload.get("period") or "n/d"), color=TEXT_DARK, fontsize=13, va="top")
    ax.text(0.43, 0.365, "Participa\u00e7\u00e3o", color=MUTED_DARK, fontsize=8.5, fontweight="bold", va="top")
    ax.text(0.43, 0.34, _fix_mojibake(payload.get("participation") or "n/d"), color=TEXT_DARK, fontsize=13, va="top")
    ax.text(0.63, 0.365, "Nota do Survey", color=MUTED_DARK, fontsize=8.5, fontweight="bold", va="top")
    ax.text(0.63, 0.34, f"{_score(payload.get('nota_final')):.2f}", color=TEXT_DARK, fontsize=13, va="top")

    logo_paths = [
        ASSET_DIR / "ufms_logo_hq.png",
        ASSET_DIR / "facom_logo_hq_cover.png",
        ASSET_DIR / "ledes_logo_hq.png",
    ]
    logo_images = [_logo_image(path) for path in logo_paths]
    logo_height = 0.060
    logo_gap = 0.024
    logo_y = 0.958
    logo_offsets = [0.0, 0.0, -0.006]
    logo_items = [
        (path, image, offset)
        for path, image, offset in zip(logo_paths, logo_images, logo_offsets)
        if image is not None
    ]
    logo_widths = [_logo_box(image, 0.0, logo_y + offset, logo_height)[2] for _, image, offset in logo_items]
    logo_group_width = sum(logo_widths) + logo_gap * max(0, len(logo_widths) - 1)
    logo_left = 0.036
    for path, image, offset in logo_items:
        if image is None:
            continue
        box = _logo_box(image, logo_left, logo_y + offset, logo_height)
        _add_logo(ax, path, box)
        logo_left += box[2] + logo_gap
    line_x = 0.036
    ax.add_patch(plt.Rectangle((line_x, 0.908), logo_group_width, 0.0016, facecolor="#315b88", edgecolor="none", alpha=0.82))

    ax.text(
        0.43,
        0.105,
        "Leitura contextual. Sem ranking entre equipes ou avalia\u00e7\u00e3o individual.",
        color=MUTED_DARK,
        fontsize=8.5,
        va="bottom",
    )
    _save(pdf, fig, DARK_BG)


def _summary_page(pdf: PdfPages, payload: dict[str, Any], payloads: list[dict[str, Any]]) -> None:
    fig, ax = _page(LIGHT_BG)
    _page_header(ax, "Resumo da equipe", "Vis\u00e3o executiva para orientar a conversa de feedback.", "P\u00c1GINA 2", accent=BLUE)

    space_values = [
        _score(value, np.nan)
        for value in payload.get("space_scores", {}).values()
        if not np.isnan(_score(value, np.nan))
    ]
    space_mean = float(np.mean(space_values)) if space_values else None
    cards = [
        ("Nota do Survey", _score_text(payload.get("nota_final")), BLUE),
        ("Participa\u00e7\u00e3o", _fix_mojibake(payload.get("participation") or "n/d"), TEAL),
        ("M\u00e9dia SPACE", _score_text(space_mean), GREEN),
    ]
    x = 0.07
    for label, value, color in cards:
        _metric_card(ax, x, 0.72, 0.265, 0.12, label, value, color)
        x += 0.297

    students = str(payload.get("expected_count", "n/d"))
    context = (
        f"Professor(a): {_fix_mojibake(payload.get('professor') or 'n/d')} | "
        f"Per\u00edodo: {_fix_mojibake(payload.get('period') or 'n/d')}\n"
        f"Integrantes: {students}\n\n"
        "Este material sintetiza respostas agregadas do survey. A leitura deve apoiar reflex\u00e3o, member check e melhoria cont\u00ednua."
    )
    _text_panel(ax, 0.07, 0.515, 0.86, 0.15, "Contexto do relat\u00f3rio", context, accent=CYAN)

    dimensions = list(SPACE_COLORS)
    rows = [["Sprint", "Particip.", "Survey", "Bem-estar", "Performance", "Comunica\u00e7\u00e3o", "Fluxo"]]
    for item in payloads:
        scores = item.get("space_scores", {})
        rows.append(
            [
                f"Sprint {item['sprint']}",
                _fix_mojibake(item.get("participation") or "n/d"),
                _score_text(item.get("nota_final")),
                *[_score_text(scores.get(dimension)) for dimension in dimensions],
            ]
        )
    _table(
        ax,
        0.07,
        0.205,
        0.86,
        0.275,
        "Hist\u00f3rico completo de notas",
        rows,
        column_widths=[0.11, 0.18, 0.11, 0.14, 0.15, 0.17, 0.14],
        font_size=6.55,
    )
    _footer(ax, payload, "P\u00c1GINA 2")
    _save(pdf, fig, LIGHT_BG)


def _metric_card(ax: plt.Axes, x: float, y: float, w: float, h: float, label: str, value: str, color: str) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.add_patch(plt.Rectangle((x, y), 0.008, h, facecolor=color, edgecolor=color, linewidth=0))
    ax.text(x + 0.025, y + h - 0.032, label.upper(), color=MUTED, fontsize=7.5, fontweight="bold", va="top")
    ax.text(x + 0.025, y + 0.038, value, color=NAVY, fontsize=21, fontweight="bold", va="bottom")


def _text_panel(ax: plt.Axes, x: float, y: float, w: float, h: float, title: str, body: str, accent: str) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.add_patch(plt.Rectangle((x, y), 0.008, h, facecolor=accent, edgecolor=accent, linewidth=0))
    ax.text(x + 0.025, y + h - 0.028, title, color=NAVY, fontsize=11.5, fontweight="bold", va="top")
    wrapped = []
    wrap_width = max(48, min(96, int(w * 108)))
    for paragraph in body.splitlines():
        wrapped.extend(textwrap.wrap(paragraph, width=wrap_width, break_long_words=False) or [""])
    ax.text(x + 0.025, y + h - 0.052, "\n".join(wrapped), color=MUTED, fontsize=7.6, va="top", linespacing=1.24)


def _table(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    rows: list[list[str]],
    column_widths: list[float] | None = None,
    font_size: float = 8.4,
) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.text(x + 0.025, y + h - 0.032, title, color=NAVY, fontsize=12.5, fontweight="bold", va="top")
    widths = column_widths or [1 / len(rows[0])] * len(rows[0])
    if len(widths) != len(rows[0]) or not np.isclose(sum(widths), 1.0):
        raise ValueError("As larguras da tabela devem corresponder as colunas e somar 1.")
    starts = np.cumsum([0.0, *widths[:-1]])
    start_y = y + h - 0.073
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            color = MUTED if r == 0 else TEXT
            weight = "bold" if r == 0 else "normal"
            align = "right" if c > 0 else "left"
            tx = (
                x + w * starts[c] + 0.018
                if align == "left"
                else x + w * (starts[c] + widths[c]) - 0.012
            )
            ax.text(
                tx,
                start_y - r * 0.035,
                str(cell),
                color=color,
                fontsize=font_size,
                fontweight=weight,
                ha=align,
                va="top",
            )


def _space_evolution_page(
    pdf: PdfPages,
    payload: dict[str, Any],
    payloads: list[dict[str, Any]],
    peer_payloads: list[dict[str, Any]],
) -> None:
    fig, ax = _page(LIGHT_BG)
    _page_header(ax, "Evolu\u00e7\u00e3o SPACE", "Movimento da equipe e compara\u00e7\u00e3o contextual sem ranking.", "P\u00c1GINA 3", accent=CYAN)

    _space_slope_chart(fig, ax, 0.07, 0.49, 0.86, 0.33, payloads)

    if len(peer_payloads) > 1:
        _comparison_panel(ax, 0.07, 0.24, 0.86, 0.18, payload, peer_payloads)

    helper = (
        "Notas maiores indicam percep\u00e7\u00e3o mais positiva. Itens inversos j\u00e1 foram invertidos. "
        "A compara\u00e7\u00e3o contextual apoia a conversa e n\u00e3o \u00e9 ranking."
    )
    _text_panel(ax, 0.07, 0.105, 0.86, 0.105, "Como ler", helper, accent=SLATE)
    _footer(ax, payload, "P\u00c1GINA 3")
    _save(pdf, fig, LIGHT_BG)


def _space_slope_chart(
    fig: plt.Figure,
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    payloads: list[dict[str, Any]],
) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.text(x + 0.025, y + h - 0.034, "Notas por dimens\u00e3o SPACE", color=NAVY, fontsize=12.5, fontweight="bold", va="top")
    ax.text(x + 0.025, y + h - 0.061, "Compara\u00e7\u00e3o direta entre sprints dispon\u00edveis para a equipe.", color=MUTED, fontsize=8, va="top")

    chart = fig.add_axes([x + 0.075, y + 0.065, w * 0.45, h - 0.14], facecolor=SURFACE)
    chart.set_ylim(0, 10)
    chart.set_yticks([0, 2, 4, 6, 8, 10])
    for spine in chart.spines.values():
        spine.set_color(BORDER)
    chart.grid(axis="y", color=BORDER, alpha=0.72, linewidth=0.8)
    chart.tick_params(axis="y", colors=MUTED, labelsize=7.5)
    chart.tick_params(axis="x", colors=MUTED, labelsize=8.5, length=0)

    ordered = sorted(payloads, key=lambda item: int(item.get("sprint", 9999)))
    current = ordered[-1] if ordered else {}
    previous = ordered[-2] if len(ordered) >= 2 else None
    x_values = list(range(len(ordered)))
    chart.set_xlim(-0.18, max(len(ordered) - 1, 1) + 0.18)
    chart.set_xticks(x_values)
    chart.set_xticklabels([f"Sprint {item.get('sprint', '?')}" for item in ordered], fontweight="bold")
    chart.set_ylabel("Nota (0-10)", color=MUTED, fontsize=8)

    for idx, (space_key, color) in enumerate(SPACE_COLORS.items()):
        values = [
            _score(item.get("space_scores", {}).get(space_key), np.nan)
            for item in ordered
        ]
        if all(np.isnan(value) for value in values):
            continue
        chart.plot(x_values, values, color=color, linewidth=2.2, marker="o", markersize=5.2, zorder=3)

    for sprint_x, item in zip(x_values, ordered):
        if not item.get("space_scores"):
            chart.text(sprint_x, 0.55, "n/d", color=MUTED, fontsize=7.5, ha="center", va="center", fontweight="bold")

    _space_value_table(ax, x + 0.525, y + 0.08, w * 0.37, h - 0.16, ordered)


def _space_value_table(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    payloads: list[dict[str, Any]],
) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#f8fafc", edgecolor=BORDER, linewidth=0.8))
    ordered = sorted(payloads, key=lambda item: int(item.get("sprint", 9999)))
    current = ordered[-1] if ordered else {}
    previous = ordered[-2] if len(ordered) >= 2 else None
    sprint_count = max(1, len(ordered))
    label_x = x + 0.016
    values_left = x + w * 0.40
    values_right = x + w - 0.010
    delta_width = w * 0.16
    sprint_width = max(0.001, (values_right - values_left - delta_width) / sprint_count)

    ax.text(x + 0.016, y + h - 0.022, "Legenda e valores", color=NAVY, fontsize=7.1, fontweight="bold", va="top")
    header_y = y + h - 0.050
    ax.text(label_x, header_y, "Dim.", color=MUTED, fontsize=6.2, fontweight="bold", va="top")
    for idx, item in enumerate(ordered):
        column_x = values_left + sprint_width * (idx + 0.5)
        ax.text(
            column_x,
            header_y,
            f"S{item.get('sprint', '?')}",
            color=MUTED,
            fontsize=6.0,
            fontweight="bold",
            ha="center",
            va="top",
        )
    ax.text(values_right, header_y, "Delta", color=MUTED, fontsize=6.0, fontweight="bold", ha="right", va="top")

    row_gap = (h - 0.080) / 4
    for idx, (space_key, color) in enumerate(SPACE_COLORS.items()):
        row_y = y + h - 0.086 - idx * row_gap
        values = [
            _score(item.get("space_scores", {}).get(space_key), np.nan)
            for item in ordered
        ]
        prev_value = values[-2] if len(values) >= 2 else np.nan
        curr_value = values[-1] if values else np.nan
        delta = curr_value - prev_value if not np.isnan(prev_value) and not np.isnan(curr_value) else np.nan
        ax.add_patch(plt.Rectangle((x + 0.016, row_y - 0.006), 0.007, 0.012, facecolor=color, edgecolor=color, linewidth=0))
        ax.text(x + 0.028, row_y, SPACE_PT.get(space_key, space_key), color=TEXT, fontsize=6.25, va="center")
        for value_idx, value in enumerate(values):
            column_x = values_left + sprint_width * (value_idx + 0.5)
            is_current = value_idx == len(values) - 1
            ax.text(
                column_x,
                row_y,
                "n/d" if np.isnan(value) else f"{value:.2f}",
                color=TEXT if is_current else MUTED,
                fontsize=5.85,
                ha="center",
                va="center",
                fontweight="bold" if is_current else "normal",
            )
        ax.text(
            values_right,
            row_y,
            "n/d" if np.isnan(delta) else f"{delta:+.2f}",
            color=color,
            fontsize=5.85,
            ha="right",
            va="center",
            fontweight="bold",
        )


def _comparison_panel(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    payload: dict[str, Any],
    peer_payloads: list[dict[str, Any]],
) -> None:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.text(x + 0.025, y + h - 0.03, "Compara\u00e7\u00e3o contextual", color=NAVY, fontsize=12, fontweight="bold", va="top")
    teams = ", ".join(str(item["team"]) for item in sorted(peer_payloads, key=lambda item: int(str(item["team"])[1:])))
    caption = f"Refer\u00eancia: {teams}. M\u00e9dia das equipes dispon\u00edveis na mesma sprint."
    ax.text(x + 0.025, y + h - 0.057, caption, color=MUTED, fontsize=7.5, va="top")
    dims = list(SPACE_COLORS)
    current = payload.get("space_scores", {})
    peer_means = {
        dim: float(np.nanmean([_score(item.get("space_scores", {}).get(dim), np.nan) for item in peer_payloads]))
        for dim in dims
    }
    base_y = y + 0.095
    for idx, dim in enumerate(dims):
        row_y = base_y - idx * 0.024
        label = SPACE_SHORT.get(dim, dim)
        cur = _score(current.get(dim), np.nan)
        mean = peer_means.get(dim, np.nan)
        ax.text(x + 0.025, row_y, SPACE_PT.get(dim, label), color=TEXT, fontsize=7.2, va="center")
        ax.add_patch(plt.Rectangle((x + 0.30, row_y - 0.006), 0.32, 0.012, facecolor="#e2e8f0", edgecolor="none"))
        if not np.isnan(mean):
            ax.add_patch(plt.Rectangle((x + 0.30, row_y - 0.006), 0.32 * min(mean, 10) / 10, 0.012, facecolor="#b8c7d9", edgecolor="none"))
        if not np.isnan(cur):
            ax.add_patch(plt.Rectangle((x + 0.30, row_y - 0.006), 0.32 * min(cur, 10) / 10, 0.012, facecolor=SPACE_COLORS[dim], edgecolor="none", alpha=0.9))
        ax.text(x + w - 0.025, row_y, f"Equipe {cur:.2f} | M\u00e9dia {mean:.2f}", color=MUTED, fontsize=6.8, ha="right", va="center")


def _questions_page(pdf: PdfPages, payload: dict[str, Any], kind: str) -> None:
    if kind == "top":
        title = "Pontos Fortes percebidos"
        subtitle = "Itens com maiores notas normalizadas no survey."
        questions = payload.get("top_q", [])
        accent = GREEN
        page_label = "P\u00c1GINA 4"
        reading = "Em item inverso, nota alta indica menor presen\u00e7a percebida do problema descrito."
    else:
        title = "Pontos de Aten\u00e7\u00e3o para conversa"
        subtitle = "Itens com menores notas normalizadas, usados como guia de investiga\u00e7\u00e3o."
        questions = payload.get("bottom_q", [])
        accent = AMBER
        page_label = "P\u00c1GINA 5"
        reading = "Em item inverso, nota baixa indica maior presen\u00e7a percebida do problema descrito."

    fig, ax = _page(LIGHT_BG)
    _page_header(ax, title, subtitle, page_label, accent=accent)
    _text_panel(
        ax,
        0.07,
        0.725,
        0.86,
        0.105,
        "Leitura",
        f"{subtitle} {reading} Estes itens orientam conversa, n\u00e3o avalia\u00e7\u00e3o individual.",
        accent=accent,
    )

    y = 0.585
    for item in questions[:5]:
        _question_card(ax, 0.07, y, 0.86, 0.105, item, accent, kind)
        y -= 0.12

    _footer(ax, payload, page_label)
    _save(pdf, fig, LIGHT_BG)


def _question_card(ax: plt.Axes, x: float, y: float, w: float, h: float, item: dict[str, Any], accent: str, kind: str) -> None:
    question = _fix_mojibake(item.get("question") or "")
    score = _score(item.get("score"))
    inverse = _is_inverse_item(question)
    dimension = _infer_question_dimension(question)
    if inverse and kind == "top":
        reading = "Item inverso ja invertido: nota alta sugere menor presenca do problema."
    elif inverse:
        reading = "Item inverso ja invertido: nota baixa sugere maior presenca do problema."
    elif kind == "top":
        reading = "Nota maior indica percepcao mais positiva."
    else:
        reading = "Nota menor indica ponto para conversa."

    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=SURFACE, edgecolor=BORDER, linewidth=1.0))
    ax.add_patch(plt.Rectangle((x, y), 0.009, h, facecolor=accent, edgecolor=accent, linewidth=0))
    question_lines = _wrapped_lines(question, 72, max_lines=3)
    question_font = 8.2 if len(question_lines) <= 2 else 7.4
    ax.text(x + 0.03, y + h - 0.024, "\n".join(question_lines), color=TEXT, fontsize=question_font, fontweight="bold", va="top", linespacing=1.18)
    ax.text(x + 0.03, y + 0.018, f"Dimens\u00e3o: {dimension}", color=MUTED, fontsize=7.0, va="bottom")
    reading_lines = _wrapped_lines(reading, 48, max_lines=2)
    ax.text(x + 0.405, y + 0.018, "\n".join(reading_lines), color=MUTED, fontsize=6.55, va="bottom", linespacing=1.12)
    if inverse:
        ax.text(x + w - 0.18, y + h - 0.026, "ITEM INVERSO", color=accent, fontsize=6.8, fontweight="bold", ha="center", va="top")
    ax.text(x + w - 0.055, y + h / 2, f"{score:.2f}", color=NAVY, fontsize=17, fontweight="bold", ha="center", va="center")


def export_all_pdfs(base_output: str | Path, cohort: str, sprint: int | None = None) -> list[Path]:
    base = Path(base_output) / cohort / "teams"
    paths: list[Path] = []
    for team_dir in sorted(path for path in base.iterdir() if path.is_dir()):
        paths.append(export_team_pdf(team_dir, sprint=sprint, out_dir=Path(base_output) / cohort / "pdfs"))
    return paths
