import json
import urllib.request
import urllib.error
import os

def test_api(url, headers, data, name):
    print(f"Testing {name}...")
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"SUCCESS: {name}: {result['choices'][0]['message']['content'][:100]}...\n")
    except urllib.error.HTTPError as e:
        print(f"FAILED: {name}: HTTP Error {e.code} - {e.read().decode('utf-8')}\n")
    except Exception as e:
        print(f"FAILED: {name}: {str(e)}\n")

# OpenRouter (Perplexity Sonar)
or_key = "REDACTED_OPENROUTER_KEY"
test_api(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
    data={"model": "perplexity/sonar", "messages": [{"role": "user", "content": "What is 2+2?"}]},
    name="OpenRouter (Perplexity Sonar)"
)

# NVIDIA (Llama 3.3 70B Instruct)
nv_key = "REDACTED_NVIDIA_KEY"
test_api(
    url="https://integrate.api.nvidia.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {nv_key}", "Content-Type": "application/json"},
    data={"model": "meta/llama-3.3-70b-instruct", "messages": [{"role": "user", "content": "What is 2+2?"}], "max_tokens": 50},
    name="NVIDIA (LLaMA 3.3 70B)"
)

# Supabase REST API Test
sb_url = "https://vyylfvwtcuyfyjgcanoy.supabase.co/rest/v1/"
sb_key = "REDACTED_SUPABASE_KEY"
print("Testing Supabase connection...")
req = urllib.request.Request(sb_url, headers={"apikey": sb_key, "Authorization": f"Bearer {sb_key}"})
try:
    with urllib.request.urlopen(req) as response:
        print(f"SUCCESS: Supabase: Connected. Status {response.status}\n")
except urllib.error.HTTPError as e:
    print(f"FAILED: Supabase: HTTP Error {e.code} - {e.read().decode('utf-8')}\n")
except Exception as e:
    print(f"FAILED: Supabase: {str(e)}\n")
