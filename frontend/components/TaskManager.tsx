/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useCallback, useEffect, useState } from "react";
import AuthButton from "./AuthButton";
import {
  createTask,
  completeTask,
  getTasks,
  getUsers,
} from "@/lib/api";

type User = {
  id: string;
  email: string;
  full_name: string;
};

type Task = {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;
  created_by: string;
  assigned_to: string;
  creator?: User;
  assignee?: User;
};

export default function TaskManager() {
  const [user, setUser] = useState<any>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [taskData, userData] = await Promise.all([getTasks(), getUsers()]);
      setTasks(taskData.tasks || []);
      setUsers(userData.users || []);
      setError("");
    } catch (err: any) {
      setError(err.message || "Unable to load data");
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("task_manager_user");
    const token = localStorage.getItem("task_manager_token");

    if (stored && token) {
      setUser(JSON.parse(stored));
      loadData();
    }
  }, [loadData]);

  const handleLogin = useCallback(
    (data: any) => {
      setUser(data.user);
      setMessage("Logged in successfully.");
      loadData();
    },
    [loadData]
  );

  const logout = () => {
    localStorage.removeItem("task_manager_token");
    localStorage.removeItem("task_manager_user");
    setUser(null);
    setTasks([]);
    setUsers([]);
    setMessage("");
  };

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!title.trim() || !assignedTo) {
      setError("Enter a title and select a user.");
      return;
    }

    setLoading(true);
    try {
      const result = await createTask({
        title,
        description,
        assigned_to: assignedTo,
      });

      setTitle("");
      setDescription("");
      setAssignedTo("");
      setMessage(
        result.notification?.status === "sent"
          ? "Task created and email notification sent."
          : "Task created. Email notification could not be sent."
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || "Could not create task");
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (taskId: string) => {
    setError("");
    setMessage("");

    try {
      const result = await completeTask(taskId);
      setMessage(
        result.notification?.status === "sent"
          ? "Task completed and notification sent."
          : "Task completed."
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || "Could not complete task");
    }
  };

  if (!user) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <div className="logo">✓</div>
          <h1>Task Manager</h1>
          <p>Hello, manage your tasks with Google login.</p>
          <AuthButton onLogin={handleLogin} onError={setError} />
          {error && <div className="error">{error}</div>}
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <div >
          <h1>Task Manager</h1>
          <h2>Welcome, {user.full_name}</h2>
        </div>
        <button className="secondary" onClick={logout}>
          Logout
        </button>
      </header>

      {message && <div className="notice">{message}</div>}
      {error && <div className="error">{error}</div>}

      <section className="grid">
        <div className="card">
          <h2>Create Task</h2>
          <form onSubmit={handleCreate}>
            <label>
              Task title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Prepare project report"
                maxLength={200}
              />
            </label>

            <label>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add task details..."
                rows={5}
              />
            </label>

            <label>
              Assign to
              <select
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
              >
                <option value="">Select a user</option>
                {users.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.full_name} — {item.email}
                  </option>
                ))}
              </select>
            </label>

            <button className="primary" disabled={loading}>
              {loading ? "Creating..." : "Create Task"}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title">
            <h2>Your Tasks</h2>
            <button className="small" onClick={loadData}>Refresh</button>
          </div>

          {tasks.length === 0 ? (
            <div className="empty">
              <strong>No tasks yet</strong>
              <span>Create or assign your task.</span>
            </div>
          ) : (
            <div className="tasks">
              {tasks.map((task) => (
                <article className={`task ${task.completed ? "done" : ""}`} key={task.id}>
                  <div>
                    <div className="task-head">
                      <h3>{task.title}</h3>
                      <span className={task.completed ? "badge done-badge" : "badge"}>
                        {task.completed ? "Completed" : "Open"}
                      </span>
                    </div>
                    <p>{task.description || "No description"}</p>
                    <small>
                      Assigned to: {task.assignee?.full_name || "Unknown"}
                    </small>
                  </div>

                  {!task.completed && (
                    <button
                      className="complete"
                      onClick={() => handleComplete(task.id)}
                    >
                      Mark complete
                    </button>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
