from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config import GOOGLE_CLIENT_ID, JWT_SECRET_KEY
from database import supabase


def verify_google_token(token: str):
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")

    info = id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        GOOGLE_CLIENT_ID
    )

    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Invalid Google token issuer")

    return info


def upsert_profile(google_user: dict):
    google_sub = google_user["sub"]
    email = google_user.get("email", "").lower()
    name = google_user.get("name", email.split("@")[0])
    picture = google_user.get("picture")

    result = (
        supabase.table("profiles")
        .upsert(
            {
                "google_sub": google_sub,
                "email": email,
                "full_name": name,
                "avatar_url": picture,
            },
            on_conflict="google_sub",
        )
        .execute()
    )

    if not result.data:
        raise RuntimeError("Unable to create/update profile")

    return result.data[0]


def create_app_token(profile):
    payload = {
        "sub": str(profile["id"]),
        "email": profile["email"],
        "name": profile["full_name"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def decode_app_token(token):
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing Authorization token"}), 401

        token = header.split(" ", 1)[1]

        try:
            user = decode_app_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return fn(user, *args, **kwargs)

    return wrapper
