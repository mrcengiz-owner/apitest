import requests
import json
import sys

# Change this to your actual domain or local IP if testing locally
BASE_URL = "http://127.0.0.1:8000/api/test-connection/"

def run_diagnostics():
    print(f"Running Diagnostics on: {BASE_URL}\n")
    print("-" * 50)

    # 1. Normal Browser Emulation
    print("[1] Test: Normal Browser Simulation (HTTPS + User-Agent)")
    headers_browser = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(BASE_URL, headers=headers_browser, verify=False)  # verify=False for self-signed or local dev
        print(f"--> Status Code: {response.status_code}")
        print(f"--> Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"--> FAILED: {str(e)}")
    print("-" * 50)

    # 2. Bot Emulation (No User-Agent)
    print("[2] Test: Bot Simulation (Empty User-Agent)")
    headers_bot = {
        "User-Agent": "" # Empty UA often triggers WAF/Bot Fight Mode
    }
    try:
        response = requests.get(BASE_URL, headers=headers_bot, verify=False)
        print(f"--> Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"--> Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"--> Response: {response.text[:200]}...") # Show truncated error
    except Exception as e:
        print(f"--> FAILED: {str(e)}")
    print("-" * 50)

    # 3. HTTP Request (Insecure)
    # Note: requests library doesn't easily force HTTP 1.0/1.1 specifically without deeper config, 
    # but hitting http:// endpoint tests the protocol.
    print("[3] Test: HTTP (Insecure) Request")
    try:
        # Explicitly using http scheme if BASE_URL was https (for demonstration)
        http_url = BASE_URL.replace("https://", "http://") 
        response = requests.get(http_url, verify=False)
        print(f"--> Status Code: {response.status_code}")
        if response.status_code == 200:
             print(f"--> Protocol Detected by Server: {response.json().get('scheme')}")
        else:
             print(f"--> Response: {response.text[:200]}...")
    except Exception as e:
        print(f"--> FAILED: {str(e)}")
    print("-" * 50)

if __name__ == "__main__":
    run_diagnostics()
