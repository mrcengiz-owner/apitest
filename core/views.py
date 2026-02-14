import requests
import json
import random
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def debug_connection(request):
    """
    Debug Endpoint to analyze request headers for connection issues.
    Now reports HTTP Method and Body data.
    """
    data = {
        "status": "Alive",
        "method": request.method,
        "scheme": request.scheme,
        "client_ip": request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR'),
        "user_agent": request.META.get('HTTP_USER_AGENT'),
        "cf_ray": request.META.get('HTTP_CF_RAY'),
        "headers": {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
        "body_received": len(request.body) if request.body else 0
    }
    return JsonResponse(data)

@csrf_exempt
def mock_get_account(request):
    """
    Simulates: api/get-eligible-account/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        body = json.loads(request.body)
        amount = body.get('amount') # Should be string or number

        # Mock Response
        return JsonResponse({
            "status": "success",
            "process_token": f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            "banka_bilgileri": {
                "banka_adi": "ZİRAAT",
                "alici_adi": "AHMET MEHMET",
                "iban": "TR450015700000000125414973"
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def mock_create_transaction(request):
    """
    Simulates: api/create-transaction/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        body = json.loads(request.body)
        
        # --- SCENARIO MATCHING FOR TESTING ---
        # 1. Blocked User Simulation
        if body.get('user_id') == 'BLOCKED_USER':
            return JsonResponse({
                "status": "failed",
                "error_code": "USER_BANNED",
                "message": "This user is restricted from making transactions."
            }, status=403)

        # 2. Maintenance Mode Simulation (Specific Amount)
        if str(body.get('amount')) == '503':
            return JsonResponse({
                "status": "error",
                "message": "Payment system is currently under maintenance."
            }, status=503)

        # 3. Invalid Amount Logic
        try:
            amt = float(body.get('amount', 0))
            if amt <= 0:
                return JsonResponse({
                    "status": "failed", 
                    "error_code": "INVALID_AMOUNT", 
                    "message": "Amount must be greater than zero."
                }, status=400)
        except:
            pass # Let it fail later or handle as string

        # Support both Token-based and Direct modes
        if body.get('process_token'):
            # Token Mode
            pass
        elif body.get('amount') and body.get('user_id'):
            # Direct Mode
            pass
        else:
             return JsonResponse({'error': 'Missing required fields (process_token OR amount+user_id)'}, status=400)

        # Mock Logic for both
        result_data = {
            "status": "success",
            "process_type": "direct" if not body.get('process_token') else "token_based",
            "customer_iban": "TR18231289327218937913",
            "customer_name": body.get('full_name', 'TEST USER').upper(),
            "amount": body.get('amount', 15000.00),
            "external_id": body.get('external_id', 'ext_123'),
            "message": "Transaction created successfully. Redirect user to payment page.",
            "payment_page_url": "https://eastpay.site/pay/TRX-" + str(random.randint(100000,999999))
        }
        
        # --- TRIGGER LIVE CALLBACK SIMULATION ---
        callback_url = body.get('callback_url')
        print(f"DEBUG: Processing Transaction. Callback URL: {callback_url}")
        
        # Prepare a realistic callback payload
        callback_payload = {
            "event": "transaction.success",
            "transaction_id": "TRX-" + str(random.randint(100000, 999999)),
            "order_id": body.get('external_id'),
            "amount": body.get('amount'),
            "currency": "TRY",
            "status": "APPROVED",
            "timestamp": "2026-02-14T12:00:00Z"
        }

        # ALWAYS save callback to our local DB (Webhook Inbox)
        try:
            from core.models import WebhookLog
            WebhookLog.objects.create(
                sender_ip="SYSTEM (Callback Simulation)",
                method="POST",
                headers={"target": callback_url or "N/A", "type": "transaction.callback"},
                body=callback_payload,
                raw_body=json.dumps(callback_payload)
            )
            print("DEBUG: Callback saved to WebhookLog")
        except Exception as e:
            print(f"DEBUG: Failed to save callback to DB: {e}")

        # ALSO send to external callback URL if provided
        if callback_url:
            try:
                import threading
                def send_webhook():
                    try:
                        import requests
                        print(f"DEBUG: Sending Async Webhook to {callback_url}")
                        resp = requests.post(callback_url, json=callback_payload, timeout=5)
                        print(f"DEBUG: Webhook Result: {resp.status_code} - {resp.text[:50]}")
                    except Exception as e:
                        print(f"DEBUG: Webhook Failed: {e}")

                threading.Thread(target=send_webhook).start()
                
            except Exception as e:
                print(f"DEBUG: Main Thread Webhook Error: {e}")

        return JsonResponse(result_data)
    except Exception as e:
        print(f"DEBUG: Transaction Error: {e}")
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def mock_withdraw_request(request):
    """
    Simulates: api/public/withdraw-request/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        body = json.loads(request.body)
        if not body.get('customer_iban') or not body.get('amount'):
             return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Mock Logic
        result_data = {
            "status": "success",
            "message": "Withdraw request received",
            "transaction_id": f"W-{random.randint(10000,99999)}"
        }

        # --- TRIGGER LIVE CALLBACK SIMULATION (WITHDRAWAL) ---
        callback_url = body.get('callback_url')
        print(f"DEBUG: Processing Withdrawal. Callback URL: {callback_url}")

        # Prepare a realistic withdrawal callback payload
        callback_payload = {
            "event": "withdrawal.status",
            "transaction_id": result_data["transaction_id"],
            "external_id": body.get('external_id'),
            "amount": body.get('amount'),
            "currency": "TRY",
            "status": "PAID",
            "timestamp": "2026-02-14T12:05:00Z"
        }

        # ALWAYS save callback to our local DB (Webhook Inbox)
        try:
            from core.models import WebhookLog
            WebhookLog.objects.create(
                sender_ip="SYSTEM (Withdrawal Callback)",
                method="POST",
                headers={"target": callback_url or "N/A", "type": "withdrawal.callback"},
                body=callback_payload,
                raw_body=json.dumps(callback_payload)
            )
            print("DEBUG: Withdrawal callback saved to WebhookLog")
        except Exception as e:
            print(f"DEBUG: Failed to save withdrawal callback to DB: {e}")

        # ALSO send to external callback URL if provided
        if callback_url:
            try:
                import threading
                def send_webhook():
                    try:
                        import requests
                        import time
                        time.sleep(2)
                        print(f"DEBUG: Sending Withdrawal Webhook to {callback_url}")
                        requests.post(callback_url, json=callback_payload, timeout=5)
                    except Exception as e:
                        print(f"DEBUG: Withdrawal Webhook Failed: {e}")
                threading.Thread(target=send_webhook).start()
                
            except Exception as e:
                print(f"DEBUG: Withdrawal Callback Error: {e}")

        return JsonResponse(result_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def diagnostic_dashboard(request):
    """
    Renders the dashboard UI for running diagnostics.
    """
    return render(request, 'core/dashboard.html')

def run_diagnostic_test(request):
    """
    Backend logic for running diagnostic tests via Python requests.
    """
    # ... (rest of the function remains same)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        target_url = data.get('target_url')
        test_type = data.get('test_type')
        http_method = data.get('http_method', 'GET').upper()
        payload = data.get('payload', {})
        
        if not target_url:
             return JsonResponse({'error': 'Target URL required'}, status=400)

        response_data = {}
        headers = {}
        verify_ssl = False # For local dev environments

        if test_type == 'browser':
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            try:
                resp = requests.request(http_method, target_url, headers=headers, json=payload, verify=verify_ssl, timeout=10)
                response_data = {
                    'status_code': resp.status_code,
                    'method_used': resp.request.method,
                    'json': resp.json() if resp.status_code == 200 else resp.text[:500]
                }
            except Exception as e:
                response_data = {'error': str(e)}

        elif test_type == 'bot':
            headers["User-Agent"] = "" # Empty UA
            try:
                resp = requests.request(http_method, target_url, headers=headers, json=payload, verify=verify_ssl, timeout=10)
                response_data = {
                    'status_code': resp.status_code,
                    'method_used': resp.request.method,
                    'json': resp.json() if resp.status_code == 200 else resp.text[:500]
                }
            except Exception as e:
                 response_data = {'error': str(e)}

        elif test_type == 'http':
             # Force HTTP scheme
             if target_url.startswith('https://'):
                 target_url = target_url.replace('https://', 'http://')
             try:
                resp = requests.request(http_method, target_url, json=payload, verify=verify_ssl, timeout=10)
                if resp.history:
                    # Check for redirects
                    response_data = {
                        'status_code': resp.status_code,
                        'method_used': resp.request.method,
                         'redirect_history': [r.url for r in resp.history],
                        'final_url': resp.url,
                         'json': resp.json() if resp.status_code == 200 else resp.text[:500]
                    }
                else:
                    response_data = {
                        'status_code': resp.status_code,
                        'method_used': resp.request.method,
                        'json': resp.json() if resp.status_code == 200 else resp.text[:500]
                    }
             except Exception as e:
                response_data = {'error': str(e)}
        
        elif test_type == 'custom':
            # Fully custom request with Headers support (Postman-style)
            request_headers = {"User-Agent": "NexKasa-Diagnostic-Tool/1.0"}
            
            # Merge custom headers from frontend
            custom_headers = data.get('custom_headers', {})
            if custom_headers:
                # Remove empty keys
                clean_headers = {k: v for k, v in custom_headers.items() if k.strip()}
                request_headers.update(clean_headers)

            try:
                resp = requests.request(
                    http_method, 
                    target_url, 
                    headers=request_headers, 
                    json=payload, 
                    verify=verify_ssl, 
                    timeout=10
                )
                
                response_data = {
                    'status_code': resp.status_code,
                    'method_used': resp.request.method,
                    'headers_sent': dict(resp.request.headers),
                    'elapsed': resp.elapsed.total_seconds() * 1000, # ms
                    'response_headers': dict(resp.headers),
                    # Try to parse JSON, if fails return text
                    'json': None
                }
                
                try:
                    response_data['json'] = resp.json()
                except:
                    # Return full text (up to 100KB) for HTML debugging
                    response_data['json'] = resp.text[:100000] 

            except Exception as e:
                response_data = {'error': str(e)}

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': f"Internal Server Error: {str(e)}"}, status=500)

# --- WEBHOOK SYSTEM ---
from core.models import WebhookLog
from django.utils import timezone

@csrf_exempt
def webhook_listener(request):
    """
    Endpoint that accepts ANY webhook and stores it for inspection.
    URL: /api/webhook-listener/
    """
    try:
        print(f"DEBUG: Listener hit by {request.method}")
        # Capture Data
        client_ip = request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR')
        # Simple header capture
        headers = {}
        for k, v in request.META.items():
            if k.startswith('HTTP_') or k in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                headers[k] = str(v)
        
        # Parse Body
        body_data = {}
        raw_body = ""
        try:
            raw_body = request.body.decode('utf-8', errors='ignore')
            if raw_body:
                body_data = json.loads(raw_body)
        except:
            pass # Keep empty if not JSON

        print(f"DEBUG: Webhook Body: {body_data}")

        # Save to DB
        log = WebhookLog.objects.create(
            sender_ip=client_ip,
            method=request.method,
            headers=headers,
            body=body_data,
            raw_body=raw_body
        )
        print(f"DEBUG: Webhook Saved ID: {log.id}")
        
        return JsonResponse({"status": "received", "log_id": str(log.id)}, status=200)

    except Exception as e:
        print(f"DEBUG: Listener Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def get_webhook_logs(request):
    """
    Returns the last 20 received webhooks for the dashboard UI.
    URL: /api/get-webhook-logs/
    """
    try:
        logs = WebhookLog.objects.all().order_by('-timestamp')[:20]
        data = []
        for log in logs:
            data.append({
                "id": str(log.id),
                "timestamp": log.timestamp.strftime("%H:%M:%S"),
                "method": log.method,
                "body": log.body,
                "headers": log.headers
            })
        print(f"DEBUG: Returning {len(data)} webhook logs")
        return JsonResponse({"logs": data})
    except Exception as e:
        print(f"DEBUG: Get Webhook Logs Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
