import httpx
import yaml
import logging
import time
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from security.waf import WAF
from security.challenges import ChallengeManager

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Load config
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    config = {
        "proxy": {"target_url": "http://localhost:8000", "listen_port": 8080, "hidden_origin_header": "X-Shielded"},
        "security": {"waf_enabled": True, "rate_limit_enabled": True, "js_challenge_enabled": True, "sensitivity": 7, "max_404_per_minute": 10},
        "blocklist": {"ips": [], "user_agents": ["curl", "python-requests"]},
        "allowlist": {"ips": ["127.0.0.1"]}
    }

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    handlers=[
                        logging.FileHandler("logs/shield.log"),
                        logging.StreamHandler()
                    ],
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

waf = WAF(sensitivity=config['security']['sensitivity'])
challenge_mgr = ChallengeManager()

# Reputation tracking (in-memory)
reputation = {} # {ip: {"404_count": 0, "last_reset": time}}

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Skip security for allowlisted IPs
    if client_ip in config['allowlist']['ips']:
        return await call_next(request)

    # 1. IP Blocklist check
    if client_ip in config['blocklist']['ips']:
        logging.warning(f"Blocked request from blacklisted IP: {client_ip}")
        return Response(content="Your IP has been blocked by Thinking Security.", status_code=403)
    
    # 2. User-Agent check
    ua = request.headers.get("user-agent", "").lower()
    if any(bot.lower() in ua for bot in config['blocklist']['user_agents']):
        logging.warning(f"Bot detected: {ua} from {client_ip}")
        return Response(content="Access denied for automated tools.", status_code=403)

    # 3. WAF inspection (Deeper inspection)
    # Check query params and path
    request_data = f"{request.url.path} {request.url.query}"
    if waf.inspect_content(request_data):
        logging.error(f"WAF Blocked malicious URL/Query from {client_ip}")
        return Response(content="Malicious activity detected (WAF).", status_code=403)
        
    # 4. JS Challenge
    if config['security']['js_challenge_enabled']:
        # To avoid infinite loop, we should check if they just solved it
        # Real version would use a signed token or JWT
        if not request.cookies.get("shield_verified"):
             logging.info(f"Issuing JS Challenge to {client_ip} (Thinking)")
             response = challenge_mgr.get_challenge_page(str(request.url))
             # Setting a temporary bypass cookie for demonstration
             response.set_cookie(key="shield_verified", value="true", max_age=3600)
             return response

    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Internal Middleware Error: {str(e)}")
        return JSONResponse(content={"error": "Internal security layer error"}, status_code=500)
    
    # 5. Anomaly Detection (404 tracking to prevent directory brute-force)
    if response.status_code == 404:
        now = time.time()
        rep = reputation.get(client_ip, {"404_count": 0, "last_reset": now})
        if now - rep["last_reset"] > 60:
            rep["404_count"] = 0
            rep["last_reset"] = now
        rep["404_count"] += 1
        reputation[client_ip] = rep
        if rep["404_count"] > config['security'].get('max_404_per_minute', 15):
            logging.critical(f"IP {client_ip} auto-blocked for too many 404s (Brute force attempt)")
            config['blocklist']['ips'].append(client_ip) 
            
    return response

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_handler(request: Request, path: str):
    target_url = f"{config['proxy']['target_url']}/{path}"
    
    async with httpx.AsyncClient() as client:
        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None) # Let httpx handle host
        headers["X-Forwarded-For"] = request.client.host
        headers["X-Forwarded-By"] = "Thinking-Security"
        headers["X-Security-Level"] = "Premium"
        
        try:
            # Get body
            body = await request.body()
            
            proxy_resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body,
                follow_redirects=True,
                timeout=60.0 # Increased timeout for slow backend
            )
            
            # Filter response headers to avoid double headers
            resp_headers = dict(proxy_resp.headers)
            resp_headers.pop("content-encoding", None) # Let FastAPI re-encode
            resp_headers.pop("content-length", None)
            
            return Response(
                content=proxy_resp.content,
                status_code=proxy_resp.status_code,
                headers=resp_headers
            )
        except httpx.ConnectError:
            return JSONResponse(content={"error": "Origin server unreachable. Check target_url in config.yaml"}, status_code=502)
        except Exception as e:
            logging.error(f"Proxy error: {str(e)}")
            return JSONResponse(content={"error": "ShieldProxy could not complete the request"}, status_code=502)

if __name__ == "__main__":
    import uvicorn
    print(f"Thinking Security Engine starting on port {config['proxy']['listen_port']}...")
    uvicorn.run(app, host="0.0.0.0", port=config['proxy']['listen_port'])
