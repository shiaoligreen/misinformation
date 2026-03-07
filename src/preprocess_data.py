import os
import json
import glob
import pandas as pd

def preprocess_raw_data():
    raw_dir = "../data/raw"
    preprocessed_dir = "../data/preprocessed"
    os.makedirs(preprocessed_dir, exist_ok=True)
    raw_files = glob.glob(os.path.join(raw_dir, "*_annotations.json"))
    for filepath in raw_files:
        base_name = os.path.basename(filepath)
        print(f"Processing {base_name}...")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data: continue
        records = []
        for record in data:
            item_data = record.get("data", {})
            annotations = record.get("annotations", [])
            res_list = annotations[0].get("result", []) if annotations else []
            vals = {"all_caps": [], "exclamation_marks": [], "hedging": [], "adjectives": [], "unk": []}
            for res in res_list:
                if "value" in res and "labels" in res["value"]:
                    for label in res["value"]["labels"]:
                        if label in vals:
                            val_text = res["value"].get("text", "")
                            start = res["value"].get("start")
                            end = res["value"].get("end")
                            
                            vals[label].append((val_text, start, end))
            records.append({
                "ID": item_data.get("Unnamed: 0") or item_data.get("id") or item_data.get("ID"),
                "Text": item_data.get("text") or item_data.get("Text"),
                "misinformation_label": item_data.get("label"),
                "all_caps": vals["all_caps"],
                "exclamation_marks": vals["exclamation_marks"],
                "hedging": vals["hedging"],
                "adjectives": vals["adjectives"],
                "unk": vals["unk"]
            })
        df = pd.DataFrame(records)
        for old, new in [("id", "ID"), ("Unnamed: 0", "ID"), ("text", "Text")]:
            if old in df.columns: df.rename(columns={old: new}, inplace=True)
        if "ID" in df.columns and "Text" in df.columns:
            df.drop_duplicates(subset=["ID", "Text"], keep="first", inplace=True)
        out_path = os.path.join(preprocessed_dir, base_name.replace(".json", "_cleaned.json"))
        df.to_json(out_path, orient="records", indent=2)
        print(f"Saved to {os.path.basename(out_path)}")

if __name__ == "__main__":
    preprocess_raw_data()