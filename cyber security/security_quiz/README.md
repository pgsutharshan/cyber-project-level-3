# Security Awareness Quiz System

A beginner-friendly cybersecurity awareness application built with Flask, MySQL, Bootstrap, HTML, CSS, and JavaScript. Users can take randomized quizzes and review their results; administrators can manage the question bank and inspect recent quiz attempts.

## Project Abstract

The Security Awareness Quiz System provides a local web-based way to assess and reinforce practical cybersecurity habits. It authenticates users, serves multiple-choice questions, calculates and records results, and gives administrators protected question-management tools.

## Introduction and Objectives

People are often the first line of defense against phishing, weak credentials, malware, and social engineering. This system turns common security guidance into short quizzes and gives learners a simple record of progress.

- Provide secure registration, login, logout, and role-based access.
- Assess knowledge across common cybersecurity topics.
- Explain answers and present practical post-quiz tips.
- Track quiz attempts and summarize awareness progress.
- Let authenticated administrators maintain question content.

## Technologies and Requirements

- Python 3.10 or later, Flask, Werkzeug, `mysql-connector-python`
- XAMPP for local MySQL/MariaDB; Apache is optional because Flask serves the app
- HTML5, CSS3, Bootstrap 5, and vanilla JavaScript
- VS Code and a modern browser

## Modules

- Authentication: validated registration, Werkzeug password hashes, signed Flask sessions.
- Learner dashboard: attempt count, latest result, average, awareness level, and recent history.
- Quiz: up to ten randomized questions, automatic scoring, answer explanations, and tips.
- History: the signed-in learner's recorded attempts.
- Admin dashboard: user/question/attempt counts, average score, and latest results.
- Question CRUD: admin-only create, read, update, and POST-only delete operations.

## Database Design

`users` stores identity, unique email, password hash, role, and account creation time. `questions` stores each prompt, four choices, answer key, and explanation. `quiz_results` stores user, score, question count, percentage, and attempt time; its foreign key associates results with users. The schema and 12 sample questions are in `database.sql`.

## System Architecture and Working Process

The browser submits HTML forms to Flask routes. Routes validate input and authorization, then use parameterized MySQL Connector queries to read or update MySQL. Jinja renders escaped template values. A quiz submission is scored on the server and saved as a result; answer explanations are rendered in the response. Flask's signed session cookie carries the authenticated user ID and role.

## Security Features

- Werkzeug `generate_password_hash` / `check_password_hash`; passwords are never stored in plaintext.
- Session-based authentication, HTTP-only and SameSite cookies, and role checks.
- Session-backed CSRF tokens on every POST form.
- Parameterized SQL, server-side validation, unique email constraint, and Jinja autoescaping.
- Deletion requires an authenticated admin and a CSRF-protected POST request.
- Set a private random `SECRET_KEY` before use outside a local demonstration. Set `FLASK_ENV=production` behind HTTPS so secure cookies are enabled. This teaching project is not a substitute for a security review before public deployment.

## CRUD Explanation

Admins use `/admin/questions` to read the question bank. `/admin/questions/add` inserts a validated question, `/admin/questions/edit/<id>` updates an existing record, and a form POST to `/admin/questions/delete/<id>` removes it. All routes require the admin role; SQL uses placeholders or bound parameters.

## Testing and Sample Outputs

Manual smoke-test checklist:

1. Register a learner and sign in; opening `/dashboard` before sign-in redirects to login.
2. Start a quiz, answer some questions, and submit. The result shows a score (for example `8 / 10`, `80%`), explanations, and tips.
3. Open History and confirm the new attempt is listed; dashboard totals and averages update.
4. Sign in as the sample admin, create a question, edit it, then delete it. Confirm a learner is denied access to admin URLs.
5. Try blank registration or invalid email input and confirm validation feedback.

The exact totals depend on the attempts made in your local database.

## Local Setup (VS Code + XAMPP)

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) and verify `python3 --version` in a terminal.
2. Install XAMPP for macOS from [apachefriends.org](https://www.apachefriends.org/). Open the XAMPP manager and start MySQL. Apache is not required for Flask.
3. Open phpMyAdmin at `http://localhost/phpmyadmin` or use the MySQL command-line client. Confirm MySQL is listening on port 3306.
4. Import `database.sql` in phpMyAdmin using **Import**, or run `mysql -u root -p < database.sql` (omit `-p` if your local root account has no password). This creates `security_quiz`, tables, sample questions, and the demo admin.
5. Open the `security_quiz` folder in VS Code. Create and activate a virtual environment, then install packages:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

6. Configure environment variables to match your XAMPP MySQL settings. Defaults are host `127.0.0.1`, port `3306`, database `security_quiz`, user `root`, and an empty password. For a non-default setup:

   ```sh
   export DB_HOST=127.0.0.1
   export DB_PORT=3306
   export DB_NAME=security_quiz
   export DB_USER=root
   export DB_PASSWORD='your-mysql-password'
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
   ```

7. Start the app from the project folder with `python app.py`. Flask listens on `http://127.0.0.1:5000`.
8. Open `http://127.0.0.1:5000` in your browser.
9. Register a learner at `/register`, then sign in at `/login`. Explore the dashboard, quiz, result, and history.
10. Sample administrator: `admin@securityquiz.local` / `Admin@123`. Sign in to reach `/admin`. Change the sample password before using this on a shared machine; in a real deployment, create a dedicated admin and remove demo credentials.
11. From the admin dashboard choose **Manage questions**. Add, edit, and delete questions using the corresponding forms.
12. As a learner, choose **Start a quiz**, submit answers, inspect explanations, then confirm the attempt and average appear on the dashboard and history page.

## Future Enhancements

Add topic tags and difficulty levels, pagination, scheduled learning, charts, password reset, email verification, richer audit logs, rate limiting, automated integration tests, and deployment configuration with managed secrets.

## Conclusion

This application demonstrates a complete local learning workflow: protected accounts, interactive assessment, persistent result tracking, and admin-managed content using Flask and MySQL.