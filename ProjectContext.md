# PROJECT CONTEXT: HR Hiring System

## 1. Project Overview:

A pet project for system integration: "HR Hiring System".
The frontend consists of two forms (Candidate and HR) located in the same browser tab, switchable via buttons. 
The backend server hosts the database logic.

## 2. Core Process:

The Candidate submits data, which the system saves to the Applications table. These applications are displayed to the HR specialist, who makes a decision: "Hire" or "Reject".

    If "Hire": Status becomes "Hired", and the linked Position is marked as no longer free.
    If "Reject": Status becomes "Canceled" (Soft Delete, record is kept for history).

## 1. Candidate Form Logic
Fields (All mandatory):

    full_name   (String)
    email       (String)
    position_id (Dropdown: fetches pos_name from Positions table, but sends the id to the server)
    educ        (String)
    experience  (String)
    birth_date  (Date)

UI Actions:

    Button "Fill with test data" (bottom left, next to "Submit"). 
        Action: Client-side only. Fills fields with: 
            full_name = "Sinitsyn Petr Igorevich"
            email = "SPI@example.com"
            position_id = First available position from the dropdown
            educ = "Higher Education"
            experience = "3 years"
            birth_date = "1992-02-29"
    Button "Submit". Sends POST request to server.

Server Response Handling:

    If HTTP 201 Created: Show message "Data submitted successfully."
    If Error (e.g., 409 or 500): Show message "Data not submitted. Please try again later. Error code: [XXX]."

## 2. Backend Logic & Database Schema
ID Generation: Use standard UUID for all id fields (generated automatically by DB/Backend).
Table: Positions

    id          (UUID, Primary Key)
    pos_name    (String)
    is_free     (Boolean, default True)

Table: Applications

    id          (UUID, Primary Key)
    position_id (UUID, Foreign Key referencing Positions.id. Note: UI displays pos_name, but DB stores position_id)
    app_date    (DateTime)
    educ        (String)
    experience  (String)
    full_name   (String)
    email       (String)
    birth_date  (Date)
    status      (String, Enum: "New", "Hired", "Canceled")

## 2.1 Endpoint Logic: POST /api/applications

    Receive data from form.
    Search in "Applications" table for a record where:
        "email" equals received "email"
        AND "position_id" equals received "position_id".

    If such a record is found, Then
        If "status" equals "New" OR "status" equals "Hired", Then
            Return HTTP 409 Conflict: "You have already applied for this position."
        Else // If "status" equals "Canceled"
            Create a new record in "Applications" (old record is kept for history):
                - Assign new UUID "id"
                - Record current "app_date"
                - Record data from form
                - Set "status" to "New"
            Return HTTP 201 Created.
        EndIf
    Else // Record not found
        Create a new record in "Applications":
            - Assign new UUID "id"
            - Record current ""app_date"
            - Record data from form
            - Set "status" to "New"
        Return HTTP 201 Created.
    EndIf

## 2.2 Demo Data Collections (For Reset Endpoint):

    PositionDemoCollection: 
        pos_name = ["Analyst", "Team Lead", "Head of Development"]
        is_free = [True, True, True]
    ApplicationDemoCollection: 
        full_name = ["Petrov Alexander Vitalievich", "Aleshin Petr Mikhailovich", "Sirotkin Nikita Vyacheslavovich"]
        email = ["Enter email for test", "Enter email for test", "Enter email for test"]
        educ = ["Higher. Bachelor", "Higher. Master", "Higher. PhD"]
        experience = ["3 years", "5 years", "7 years"]
        birth_date = ["1994-06-02", "1992-07-03", "1990-09-05"]
        status = ["New", "New", "New"]

## 3. HR Form Logic
## 3.1 UI Layout (Top to Bottom):

    Refresh Block: "Refresh" button (top right).
    Filter Block: 
        Checkbox + Input for "Position" (pos_name).
        Checkbox + Input for "Full Name" (full_name).
    Candidates Table Block: 
        Header: "Candidates".
        Columns: Position, Education, Experience, Full Name, Email.
        Crucial: The email cell in each row must be inline editable. HR can click, type a real email, and press Enter or click away to save.
    Positions Table Block: 
        Header: "Company Positions".
        Input row: pos_name (String), is_free (Boolean).
        Button: "Add" (sends POST to create new position).
    Control Block (Bottom):
        Left: Input field "Support Email" (String, always available).
        Center: Button "Reset & Load Demo Data".
        Right: Buttons "Hire" and "Reject" (Disabled by default).

## 3.2 Logic: "Reset & Load Demo Data" Button

1. Browser sends POST request to reset endpoint.
2. Server deletes all records from "Applications".
3. If "Positions" table is empty, server seeds it with `PositionDemoCollection`.
4. Server creates 3 new records in "Applications" using `ApplicationDemoCollection` (assigning valid `position_id`s).
5. Server returns "Success".
6. Frontend auto-refreshes the Candidates table.
7. Frontend displays a hint: "To test email sending, please edit the placeholder emails in the Candidates table."

## 3.3 Logic: "Refresh" Button

    Create empty object `RespParam`.
    If Checkbox "Position" is True AND Input "Position" is not empty, Then
        Add "position" filter to `RespParam`.
    EndIf
    If Checkbox "Full Name" is True AND Input "Full Name" is not empty, Then
        Add "full_name" filter to `RespParam`.
    EndIf

    Send GET request to server with `RespParam`.
    If data is received successfully:
        If data is parsed correctly:
            If record is "New":
                Add new row to table.
            Else:
                Update existing row by matching "id".
        Else:
            Show error: "Failed to parse data. Code XXX".
    Else:
        Show error: "Error receiving data. Code XXX".

## 3.4 Logic: Row Selection & Actions

    If user selects a row in Candidates table:
        Enable "Hire" and "Reject" buttons.
    If user deselects the row:
        Disable "Hire" and "Reject" buttons.

## 3.5 Logic: "Reject" Button        

    Get the `email` from the selected (and potentially edited) row.
    // Validation: If email does not contain "@", skip sending and show warning "Invalid email, email not sent".
    If valid:
        Send email via Brevo to `email` with text: "Sorry, your application is not a fit for us. Have a good day."
    Update record "status" to "Canceled".

## 3.6 Logic: "Hire" Button

    Get the `email` from the selected (and potentially edited) row.
    Get the `support_email` from the Support Email input field.
    // Validation: If candidate `email` does not contain "@", skip candidate email and show warning.

    If candidate `email` is valid:
        Send email via Brevo to candidate `email`: "Congratulations, you are hired! Come work with us."

    If `support_email` is valid:
        Send email via Brevo to `support_email`: "New employee [full_name] hired. Please prepare a workplace."

    Update record "status" to "Hired".
    Find the linked record in "Positions" table via `position_id` and set `is_free` to False.