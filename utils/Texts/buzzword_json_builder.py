import json
from pathlib import Path

def convert_buzzwords_to_json(
    input_path=Path("utils/Texts/buzzwords.txt"),
    output_path=Path("static/data/buzzwords.json"),
    verbose=True,
):
    buzzwords = []

    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            left, right = line.split("=", 1)
            term = left.strip()
            assoc = right.strip()
            buzzwords.append({"term": term, "assoc": assoc})

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(buzzwords, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"✅ Converted {len(buzzwords)} buzzwords to JSON.")