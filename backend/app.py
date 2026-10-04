from flask import Flask, request, jsonify
from flask_cors import CORS

from auth import (
    verify_google_token,
    upsert_profile,
    create_app_token,
    auth_required,
)
from database import supabase
from gmail_service import send_task_created_email, send_task_completed_email
from services.task_service import (
    list_users,
    list_tasks,
    create_task,
    complete_task,
    get_profile,
)

app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/auth/google")
def google_login():
    data = request.get_json(silent=True) or {}
    google_token = data.get("credential")

    if not google_token:
        return jsonify({"error": "Google credential is required"}), 400

    try:
        google_user = verify_google_token(google_token)

        if not google_user.get("email_verified", False):
            return jsonify({"error": "Google email is not verified"}), 401

        profile = upsert_profile(google_user)
        token = create_app_token(profile)

        return jsonify(
            {
                "token": token,
                "user": profile,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 401


@app.get("/api/users")
@auth_required
def users(current_user):
    return jsonify({"users": list_users(current_user["sub"])})


@app.get("/api/tasks")
@auth_required
def tasks(current_user):
    return jsonify({"tasks": list_tasks(current_user["sub"])})


@app.post("/api/tasks")
@auth_required
def create_task_endpoint(current_user):
    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    assigned_to = data.get("assigned_to")

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if not assigned_to:
        return jsonify({"error": "Please select an assignee"}), 400

    if len(title) > 200:
        return jsonify({"error": "Task title is too long"}), 400

    try:
        task, assignee = create_task(
            title,
            description,
            current_user["sub"],
            assigned_to,
        )

        email_status = "not_sent"
        email_error = None

        try:
            send_task_created_email(task, assignee)
            email_status = "sent"
        except Exception as exc:
            email_status = "failed"
            email_error = str(exc)

        return jsonify(
            {
                "task": task,
                "notification": {
                    "status": email_status,
                    "error": email_error,
                },
            }
        ), 201

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.patch("/api/tasks/<task_id>/complete")
@auth_required
def complete_task_endpoint(current_user, task_id):
    try:
        task = complete_task(task_id, current_user["sub"])

        email_status = "not_sent"
        email_error = None

        try:
            creator = get_profile(task["created_by"])
            if creator and creator["id"] != current_user["sub"]:
                send_task_completed_email(task, creator)
                email_status = "sent"
            else:
                email_status = "skipped"
        except Exception as exc:
            email_status = "failed"
            email_error = str(exc)

        return jsonify(
            {
                "task": task,
                "notification": {
                    "status": email_status,
                    "error": email_error,
                },
            }
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
