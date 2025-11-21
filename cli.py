import argparse
import json
from tools.redact import process_bytes

def main():
    parser = argparse.ArgumentParser(description="PII Redaction CLI")
    parser.add_argument("--input", required=True, help="Path to input file (text/pdf/image)")
    parser.add_argument("--out", required=False, help="Path to save redacted text output")
    parser.add_argument("--entities-json", required=False, help="Path to save entities json")

    args = parser.parse_args()

    import mimetypes, pathlib
    mime, _ = mimetypes.guess_type(args.input)
    content_type = mime or "application/octet-stream"

    data = pathlib.Path(args.input).read_bytes()
    result = process_bytes(data, content_type)

    print(json.dumps({
        "content_type": result["content_type"],
        "text_length": result["text_length"],
        "entities_count": len(result["entities"])
    }, indent=2))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result["redacted_text"])

    if args.entities_json:
        with open(args.entities_json, "w", encoding="utf-8") as f:
            json.dump(result["entities"], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
