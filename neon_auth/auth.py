import httpx
from .config import NEON_AUTH_URL, NEON_API_KEY, TEST_EMAIL, TEST_PASSWORD

def sign_up(email: str = TEST_EMAIL, password: str = TEST_PASSWORD, name: str = "capiapi_user"):
    r = httpx.post(
        f"{NEON_AUTH_URL}/sign-up/email",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NEON_API_KEY}",
            "Origin": "http://localhost:3000",
        },
        cookies={"apiKeyCookie": NEON_API_KEY},
        json={
            "name": name,
            "email": email,
            "password": password,
            "image": "",
            "callbackURL": "",
            "rememberMe": True,
        },
        timeout=30,
    )
    print(f"Sign-up status: {r.status_code}")
    print(r.text)
    return r

def sign_in(email: str = TEST_EMAIL, password: str = TEST_PASSWORD):
    r = httpx.post(
        f"{NEON_AUTH_URL}/sign-in/email",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {NEON_API_KEY}",
            "Origin": "http://localhost:3000",
        },
        cookies={"apiKeyCookie": NEON_API_KEY},
        json={
            "email": email,
            "password": password,
            "callbackURL": "",
            "rememberMe": True,
        },
        timeout=30,
    )
    print(f"Sign-in status: {r.status_code}")
    print(f"Sign-in ALL headers: {dict(r.headers)}")
    print(f"Sign-in ALL cookies: {dict(r.cookies)}")
    print(f"Sign-in body: {r.text}")
    return r

def get_jwt_token(email: str = TEST_EMAIL, password: str = TEST_PASSWORD):
    r = sign_in(email, password)
    if r.status_code == 200:
        # Obtener la cookie de sesión de la respuesta
        session_cookie = r.cookies.get("__Secure-neon-auth.session_token")
        print(f"Session cookie: {session_cookie}")
        
        if session_cookie:
            session_r = httpx.get(
                f"{NEON_AUTH_URL}/get-session",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {NEON_API_KEY}",
                    "Origin": "http://localhost:3000",
                },
                cookies={
                    "apiKeyCookie": NEON_API_KEY,
                    "__Secure-neon-auth.session_token": session_cookie,
                },
                timeout=30,
            )
            print(f"get-session status: {session_r.status_code}")
            print(f"get-session body: {session_r.text}")
            jwt = session_r.headers.get("set-auth-jwt")
            if jwt:
                print("JWT token obtained!")
                return jwt
    else:
        print(f"Sign-in failed: {r.text}")
    return None