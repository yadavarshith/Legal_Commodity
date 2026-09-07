import json
import urllib.request
from pathlib import Path

uploads_dir = Path("d:/Legal_Commodity/uploads")
image_files = [
    uploads_dir / "label_5ff2b5cd.png",
    uploads_dir / "label_3b4b3256.jpeg",
    uploads_dir / "label_76b6011e.jpeg",
]

print("=== PART 1 VERIFICATION: PIPELINE TRACE FOR 3 DIFFERENT IMAGES ===")

def post_multipart(url, fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = []
    
    for key, value in fields.items():
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        body.append(b"")
        body.append(value.encode())
        
    for key, filename, content in files:
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode())
        body.append(b'Content-Type: image/jpeg')
        body.append(b"")
        body.append(content)
        
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    
    payload = b"\r\n".join(body)
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

for idx, img_path in enumerate(image_files, start=1):
    if not img_path.exists():
        print(f"File not found: {img_path}")
        continue
    print(f"\n--- TEST IMAGE #{idx}: {img_path.name} ---")
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    
    try:
        result = post_multipart(
            "http://127.0.0.1:8000/upload-and-scan",
            {"category": "all", "package_type": "pre-packaged", "import_status": "domestic"},
            [("file", img_path.name, img_bytes)]
        )
        print(f"Inspection ID: {result.get('inspection_id')}")
        print(f"Overall Status: {result.get('overall_status')}")
        print(f"OCR Text Line Count: {len(result.get('ocr_results', []))}")
        print("Extracted Declarations:")
        for d in result.get('declarations', []):
            print(f"   • {d.get('type')}: '{d.get('normalized_value')}' (raw: '{d.get('raw_text')}')")
        print("Rule Findings (Sample):")
        for f in result.get('findings', [])[:4]:
            print(f"   • [{f.get('rule_id')} | {f.get('status')}]: {f.get('description')}")
    except Exception as e:
        print(f"HTTP Error: {e}")
