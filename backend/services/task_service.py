from datetime import datetime, timezone
from database import supabase


def get_profile(profile_id):
    result = (
        supabase.table("profiles")
        .select("*")
        .eq("id", profile_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def list_users(exclude_id=None):
    query = supabase.table("profiles").select("id,email,full_name,avatar_url").order("full_name")
    if exclude_id:
        query = query.neq("id", exclude_id)
    return query.execute().data or []


def list_tasks(user_id):
    result = (
        supabase.table("tasks")
        .select(
            "id,title,description,completed,completed_at,created_at,updated_at,"
            "created_by,assigned_to,"
            "creator:profiles!tasks_created_by_fkey(id,email,full_name),"
            "assignee:profiles!tasks_assigned_to_fkey(id,email,full_name)"
        )
        .or_(f"created_by.eq.{user_id},assigned_to.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def create_task(title, description, creator_id, assignee_id):
    assignee = get_profile(assignee_id)
    if not assignee:
        raise ValueError("Assigned user does not exist")

    result = (
        supabase.table("tasks")
        .insert(
            {
                "title": title.strip(),
                "description": description.strip(),
                "created_by": creator_id,
                "assigned_to": assignee_id,
            }
        )
        .execute()
    )

    if not result.data:
        raise RuntimeError("Task creation failed")

    return result.data[0], assignee


def complete_task(task_id, user_id):
    current = (
        supabase.table("tasks")
        .select("*")
        .eq("id", task_id)
        .limit(1)
        .execute()
    )

    if not current.data:
        raise ValueError("Task not found")

    task = current.data[0]

    if task["assigned_to"] != user_id and task["created_by"] != user_id:
        raise PermissionError("You cannot complete this task")

    if task["completed"]:
        return task

    result = (
        supabase.table("tasks")
        .update(
            {
                "completed": True,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", task_id)
        .execute()
    )

    if not result.data:
        raise RuntimeError("Task completion failed")

    return result.data[0]
