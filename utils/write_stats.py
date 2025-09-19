import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import json, re, sys
from bs4 import BeautifulSoup
from collections import defaultdict
from collections import Counter
from .search_helpers.stats_build_data import build_data_banks


def analyze_table_stats(table_files):
    deprecated_classes = {"table_old", "unstyled", "legacy"}

    stats = {
        "total_tables": 0,
        "tables_with_sections": 0,
        "tables_with_no_class": 0,
        "tables_with_multiple_classes": 0,
        "tables_with_deprecated_class": 0,
        "class_counts": defaultdict(int),
        "file_classes": {},
        "class_usage_per_file": defaultdict(lambda: defaultdict(int)),
        "unique_classes": [],
        "total_rows": 0,
        "total_cols": 0,
        "tables_with_header_row": 0,
        "tables_with_span": 0,
    }

    column_header_counter = Counter()
    row_label_counter = Counter()
    rows_with_exactly_2_cols = 0
    rows_with_mixed_col_counts = 0
    tables_with_inconsistent_row_lengths = 0
    tables_with_no_th = 0
    tables_with_only_th_in_col1 = 0
    th_cells_not_in_first_col = 0

    total_words = 0
    total_cells = 0
    max_rows = 0
    max_cols = 0
    row_dividers_per_table = []

    non_header_word_counter = Counter()

    for table_file in table_files:
        soup = BeautifulSoup(table_file.read_text(), "html.parser")
        tables = soup.find_all("table")
        stats["total_tables"] += len(tables)

        for t in tables:
            rows = t.find_all("tr")
            max_rows = max(max_rows, len(rows))
            table_row_dividers = sum(1 for row in rows if any("row-divider" in (cls or []) for cls in [cell.get("class") for cell in row.find_all(["td", "th"])]))
            row_dividers_per_table.append(table_row_dividers)

            stats["total_rows"] += len(rows)

            if any(cell.name == "th" for row in rows for cell in row.find_all(["th", "td"])):
                stats["tables_with_header_row"] += 1

            if any(cell.has_attr("colspan") or cell.has_attr("rowspan") for row in rows for cell in row.find_all(["td", "th"])):
                stats["tables_with_span"] += 1

            # estimate columns from the first row
            if rows:
                first_row_cells = rows[0].find_all(["td", "th"])
                stats["total_cols"] += len(first_row_cells)
                max_cols = max(max_cols, len(first_row_cells))

            # Track column headers
            if rows:
                header_cells = rows[0].find_all(["th", "td"])
                headers = [cell.get_text(strip=True).lower() for cell in header_cells]
                for h in headers:
                    if len(h) > 0:
                        column_header_counter[h] += 1

            cls = t.get("class", [])
            if not cls:
                stats["tables_with_no_class"] += 1
            if len(cls) > 1:
                stats["tables_with_multiple_classes"] += 1
            if any(c in deprecated_classes for c in cls):
                stats["tables_with_deprecated_class"] += 1
            # Detect tables with section rows: at least one <td class="row-divider"> in the table
            if any("row-divider" in td.get("class", []) for td in t.find_all("td")):
                stats["tables_with_sections"] += 1
            for c in cls:
                stats["class_counts"][c] += 1
                stats["class_usage_per_file"][table_file.name][c] += 1

            stats["file_classes"][table_file.name] = cls

            # Row and structure stats
            col_counts = set()
            for row in rows:
                cells = row.find_all(["td", "th"])
                total_cells += len(cells)
                for cell in cells:
                    text = cell.get_text(strip=True)
                    total_words += len(text.split())
                    if row != rows[0]:  # skip header row
                        words = re.findall(r'\b\w+\b', text.lower())
                        for word in words:
                            if len(word) > 2:
                                non_header_word_counter[word] += 1

                col_counts.add(len(cells))

                if cells:
                    first_cell_text = cells[0].get_text(strip=True).lower()
                    if len(first_cell_text) > 0:
                        row_label_counter[first_cell_text] += 1

                if len(cells) == 2:
                    rows_with_exactly_2_cols += 1

                th_cells = row.find_all("th")
                if not th_cells:
                    tables_with_no_th += 1
                else:
                    if all(th in row.find_all(["th", "td"])[:1] for th in th_cells):
                        tables_with_only_th_in_col1 += 1
                    if any(th not in row.find_all(["th", "td"])[:1] for th in th_cells):
                        th_cells_not_in_first_col += 1
            if len(col_counts) > 1:
                tables_with_inconsistent_row_lengths += 1

    # Group class names by prefix and sort alphabetically within each group
    grouped_counts = defaultdict(lambda: defaultdict(dict))
    class_file_map = defaultdict(list)

    for fname, classes in stats["file_classes"].items():
        for c in classes:
            class_file_map[c].append(fname)

    for class_name, count in stats["class_counts"].items():
        m = re.match(r"([a-zA-Z]+)", class_name)
        prefix = m.group(1) if m else "other"
        grouped_counts[prefix][class_name] = {
            "count": count,
            "files": sorted(class_file_map[class_name])
        }

    stats["class_counts"] = {
        group: dict(sorted(classes.items()))
        for group, classes in sorted(grouped_counts.items())
    }

    stats["unique_classes"] = sorted(
        k for g in stats["class_counts"] for k in stats["class_counts"][g]
    )

    stats["file_classes"] = {
        fname: sorted(classes) for fname, classes in sorted(stats["file_classes"].items())
    }

    # Remove unused key
    stats.pop("class_usage_per_file", None)

    if stats["total_tables"] > 0:
        stats["avg_rows_per_table"] = round(stats["total_rows"] / stats["total_tables"], 2)
        stats["avg_cols_per_table"] = round(stats["total_cols"] / stats["total_tables"], 2)

    # Add new statistics
    stats["common_column_headers"] = dict(column_header_counter.most_common(50))
    stats["common_row_labels"] = dict(row_label_counter.most_common(50))
    stats["row_structure"] = {
        "rows_with_exactly_2_cols": rows_with_exactly_2_cols,
        "rows_with_mixed_col_counts": rows_with_mixed_col_counts,
        "tables_with_inconsistent_row_lengths": tables_with_inconsistent_row_lengths
    }
    stats["th_usage"] = {
        "tables_with_no_th": tables_with_no_th,
        "tables_with_only_th_in_col1": tables_with_only_th_in_col1,
        "th_cells_not_in_first_col": th_cells_not_in_first_col
    }
    stats["avg_words_per_cell"] = round(total_words / total_cells, 2) if total_cells else 0
    stats["max_table_dimensions"] = {"rows": max_rows, "cols": max_cols}
    stats["avg_row_dividers_per_table"] = round(sum(row_dividers_per_table) / len(row_dividers_per_table), 2) if row_dividers_per_table else 0
    stats["row_labels_in_multiple_files"] = {
        label: count for label, count in row_label_counter.items() if count > 1
    }
    stats["frequent_non_header_words"] = dict(non_header_word_counter.most_common(50))

    return stats

def write_if_changed(path, content):
    if not path.exists() or path.read_text() != content:
        path.write_text(content)

def write_them_stats():
    table_dir = Path("subdex")
    table_files = list(table_dir.glob("*.table.html"))
    stats = analyze_table_stats(table_files)

    stats_path = Path("table_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(stats_path, json.dumps(stats, indent=2))
    print(f"📊 Stats file written to: {stats_path}")
    build_data_banks()

if __name__ == "__main__":
    write_them_stats()
