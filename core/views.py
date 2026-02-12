import requests
import json
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

def diagnostic_dashboard(request):
    """
    Renders the dashboard UI for running diagnostics.
    """
    return render(request, 'core/dashboard.html')

def run_diagnostic_test(request):
    """
    Backend logic for running diagnostic tests via Python requests.
    Now supports custom HTTP methods.
    """
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
                # Use request() instead of get() to support dynamic methods if needed, though browser emulation usually implies GET navigation
                # But for flexibility we use the passed method if provided, default to GET
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
                    'elapsed': resp.elapsed.total_seconds(),
                    'response_headers': dict(resp.headers),
                    'json': resp.json() if resp.status_code == 200 or resp.headers.get('Content-Type', '').startswith('application/json') else resp.text[:1000]
                }
            except Exception as e:
                response_data = {'error': str(e)}

        return JsonResponse(response_data)

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': f"Internal Server Error: {str(e)}"}, status=500)
