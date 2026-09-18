"""Render the owner's standalone delivery dashboard from its existing report data."""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8-sig"))
    template = Path(__file__).resolve().parent.parent / "assets" / "delivery-dashboard.html"
    # Prevent user content from terminating the JSON script block.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    result = template.read_text(encoding="utf-8").replace("__REPORT_DATA__", payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(args.output.resolve())

if __name__ == "__main__":
    main()
