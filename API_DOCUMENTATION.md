# API Documentation

## Table of Contents
- [Overview](#overview)
- [Application Base URL](#application-base-url)
- [Authentication](#authentication)
- [Response Formats](#response-formats)
- [Error Codes](#error-codes)
- [Endpoints](#endpoints)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Management Endpoints](#user-management-endpoints)
  - [Task Management Endpoints](#task-management-endpoints)
    
---

## Overview

TaskFlow API is a RESTful task management system that allows users to create, manage, and organize their tasks. The API supports user authentication, task CRUD operations, filtering, pagination, and bulk operations.

**Version:** 1.0.0  
**Last Updated:** October 31, 2025

---

## Application Base URL

```
http://localhost:5000
```

## Response Formats

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "details": { ... }
}
```

### Paginated Response

```json
{
  "success": true,
  "message": "Success message",
  "data": {
    "tasks": [...],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total_items": 50,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## Error Codes

| Status Code | Meaning |
|------------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---


# User Signup and authentication endpoints

## User authentication ase URL

```
http://localhost:5000/auth
```

## Authentication

TaskFlow API uses **JWT (JSON Web Token)** for authentication.

### Getting a Token

1. Sign up then log in to receive an access token.
2. Include the token in the `Authorization` header for protected endpoints

### Header Format

```
Authorization: Bearer <your_access_token>
```

### Token Expiration

Tokens expire after 1 hour. You'll need to log in again to get a new token.

---

## Endpoints

## Authentication Endpoints

### 1. Sign Up

Create a new user account.

**Endpoint:** `POST [http://127.0.0.1:5000/auth/signup](http://127.0.0.1:5000/auth/signup)`

**Authentication Required:** No

**Request Body:**
```json
{
    "name":"Perry",
    "email":"perry@gmail.com",
    "password":"perryperry"
}
```

**Validation Rules:**
- `name`: Required, 3-100 characters
- `email`: Required, valid email format
- `password`: Required, minimum 6 characters, must contain uppercase, lowercase, and number

**Success Response:** `201 Created`
```json
{
    "message": "User registered successfully"
}
```

**Error Responses:**

`400 Bad Request` - Email already exists
```json
{
    "message": "Email already registered"
}
```

`400 Bad Request` - Validation error
```json
{
    "errors": [
        {
            "ctx": {
                "min_length": 6
            },
            "input": "p",
            "loc": [
                "password"
            ],
            "msg": "String should have at least 6 characters",
            "type": "string_too_short",
            "url": "https://errors.pydantic.dev/2.12/v/string_too_short"
        }
    ]
}
```

---

### 2. Login

Authenticate and receive an access token.

**Endpoint:** `POST [http://127.0.0.1:5000/auth/login](http://127.0.0.1:5000/auth/login)`

**Authentication Required:** No

**Request Body:**
```json
{
    "email":"perry@gmail.com",
    "password":"perryperry"
}
```

**Success Response:** `200 OK`
```json
{
    "access_token": "access token....",
    "message": "Login successful",
    "user": {
        "email": "perry@gmail.com",
        "name": "Perry",
        "user_id": 3
    }
}
```

**Error Response:** `401 Unauthorized`
```json
{
    "message": "Invalid email or password"
}
```

---

## User Management Endpoints

### 3. Get Current User Profile

Get the authenticated user's profile information.

**Endpoint:** `GET /auth/user`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response:** `200 OK`
```json
{
  "user_id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

**Error Response:** `404 Not Found`
```json
{
  "message": "User not found"
}
```

---

### 4. Update Current User Profile

Update the authenticated user's profile.

**Endpoint:** `PUT /auth/user`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "password":"PeryPery"
}
```

**Note:** One can update name or password for a user. Both fields are optional. Include only the fields you want to update.

**Success Response:** `200 OK`
```json
{
    "message": "User updated successfully"
}
```

**Missing Authorozation token response:** `401 Unauthorized`
```json
{
    "msg": "Missing Authorization Header"
}
```


---

### 5. Get Current User Profile

Get the authenticated user's profile.

**Endpoint:** `PUT [http://127.0.0.1:5000/auth/user](http://127.0.0.1:5000/auth/user)`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
None

**Success Response:** `200 OK`
```json
{
    "email": "perry@gmail.com",
    "name": "Perry",
    "user_id": 3
}
```

**Missing Authorozation token response:** `401 Unauthorized`
```json
{
    "msg": "Missing Authorization Header"
}
```


---


# Task flow API Endpoints

## Base URL

```
http://localhost:5000/user/tasks
```

---

## Task Management Endpoints

### 5. Get All Tasks (with Filtering & Pagination)

Retrieve all tasks for the authenticated user with optional filters.

**Endpoint:** `GET /user/tasks`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `status` | string | No | Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED) | - |
| `priority` | string | No | Filter by priority (LOW, MEDIUM, HIGH) | - |
| `search` | string | No | Search in title and description | - |
| `page` | integer | No | Page number | 1 |
| `per_page` | integer | No | Items per page (max: 100) | 5 |

**Example Requests:**

***Get all tasks:***

*Request:*
```
GET [http://127.0.0.1:5000/user/tasks](http://127.0.0.1:5000/user/tasks)
```

*Success Response:* `200 OK`
```json
{
    "data": {
        "pagination": {
            "has_next": true,
            "has_prev": false,
            "page": 1,
            "per_page": 5,
            "total_items": 7,
            "total_pages": 2
        },
        "tasks": [
            {
                "description": "Finish slides and demo",
                "due_date": "2025-11-20",
                "is_overdue": false,
                "priority": "LOW",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 3,
                "title": "Prepare Project file",
                "user_id": 3
            },
            {
                "description": "Gather receipts and submit for approval",
                "due_date": "2025-12-01",
                "is_overdue": false,
                "priority": "MEDIUM",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 4,
                "title": "Submit Expense Report",
                "user_id": 3
            },
            {
                "description": "Discuss Q4 goals and assign action items",
                "due_date": "2025-11-25",
                "is_overdue": false,
                "priority": "HIGH",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 5,
                "title": "Team Meeting",
                "user_id": 3
            }
        ]
    },
    "message": "Tasks retrieved successfully",
    "success": true
}
```

***Filter by status:***

*Request:*
```
GET [http://127.0.0.1:5000/user/tasks?status=pending](http://127.0.0.1:5000/user/tasks?status=pending)
```

*Success Response:* `200 OK`
```json
{
    "data": {
        "pagination": {
            "has_next": true,
            "has_prev": false,
            "page": 1,
            "per_page": 5,
            "total_items": 7,
            "total_pages": 2
        },
        "tasks": [
            {
                "description": "Finish slides and demo",
                "due_date": "2025-11-20",
                "is_overdue": false,
                "priority": "LOW",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 4,
                "title": "Prepare Project file",
                "user_id": 3
            },
            {
                "description": "Finish slides and demo",
                "due_date": "2025-11-20",
                "is_overdue": false,
                "priority": "LOW",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 6,
                "title": "Prepare Project file",
                "user_id": 3
            },
            {
                "description": "Gather receipts and submit for approval",
                "due_date": "2025-12-01",
                "is_overdue": false,
                "priority": "MEDIUM",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 7,
                "title": "Submit Expense Report",
                "user_id": 3
            },
            {
                "description": "Discuss Q4 goals and assign action items",
                "due_date": "2025-11-25",
                "is_overdue": false,
                "priority": "HIGH",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 8,
                "title": "Team Meeting",
                "user_id": 3
            }
        ]
    },
    "message": "Tasks retrieved successfully",
    "success": true
}
```


***Filter by priority:***
```
GET [http://127.0.0.1:5000/user/tasks?priority=high](http://127.0.0.1:5000/user/tasks?priority=high)
```

*Success Response:* `200 OK`
```json
{
    "data": {
        "pagination": {
            "has_next": false,
            "has_prev": false,
            "page": 1,
            "per_page": 5,
            "total_items": 1,
            "total_pages": 1
        },
        "tasks": [
            {
                "description": "Discuss Q4 goals and assign action items",
                "due_date": "2025-11-25",
                "is_overdue": false,
                "priority": "HIGH",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 8,
                "title": "Team Meeting",
                "user_id": 3
            }
        ]
    },
    "message": "Tasks retrieved successfully",
    "success": true
}
```

***Search tasks:***
```
GET [http://127.0.0.1:5000/user/tasks?search=goals](http://127.0.0.1:5000/user/tasks?search=goals)
```

*Success Response:* `200 OK`
```json
{
    "data": {
        "pagination": {
            "has_next": false,
            "has_prev": false,
            "page": 1,
            "per_page": 5,
            "total_items": 1,
            "total_pages": 1
        },
        "tasks": [
            {
                "description": "Discuss Q4 goals and assign action items",
                "due_date": "2025-11-25",
                "is_overdue": false,
                "priority": "HIGH",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 8,
                "title": "Team Meeting",
                "user_id": 3
            }
        ]
    },
    "message": "Tasks retrieved successfully",
    "success": true
}
```


***With pagination:***
```
GET [http://127.0.0.1:5000/user/tasks?page=2&per_page=2](http://127.0.0.1:5000/user/tasks?page=2&per_page=2)
```

*Success Response:* `200 OK`
```json
{
    "data": {
        "pagination": {
            "has_next": true,
            "has_prev": true,
            "page": 2,
            "per_page": 2,
            "total_items": 7,
            "total_pages": 4
        },
        "tasks": [
            {
                "description": "Finish slides and demo",
                "due_date": "2025-11-20",
                "is_overdue": false,
                "priority": "LOW",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 6,
                "title": "Prepare Project file",
                "user_id": 3
            },
            {
                "description": "Gather receipts and submit for approval",
                "due_date": "2025-12-01",
                "is_overdue": false,
                "priority": "MEDIUM",
                "start_date": "2025-10-31",
                "status": "PENDING",
                "task_id": 7,
                "title": "Submit Expense Report",
                "user_id": 3
            }
        ]
    },
    "message": "Tasks retrieved successfully",
    "success": true
}
```



**Error Responses:**

`400 Bad Request` - Invalid status
```json
{
  "success": false,
  "error": "Invalid status. Must be one of: ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']"
}
```

`400 Bad Request` - Invalid priority
```json
{
  "success": false,
  "error": "Invalid priority. Must be one of: ['LOW', 'MEDIUM', 'HIGH']"
}
```

---

### 6. Get Single Task

Retrieve a specific task by ID.

**Endpoint:** `GET [http://127.0.0.1:5000/user/tasks/<task_id>](http://127.0.0.1:5000/user/tasks/{{task_id}})`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**URL Parameters:**
- `task_id` (integer): The ID of the task

**Example Request:**
```
GET [http://127.0.0.1:5000/user/tasks/7](http://127.0.0.1:5000/user/tasks/7)
```

**Success Response:** `200 OK`
```json
{
    "data": {
        "description": "Gather receipts and submit for approval",
        "due_date": "2025-12-01",
        "is_overdue": false,
        "priority": "MEDIUM",
        "start_date": "2025-10-31",
        "status": "PENDING",
        "task_id": 7,
        "title": "Submit Expense Report",
        "user_id": 3
    },
    "message": "Task fetched successfully",
    "success": true
}
```

**Error Response:** `404 Not Found`
```json
{
    "error": "Task not found",
    "success": false
}
```

---

### 7. Create Task

Create a new task.

**Endpoint:** `POST [http://127.0.0.1:5000/user/tasks](http://127.0.0.1:5000/user/tasks)`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "title": "Code Review",
    "description": "Review pull requests for the new feature branch",
    "status": "PENDING",
    "priority": "MEDIUM",
    "due_date": "2025-12-07"
}
```

**Field Details:**

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `title` | string | Yes | Task title (1-200 chars) | - |
| `description` | string | No | Task description | null |
| `status` | string | No | PENDING, IN_PROGRESS, COMPLETED, CANCELLED | PENDING |
| `priority` | string | No | LOW, MEDIUM, HIGH | LOW |
| `start_date` | date | No | Task start date (YYYY-MM-DD) | Current date |
| `due_date` | date | No | Task due date (YYYY-MM-DD) | null |

**Success Response:** `201 Created`
```json
{
    "data": {
        "description": "Review pull requests for the new feature branch",
        "due_date": "2025-12-07",
        "is_overdue": false,
        "priority": "MEDIUM",
        "start_date": "2025-10-31",
        "status": "PENDING",
        "task_id": 11,
        "title": "Code Review",
        "user_id": 3
    },
    "message": "Task created successfully",
    "success": true
}
```

**Error Responses:**

`400 Bad Request` - Validation error
```json
{
  "success": false,
  "error": "1 validation error for TaskCreateSchema\ntitle\n  Field required [type=missing, input_value={...}, input_type=dict]"
}
```

`400 Bad Request` - Due date in the past
```json
{
    "error": "1 validation error for TaskCreateSchema\ndue_date\n  Value error, Due date cannot be in the past. [type=value_error, input_value='2025-01-07', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.12/v/value_error",
    "success": false
}
```

---

### 8. Update Task

Update an existing task.

**Endpoint:** `PUT [http://127.0.0.1:5000/user/tasks/<task_id>](http://127.0.0.1:5000/user/tasks/{{task_id}})`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**URL Parameters:**
- `task_id` (integer): The ID of the task to update

**Request Body:**
One can edit title, description, status, priority, due_date
```json
{
    "title": "Second project doing",
    "description": "We now need to do 2nd project be ready",
    "status":"COMPLETED"
}
```

**Note:** All fields are optional. Include only the fields you want to update.

**Success Response:** `200 OK`
```json
{
    "data": {
        "description": "We now need to do 2nd project be ready",
        "due_date": "2025-12-01",
        "is_overdue": false,
        "priority": "MEDIUM",
        "start_date": "2025-10-31",
        "status": "COMPLETED",
        "task_id": 7,
        "title": "Second project doing",
        "user_id": 3
    },
    "message": "Task updated successfully",
    "success": true
}
```

**Error Responses:**

`404 Not Found`
```json
{
  "success": false,
  "error": "Task not found"
}
```

`400 Bad Request` - Validation error example for wrong status field provided
```json
{
    "details": [
        {
            "field": "status",
            "message": "Value error, Status must be one of: ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']",
            "type": "value_error"
        }
    ],
    "error": "Validation failed",
    "success": false
}
```

---

### 9. Delete Task

Delete a specific task.

**Endpoint:** `DELETE [http://127.0.0.1:5000/user/tasks/<task_id>](http://127.0.0.1:5000/user/tasks/{{task_id}})`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**URL Parameters:**
- `task_id` (integer): The ID of the task to delete

**Example Request:**
```
DELETE [http://127.0.0.1:5000/user/tasks/12](http://127.0.0.1:5000/user/tasks/12)
```

**Success Response:** `200 OK`
```json
{
    "message": "Task deleted successfully",
    "success": true
}
```

**Error Response:** `404 Not Found`
```json
{
    "error": "Task not found",
    "success": false
}
```

---

### 10. Bulk Delete Tasks

Delete multiple mentioned tasks at once.

**Endpoint:** `DELETE [http://127.0.0.1:5000/user/tasks/bulk_delete?task_ids=<ids>](http://127.0.0.1:5000/user/tasks/bulk_delete?task_ids={{ids}})`

**Authentication Required:** Yes

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `task_ids` (string): Comma-separated list of task IDs

**Example Request:**
```
DELETE [http://127.0.0.1:5000/user/tasks/bulk_delete?task_ids=13,14,15](http://127.0.0.1:5000/user/tasks/bulk_delete?task_ids=13,14,15)
```

**Success Response:** `200 OK`
```json
{
    "message": "Deleted 3 tasks",
    "success": true
}
```

**Error Responses:**

`400 Bad Request` - Missing task_ids
```json
{
    "error": "task_ids query parameter required",
    "success": false
}
```

`404 Not Found` - No valid tasks found
```json
{
    "error": "No valid tasks found to delete",
    "success": false
}
```

---

## Data Models

### User Model

```json
{
  "user_id": integer,
  "name": string,
  "email": string,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Task Model

```json
{
  "task_id": integer,
  "title": string,
  "description": string,
  "start_date": date,
  "due_date": date,
  "priority": enum ["LOW", "MEDIUM", "HIGH"],
  "status": enum ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
  "user_id": integer,
  "is_overdue": boolean
}
```

---

## Enums

### Task Status
- `PENDING` - Task not started
- `IN_PROGRESS` - Task is being worked on
- `COMPLETED` - Task finished
- `CANCELLED` - Task cancelled

### Task Priority
- `LOW` - Low priority
- `MEDIUM` - Medium priority
- `HIGH` - High priority

---

## Example Workflows


### Complete User Journey

#### 1. Register a new user
```bash
curl -X POST http://localhost:5000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

#### 2. Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

Response includes `access_token` - save this for subsequent requests.

#### 3. Create a task
```bash
curl -X POST http://localhost:5000/user/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "title": "Complete Project",
    "description": "Finish the TaskFlow API",
    "priority": "HIGH",
    "due_date": "2025-11-15"
  }'
```

#### 4. Get all high priority tasks
```bash
curl -X GET "http://localhost:5000/user/tasks?priority=HIGH" \
  -H "Authorization: Bearer <your_token>"
```

#### 5. Update task status
```bash
curl -X PUT http://localhost:5000/user/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "status": "COMPLETED"
  }'
```

#### 6. Delete completed tasks
```bash
curl -X DELETE "http://localhost:5000/user/tasks/bulk_delete?task_ids=1,2,3" \
  -H "Authorization: Bearer <your_token>"
```

---

## Rate Limiting

Currently, there are no rate limits implemented. This will be added in future versions.

---

## Changelog

### Version 1.0.0 (October 31, 2025)
- Initial release
- User authentication with JWT
- Full CRUD operations for tasks
- Task filtering by status and priority
- Search functionality
- Pagination support
- Bulk delete operations

---

## License

MIT License - See LICENSE file for details
