from datetime import datetime, timezone
from firestore_db import get_db

DEMO_USER_ID = "demo_user"


def save_profile(profile: dict):
    db = get_db()
    doc_ref = db.collection("users").document(DEMO_USER_ID).collection("data").document("profile")
    doc_ref.set(
        {
            **profile,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        merge=True,
    )


def load_profile() -> dict:
    db = get_db()
    doc_ref = db.collection("users").document(DEMO_USER_ID).collection("data").document("profile")
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else {}


def save_alerts(alerts: list[dict]):
    db = get_db()
    base = db.collection("users").document(DEMO_USER_ID).collection("alerts")

    # write each alert as its own document (id must exist)
    for a in alerts:
        aid = a.get("id")
        if not aid:
            continue
        base.document(aid).set(
            {
                **a,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            merge=True,
        )


def load_alerts() -> list[dict]:
    db = get_db()
    base = db.collection("users").document(DEMO_USER_ID).collection("alerts")
    docs = base.stream()
    out = []
    for d in docs:
        data = d.to_dict()
        if data:
            out.append(data)
    return out


def save_resolved_ids(resolved_ids: set[str]):
    db = get_db()
    doc_ref = db.collection("users").document(DEMO_USER_ID).collection("data").document("state")
    doc_ref.set({"resolved_alert_ids": list(resolved_ids)}, merge=True)


def load_resolved_ids() -> set[str]:
    db = get_db()
    doc_ref = db.collection("users").document(DEMO_USER_ID).collection("data").document("state")
    doc = doc_ref.get()
    if not doc.exists:
        return set()
    data = doc.to_dict() or {}
    return set(data.get("resolved_alert_ids", []))
