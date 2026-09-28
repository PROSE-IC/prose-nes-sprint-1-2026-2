from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_team_pdf as exporter


class RecordingPdf:
    def __init__(self, output):
        self.figures = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get_pagecount(self):
        return len(self.figures)

    def savefig(self, fig, **kwargs):
        if kwargs.get("bbox_inches") is not None:
            raise AssertionError("PDF pages must not be cropped to content")
        fig.canvas.draw()
        self.figures.append(fig)


class PdfLayoutTests(unittest.TestCase):
    def test_both_team_reports_fit_a4_pages(self):
        for team in ("T3", "T9"):
            with self.subTest(team=team):
                recording = RecordingPdf(None)
                with patch.object(exporter, "PdfPages", return_value=recording):
                    exporter.export_team_pdf(team, "Sprint 1", ROOT / ".tmp" / "test.pdf")
                self.assertEqual(len(recording.figures), 6)
                for page_number, fig in enumerate(recording.figures, start=1):
                    self.assertAlmostEqual(fig.get_size_inches()[0], 210 / 25.4)
                    self.assertAlmostEqual(fig.get_size_inches()[1], 297 / 25.4)
                    renderer = fig.canvas.get_renderer()
                    boxes = []
                    for text in fig.texts:
                        box = text.get_window_extent(renderer).transformed(fig.transFigure.inverted())
                        boxes.append((text.get_text(), box))
                        self.assertGreaterEqual(box.x0, 0.04, (team, page_number, text.get_text()))
                        self.assertLessEqual(box.x1, 0.96, (team, page_number, text.get_text()))
                        self.assertGreaterEqual(box.y0, 0.02, (team, page_number, text.get_text()))
                        self.assertLessEqual(box.y1, 0.96, (team, page_number, text.get_text()))
                    for index, (label, box) in enumerate(boxes):
                        for other_label, other in boxes[index + 1:]:
                            overlap_x = min(box.x1, other.x1) - max(box.x0, other.x0)
                            overlap_y = min(box.y1, other.y1) - max(box.y0, other.y0)
                            self.assertFalse(overlap_x > 0.002 and overlap_y > 0.002, (team, page_number, label, other_label))
                    if page_number == 1:
                        for text in fig.texts:
                            text_box = text.get_window_extent(renderer)
                            for logo_axis in fig.axes:
                                self.assertFalse(text_box.overlaps(logo_axis.get_window_extent(renderer)))


if __name__ == "__main__":
    unittest.main()
