import csv
import json

def csv_to_jsonl(csv_file, jsonl_file):
    with open(csv_file, 'r', encoding='utf-8') as f_csv, open(jsonl_file, 'w', encoding='utf-8') as f_jsonl:
        reader = csv.DictReader(f_csv)
        for row in reader:
            input_text = row.get('input', '').strip()
            output_text = row.get('output', '').strip()
            json_line = {"input": input_text, "output": output_text}
            f_jsonl.write(json.dumps(json_line, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    csv_to_jsonl("vi.csv", "output.jsonl")