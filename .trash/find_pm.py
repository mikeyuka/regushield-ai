import json
import os

jsonl_path = r"C:\Users\MICHEAL UKARIA\.accio\accounts\1761944498\agents\DID-F456DA-30F456DAU1777979-2768-4B2E21\sessions\DID-F456DA-30F456DAU1777979-2768-4B2E21_CID-26944498U1782541-84E868-2034-FF6FF9.messages.jsonl"

with open(jsonl_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            content = data.get('content', '')
            if not content:
                continue
            
            # Check for PM, RICE, JTBD
            if "RICE" in content or "JTBD" in content or "UVP" in content or "PM's report" in content or "product manager" in content or "pm_blueprint" in content:
                print(f"Match on line {i}: {content[:150]}...")
                # let's write matches to files so we can read them
                out_path = f"pm_match_line_{i}.md"
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(content)
                print(f"Saved match to {out_path}")
        except Exception as e:
            pass
