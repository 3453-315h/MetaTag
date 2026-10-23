"""Exporter for tracklist reports."""

import csv
import html
from pathlib import Path
from typing import List, Any

from ..track import Track


def sanitize_csv_cell(val: Any) -> Any:
    """Neutralize potential spreadsheet formula injection in CSV cells."""
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val}"
    return val


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
                    sanitize_csv_cell(t.title or t.file_path.name),
                    sanitize_csv_cell(t.artist),
                    sanitize_csv_cell(t.album),
                    t.year,
                    dur_str,
                ])
        return True
    except Exception as e:
        print(f"CSV Export error: {e}")
        return False


def export_html(tracks: List[Track], path: Path) -> bool:
    """Export tracklist to a printable HTML summary with escaped markup."""
    try:
        html_out = [
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
            track_num = html.escape(str(t.track_number or i + 1))
            title = html.escape(str(t.title or t.file_path.name))
            artist = html.escape(str(t.artist))
            album = html.escape(str(t.album))
            duration = html.escape(dur_str)

            html_out.append(
                f"<tr><td>{track_num}</td>"
                f"<td>{title}</td>"
                f"<td>{artist}</td>"
                f"<td>{album}</td>"
                f"<td>{duration}</td></tr>"
            )

        html_out.append("</tbody></table></body></html>")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_out))
        return True
    except Exception as e:
        print(f"HTML Export error: {e}")
        return False
