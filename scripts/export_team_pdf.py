from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import pdf_report as design
from matplotlib.backends.backend_pdf import PdfPages


PUBLIC_FIELDS = (
    "team", "sprint", "artifact", "professor", "period", "expected_count",
    "respondent_count", "participation", "nota_final", "space_scores", "top_q", "bottom_q",
)


def public_payload(payload: dict) -> dict:
    # Only aggregate values and team metadata may enter the public PDF.
    return {key: payload[key] for key in PUBLIC_FIELDS if key in payload}


def export_team_pdf(team: str, sprint: str | int, output: Path, *, metrics_root: Path) -> Path:
    if not re.fullmatch(r"T\d+", team):
        raise ValueError("Informe uma equipe no formato T3 ou T9.")
    match = re.fullmatch(r"(?:Sprint\s+)?(\d+)", str(sprint), flags=re.I)
    if not match:
        raise ValueError("Informe uma sprint no formato 1 ou 'Sprint 1'.")
    sprint_number = int(match.group(1))
    team_dir = Path(metrics_root) / team
    history = [public_payload(item) for item in design.load_team_payloads(team_dir)
               if int(item["sprint"]) <= sprint_number]
    selected = next((item for item in history if int(item["sprint"]) == sprint_number), None)
    if selected is None:
        raise ValueError(f"Metricas da Sprint {sprint_number} nao encontradas em {team_dir / 'metrics'}")
    peers = [public_payload(item) for item in design._load_peer_payloads(team_dir, sprint_number)]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) as pdf:
        design._cover_page(pdf, selected)
        design._summary_page(pdf, selected, history)
        design._space_evolution_page(pdf, selected, history, peers)
        design._questions_page(pdf, selected, kind="top")
        design._questions_page(pdf, selected, kind="bottom")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta o PDF no modelo aprovado de cinco paginas.")
    parser.add_argument("--team", required=True)
    parser.add_argument("--sprint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metrics-root", type=Path, required=True,
                        help="Pasta local teams contendo os JSONs agregados com precisao completa; nao publicar no GitHub.")
    args = parser.parse_args()
    print(export_team_pdf(args.team, args.sprint, args.output, metrics_root=args.metrics_root))


if __name__ == "__main__":
    main()
