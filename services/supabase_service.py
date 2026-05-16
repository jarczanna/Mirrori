import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)

def get_service_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)

# ─── USERS ───────────────────────────────────

def create_user(email: str, plan: str = "essential") -> dict:
    sb = get_client()
    result = sb.table("users").insert({"email": email, "plan": plan}).execute()
    return result.data[0] if result.data else None

def get_user_by_email(email: str) -> dict:
    sb = get_client()
    result = sb.table("users").select("*").eq("email", email).execute()
    return result.data[0] if result.data else None

def complete_onboarding(user_id: str) -> None:
    sb = get_client()
    sb.table("users").update({"onboarding_completed": True}).eq("id", user_id).execute()

# ─── ANALYSES ────────────────────────────────

def create_analysis(user_id: str, photo_url: str, ankieta: dict) -> dict:
    sb = get_client()
    result = sb.table("analyses").insert({
        "user_id": user_id,
        "photo_url": photo_url,
        "ankieta_json": ankieta,
        "status": "pending"
    }).execute()
    return result.data[0] if result.data else None

def save_ai_analysis(analysis_id: str, ai_result: dict) -> None:
    sb = get_client()
    sb.table("analyses").update({
        "ai_analysis_json": ai_result
    }).eq("id", analysis_id).execute()

def get_pending_analyses() -> list:
    sb = get_service_client()
    result = (
        sb.table("analyses")
        .select("*, users(email, plan)")
        .eq("status", "pending")
        .order("created_at")
        .execute()
    )
    return result.data or []

def approve_analysis(analysis_id: str, korekta: dict = None, komentarz: str = None) -> None:
    sb = get_service_client()
    update_data = {"status": "approved" if not korekta else "corrected"}
    if korekta:
        update_data["stylistka_korekta"] = korekta
    if komentarz:
        update_data["stylistka_komentarz"] = komentarz
    sb.table("analyses").update(update_data).eq("id", analysis_id).execute()

def get_user_analysis(user_id: str) -> dict:
    sb = get_client()
    result = (
        sb.table("analyses")
        .select("*")
        .eq("user_id", user_id)
        .in_("status", ["approved", "corrected"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None

# ─── WARDROBE ────────────────────────────────

def get_wardrobe_count(user_id: str) -> int:
    sb = get_client()
    result = sb.table("wardrobe").select("id", count="exact").eq("user_id", user_id).execute()
    return result.count or 0

def add_wardrobe_item(user_id: str, zdjecie_url: str, opis: str, kategoria: str, kolor: str, plan: str) -> dict | None:
    limit = 12 if plan == "essential" else None
    if limit and get_wardrobe_count(user_id) >= limit:
        return None  # limit osiągnięty
    sb = get_client()
    result = sb.table("wardrobe").insert({
        "user_id": user_id,
        "zdjecie_url": zdjecie_url,
        "opis": opis,
        "kategoria": kategoria,
        "kolor": kolor
    }).execute()
    return result.data[0] if result.data else None

def get_wardrobe(user_id: str) -> list:
    sb = get_client()
    result = sb.table("wardrobe").select("*").eq("user_id", user_id).order("created_at").execute()
    return result.data or []

def get_wardrobe_by_category(user_id: str) -> dict:
    items = get_wardrobe(user_id)
    grouped = {}
    for item in items:
        cat = item.get("kategoria", "inne")
        grouped.setdefault(cat, []).append(item)
    return grouped

# ─── STYLE CASES (RAG) ───────────────────────

def add_style_case(analysis_id: str, analysis_json: dict) -> dict:
    sb = get_service_client()
    result = sb.table("style_cases").insert({
        "typ_sylwetki": analysis_json.get("typ_sylwetki"),
        "kolorystyka": analysis_json.get("kolorystyka"),
        "proporcje": analysis_json.get("proporcje"),
        "rekomendacje": analysis_json.get("rekomendacje_ogolne"),
        "czego_unikac": analysis_json.get("czego_unikac"),
        "tagi": analysis_json.get("tagi", []),
        "zrodlo_analysis_id": analysis_id
    }).execute()
    return result.data[0] if result.data else None

def get_similar_cases(body_type: str, style_tags: list, limit: int = 5) -> list:
    sb = get_client()
    result = (
        sb.table("style_cases")
        .select("*")
        .eq("typ_sylwetki", body_type)
        .limit(limit)
        .execute()
    )
    return result.data or []

# ─── STORAGE ─────────────────────────────────

def upload_photo(bucket: str, path: str, file_bytes: bytes, content_type: str = "image/jpeg") -> str:
    sb = get_service_client()
    sb.storage.from_(bucket).upload(path, file_bytes, {"content-type": content_type})
    result = sb.storage.from_(bucket).get_public_url(path)
    return result

def upload_sylwetka(user_id: str, file_bytes: bytes) -> str:
    path = f"{user_id}/sylwetka.jpg"
    return upload_photo("sylwetki", path, file_bytes)

def upload_wardrobe_item(user_id: str, item_id: str, file_bytes: bytes) -> str:
    path = f"{user_id}/{item_id}.jpg"
    return upload_photo("szafa", path, file_bytes)

# ─── STYLIZATIONS ────────────────────────────

def save_stylization(user_id: str, typ: str, items: list, miesiac: str) -> dict:
    sb = get_service_client()
    result = sb.table("stylizations").insert({
        "user_id": user_id,
        "typ": typ,
        "items": items,
        "miesiac": miesiac,
        "zatwierdzona": False
    }).execute()
    return result.data[0] if result.data else None

def get_user_stylizations(user_id: str, typ: str = None) -> list:
    sb = get_client()
    query = sb.table("stylizations").select("*").eq("user_id", user_id).eq("zatwierdzona", True)
    if typ:
        query = query.eq("typ", typ)
    result = query.order("created_at", desc=True).execute()
    return result.data or []
