from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_team_pdf as exporter


class RecordingPdf:
    def __init__(self):
        self.figures = []
        self.backgrounds = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def savefig(self, fig, **kwargs):
        if kwargs.get("bbox_inches") is not None:
            raise AssertionError("Pages must retain the approved paper size")
        fig.canvas.draw()
        self.figures.append(fig)
        self.backgrounds.append(kwargs["facecolor"])


class PdfLayoutTests(unittest.TestCase):
    def test_approved_five_page_design_and_public_metadata(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with self.subTest(design="approved"):
            base = ROOT / ".tmp"
            for team, count in (("T1", 6), ("T3", 4), ("T9", 3)):
                history = []
                for sprint in (0, 1):
                    payload = {
                        "team": team, "sprint": sprint, "artifact": "Survey Alunos 1",
                        "professor": "Professor", "period": "Noturno", "expected_count": 6,
                        "respondent_count": count, "participation": f"{count}/6 ({count / 6 * 100:.1f}%)",
                        "students": ["PRIVATE STUDENT NAME"], "nota_final": 7.985243055555555,
                        "space_scores": {key: 8.123456789 for key in exporter.design.SPACE_COLORS},
                        "top_q": [{"question": "Satisfa\u00e7\u00e3o geral [Com o modo como organiza o trabalho da equipe (Em rela\u00e7\u00e3o ao professor orientador)]", "score": 9.58}] * 5,
                        "bottom_q": [{"question": "Fatores externos afetando produtividade ou bem-estar (item inverso)", "score": 3.125}] * 5,
                    }
                    history.append(payload)
                with self.subTest(team=team):
                    recording = RecordingPdf()
                    peers = [dict(history[-1], team=peer) for peer in ("T1", "T3", "T9")]
                    with patch.object(exporter, "PdfPages", return_value=recording), \
                         patch.object(exporter.design, "load_team_payloads", return_value=history), \
                         patch.object(exporter.design, "_load_peer_payloads", return_value=peers):
                        exporter.export_team_pdf(team, 1, base / "test.pdf", metrics_root=base)
                    self.assertEqual(recording.backgrounds, ["#07172f"] + ["#f7fafc"] * 4)
                    self.assertEqual(len(recording.figures), 5)
                    all_text = []
                    for page_number, fig in enumerate(recording.figures, start=1):
                        self.assertAlmostEqual(fig.get_size_inches()[0], 8.27)
                        self.assertAlmostEqual(fig.get_size_inches()[1], 11.69)
                        renderer = fig.canvas.get_renderer()
                        boxes = []
                        for axis in fig.axes:
                            for artist in axis.texts:
                                label = artist.get_text()
                                all_text.append(label)
                                box = artist.get_window_extent(renderer).transformed(fig.transFigure.inverted())
                                boxes.append((label, box))
                                self.assertGreaterEqual(box.x0, 0.02, (team, page_number, label))
                                self.assertLessEqual(box.x1, 0.98, (team, page_number, label))
                                self.assertGreaterEqual(box.y0, 0.02, (team, page_number, label))
                                self.assertLessEqual(box.y1, 0.96, (team, page_number, label))
                        for index, (label, box) in enumerate(boxes):
                            for other_label, other in boxes[index + 1:]:
                                overlap_x = min(box.x1, other.x1) - max(box.x0, other.x0)
                                overlap_y = min(box.y1, other.y1) - max(box.y0, other.y0)
                                self.assertFalse(overlap_x > 0.002 and overlap_y > 0.002,
                                                 (team, page_number, label, other_label))
                    self.assertNotIn("PRIVATE STUDENT NAME", "\n".join(all_text))
                    self.assertIn("RELAT\u00d3RIO\nNES SPACE", all_text)
                    self.assertIn("7.99", all_text)
                    self.assertIn("8.12", all_text)
                    self.assertEqual(sum(len(axis.images) for axis in recording.figures[0].axes), 3)

    def test_public_payload_preserves_precision_and_omits_names(self):
        public = exporter.public_payload({"students": ["PRIVATE"], "nota_final": 7.985243055555555})
        self.assertEqual(public, {"nota_final": 7.985243055555555})

    def test_transparency_conflicts_are_communication(self):
        self.assertTrue(exporter.design._infer_question_dimension("Conflitos de transpar\u00eancia das informa\u00e7\u00f5es").startswith("SPACE-C"))


if __name__ == "__main__":
    unittest.main()
