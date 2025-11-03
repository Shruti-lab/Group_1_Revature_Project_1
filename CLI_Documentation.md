# TaskFlow CLI Documentation

This document explains how to use the TaskFlow CLI tool built using Python and Click framework. The CLI interacts with a Flask-based backend API for authentication and task management.

---
## ✅ *Setup Instructions*
1. Ensure backend API is running at:
   
   http://127.0.0.1:5000
   
2. Install dependencies:
   bash
   pip install click requests
   
3. Run the CLI file:
   bash
   python -m app.cli <command>
   

---
# ✅ *Authentication Commands*

### *1. Sign Up*
Register a new user
bash
python -m app.cli signup --name "John Doe" --email "john@example.com" --password "123456"

*Response:* JSON message confirming account creation.

---
### *2. Login*
Login and store JWT token in token.txt
bash
python -m app.cli login --email "john@example.com" --password "123456"

✅ If successful: Login successful. Token saved.

---
### *3. Current User*
Fetch logged-in user profile
bash
python -m app.cli current-user


---
### *4. Update Profile*
Update name and/or password
bash
python -m app.cli update-user --name "New Name" --password "newpass123"


---
# ✅ *Task Commands*

### *5. Create Task*
bash
python -m app.cli create-task

CLI will prompt for:
- Title
- Description
Optional:
- --status (PENDING, IN_PROGRESS…)
- --priority
- --due_date YYYY-MM-DD
- --start_date YYYY-MM-DD

Example:
bash
python -m app.cli create-task --status COMPLETED --priority HIGH --due_date 2026-01-20


---
### *6. List All Tasks (with filters & pagination)*
bash
python -m app.cli list --status PENDING --priority HIGH --search "report" --page 1 --per-page 5

All options are optional.

---
### *7. Get Single Task*
bash
python -m app.cli get-task 4

Fetches task with ID = 4

---
### *8. Overdue Tasks*
bash
python -m app.cli overdue-tasks

Shows tasks whose due date passed.

---
### *9. Today’s Tasks*
bash
python -m app.cli todays-tasks


---
### *10. Task Statistics*
bash
python -m app.cli stat-tasks

Returns summary count of tasks by status & priority.

---
### *11. Recent Tasks*
bash
python -m app.cli recent-tasks --limit 10


---
### *12. Upcoming Tasks*
bash
python -m app.cli upcoming-tasks


---
### *13. Update Task*
bash
python -m app.cli update-task 3 --title "New Title" --priority HIGH --due_date 2025-02-01

Updates only provided fields.

---
### *14. Delete a Task*
bash
python -m app.cli delete-task 3

Prompts confirmation before deletion.

---
### *15. Bulk Delete Tasks*
bash
python -m app.cli bulk-delete --ids 2 5 7

Deletes multiple tasks at once.

---
## ✅ TOKEN HANDLING
Token is stored in:

token.txt

If token missing, CLI asks to login first.

---
## ✅ Error Handling
- If server unreachable → shows connection error
- If token invalid → backend returns unauthorized message
- If update has no fields → prints: Nothing to update.

---
## ✅ Conclusion
TaskFlow CLI provides full task lifecycle: create, list, update, filter, stats, delete & bulk delete. It can replace frontend UI for developers or automation.