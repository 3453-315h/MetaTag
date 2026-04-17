"""Exporter for tracklist reports."""

import csv
from pathlib import Path
from typing import List, Any

from ..track import Track

def export_csv(tracks: List[Track], path: Path) -> bool:
    """Export tracklist to a CSV file."""
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Title", "Artist", "Album", "Year", "Duration"])
            for i, t in enumerate(tracks):
                dur_s = t.duration // 1000
                dur_str = f"{dur_s // 60}:{dur_s % 60:02d}"
                writer.writerow([
                    t.track_number or i + 1,
                    t.title or t.file_path.name,
                    t.artist,
                    t.album,
                    t.year,
                    dur_str
                ])
        return True
    except Exception as e:
        print(f"CSV Export error: {e}")
        return False

def export_html(tracks: List[Track], path: Path) -> bool:
    """Export tracklist to a printable HTML summary."""
    try:
        html = [
            "<html><head><style>",
            "body { font-family: sans-serif; padding: 40px; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 20px; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "th { background-color: #f4f4f4; }",
            "h1 { color: #333; }",
            "</style></head><body>",
            "<h1>MetaTag — Tracklist Report</h1>",
            f"<p>Exported {len(tracks)} tracks.</p>",
            "<table><thead><tr><th>#</th><th>Title</th><th>Artist</th><th>Album</th><th>Duration</th></tr></thead><tbody>"
        ]
        
        for i, t in enumerate(tracks):
            dur_s = t.duration // 1000
            dur_str = f"{dur_s // 60}:{dur_s % 60:02d}"
            html.append(f"<tr><td>{t.track_number or i + 1}</td>"
                        f"<td>{t.title or t.file_path.name}</td>"
                        f"<td>{t.artist}</td>"
                        f"<td>{t.album}</td>"
                        f"<td>{dur_str}</td></tr>")
        
        html.append("</tbody></table></body></html>")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
        return True
    except Exception as e:
        print(f"HTML Export error: {e}")
        return False
