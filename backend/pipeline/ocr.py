import base64
import json
import os
from openai import OpenAI

def _extract_parse_text(message) -> str:
    if getattr(message, "content", None):
        return message.content

    parts = []
    for tool_call in getattr(message, "tool_calls", []) or []:
        function = getattr(tool_call, "function", None)
        arguments = getattr(function, "arguments", None)
        if not arguments:
            continue
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            parts.append(arguments)
            continue
        for page in parsed:
            if isinstance(page, list):
                for block in page:
                    if isinstance(block, dict) and block.get("text"):
                        parts.append(block["text"].replace("<br>", "\n"))
            elif isinstance(page, dict) and page.get("text"):
                parts.append(page["text"].replace("<br>", "\n"))
    return "\n".join(parts)

def run_ocr(image_paths):
    """
    Sends each page image to NVIDIA document parse OCR and returns combined raw text.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NVIDIA_OCR_MODEL", "nvidia/nemotron-parse")
    
    if not api_key:
        print("  [run_ocr] WARNING: NVIDIA_API_KEY not set. Skipping OCR.")
        return ""

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    all_text = []

    for img_path in image_paths:
        print(f"  [run_ocr] Processing {os.path.basename(img_path)} ...")
        
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            # nvidia/nemotron-parse expects image-only content and returns extracted
            # text blocks in tool_calls.function.arguments.
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]
                }],
                max_tokens=4096
            )
            
            page_text = _extract_parse_text(response.choices[0].message)
            all_text.append(page_text)
            
        except Exception as e:
            print(f"  [run_ocr] ERROR processing {img_path}: {e}")

    return "\n\n--- PAGE BREAK ---\n\n".join(all_text)
