import time
import base64
import json
import requests
from jose import jwk, jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse


# ====== CONFIG ======
REGION = "us-east-1"
USER_POOL_ID = "us-east-1_HnQ0JSedi"
CLIENT_ID = "66iq182l7gfjkh73enrs0ham4a"
CLIENT_SECRET= "1mbc0s1k36dm15j8hr1o44meomlosiahp63k5osb36riojqcpph0"
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
# REDIRECT_URI = "http://localhost:6006/callback"
REDIRECT_URI = "https://chatwithexcel.operisoft.com/api/callback"
# HOSTED_UI_DOMAIN = f"https://us-east-1hnq0jsedi.auth.us-east-1.amazoncognito.com"
HOSTED_UI_DOMAIN = f"https://us-east-1hnq0jsedi.auth.us-east-1.amazoncognito.com"

authorize_url = f"{HOSTED_UI_DOMAIN}/oauth2/authorize"
token_url = f"{HOSTED_UI_DOMAIN}/oauth2/token"

# ====== JWKS CACHE ======
JWKS_CACHE = None
JWKS_LAST_FETCH = 0
JWKS_TTL = 3600  # 1 hour

def get_jwks():
    global JWKS_CACHE, JWKS_LAST_FETCH
    now = time.time()
    if JWKS_CACHE is None or (now - JWKS_LAST_FETCH) > JWKS_TTL:
        resp = requests.get(JWKS_URL)
        resp.raise_for_status()
        JWKS_CACHE = resp.json()
        JWKS_LAST_FETCH = now
    return JWKS_CACHE

def get_public_key(kid: str):
    jwks = get_jwks()
    for key in jwks['keys']:
        if key['kid'] == kid:
            return key
    return None

def decode_and_verify(token: str) -> dict:
    # Decode header to get kid
    headers_segment = token.split('.')[0]
    padded = headers_segment + '=' * (4 - len(headers_segment) % 4)
    headers = json.loads(base64.urlsafe_b64decode(padded))
    kid = headers['kid']

    key = get_public_key(kid)
    if not key:
        raise HTTPException(status_code=401, detail="Public key not found")

    public_key = jwk.construct(key)
    public_key_pem = public_key.to_pem().decode()

    try:
        claims = jwt.decode(
            token,
            public_key_pem,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}",
            options={"verify_at_hash": False}
        )
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")



# ====== FASTAPI APP ======
app = FastAPI()
auth_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials
    return decode_and_verify(token)

@app.get("/secure")
def secure_endpoint(user: dict = Depends(verify_token)):
    return {"message": "You are authorized!", "user": user}

@app.get("/callback")
async def handle_callback(request: Request):
    code = request.query_params.get("code")
    print(code)
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}"
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    print("HIII")

    response = requests.post(
        token_url,
        headers=headers,
        data=data
    )
    tokens = response.json()
    print(tokens)
    # Optionally store tokens or pass to frontend via redirect
    # return RedirectResponse(f"http://localhost:8501?id_token={tokens.get('id_token')}")
    return RedirectResponse(f"https://chatwithexcel.operisoft.com?id_token={tokens.get('id_token')}")
