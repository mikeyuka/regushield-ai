import json
import os

jsonl_path = r"C:\Users\MICHEAL UKARIA\.accio\accounts\1761944498\agents\DID-F456DA-30F456DAU1777979-2768-4B2E21\sessions\DID-F456DA-30F456DAU1777979-2768-4B2E21_CID-26944498U1782541-84E868-2034-FF6FF9.messages.jsonl"
output_dir = r"C:\Users\MICHEAL UKARIA\.accio\accounts\1761944498\agents\DID-F456DA-30F456DAU1777979-2768-4B2E21\project"

with open(jsonl_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            content = data.get('content', '')
            if not content:
                continue
            
            # Look for specific markers to identify the messages we need
            if "Technical Implementation & Automation Blueprint: ReguShield AI" in content:
                out_path = os.path.join(output_dir, f"coder_blueprint_line_{i}.md")
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_path_clean = out_path
                    out_f.write(content)
                print(f"Extracted Coder blueprint from line {i} to {out_path}")
            
            elif "Organic Growth & Low-CAC Acquisition Blueprint" in content:
                out_path = os.path.join(output_dir, f"smm_blueprint_line_{i}.md")
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(content)
                print(f"Extracted SMM blueprint from line {i} to {out_path}")
                
            elif "I have completed a thorough, professional-grade financial modeling" in content:
                out_path = os.path.join(output_dir, f"financial_expert_summary_line_{i}.md")
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(content)
                print(f"Extracted Financial Expert summary from line {i} to {out_path}")
                
        except Exception as e:
            print(f"Error on line {i}: {e}")
