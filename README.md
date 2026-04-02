# AI GK Quiz App

Modern full-stack quiz application built with Flask, MySQL, HTML, CSS, and JavaScript.

## Features

- User registration, login, logout, and session handling
- First-time rules screen before quiz start
- OpenAI-powered question generation with database caching
- 3 levels with progressive unlocking
- 7 quiz categories
- One-question-at-a-time flow with timer and autosave
- Profile page with avatar upload and quiz history
- Leaderboard
- Admin signup, login, dashboard, and question manager
- Dark/light mode, animated background, smooth UI transitions

## Quick Start

1. Create the MySQL database and tables by importing [schema.sql](/c:/xampp/htdocs/quiz_app/database/schema.sql).
2. Create a `.env` file based on [.env.example](/c:/xampp/htdocs/quiz_app/.env.example).
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python app.py
```

5. Open `http://127.0.0.1:5000`.

## Admin Setup

- Admin signup page: `http://127.0.0.1:5000/admin/register`
- Admin login page: `http://127.0.0.1:5000/admin/login`
- Separate admin table SQL: [admin_auth.sql](/c:/xampp/htdocs/quiz_app/database/admin_auth.sql)
- If your existing tables were created earlier, run [admin_signup_patch.sql](/c:/xampp/htdocs/quiz_app/database/admin_signup_patch.sql) once in phpMyAdmin if admin columns are missing.

## Notes

- The app uses `OPENAI_API_KEY` from your environment. Do not hardcode API keys in source files.
- To use XAMPP MySQL as-is, the default connection string is:

```env
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/quiz_app
```
