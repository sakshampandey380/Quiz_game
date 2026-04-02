# 🧠 Quizly - AI GK Quiz App

A modern full-stack AI-powered quiz platform built with **Flask, MySQL, HTML, CSS, and JavaScript**, designed to deliver an interactive and intelligent quiz experience.

---

## ✨ Features

* 🔐 **Authentication System**

  * User registration, login, logout
  * Secure session handling

* 📜 **Quiz Flow**

  * First-time rules screen
  * One-question-at-a-time interface
  * Timer-based questions with autosave

* 🤖 **AI Question Generation**

  * OpenAI-powered dynamic questions
  * Database caching for performance

* 🎯 **Levels & Progression**

  * 3 levels with progressive unlocking
  * Structured difficulty system

* 📚 **Categories**

  * 7 quiz categories
  * Diverse knowledge coverage

* 👤 **User Profile**

  * Avatar upload
  * Quiz history tracking

* 🏆 **Leaderboard**

  * Competitive ranking system

* 🛠️ **Admin Panel**

  * Admin signup/login
  * Dashboard with controls
  * Question management system

* 🎨 **UI/UX**

  * Dark / Light mode
  * Animated background
  * Smooth transitions

---

## 🛠️ Tech Stack

### Backend

* Flask (Python)

### Database

* MySQL

### Frontend

* HTML, CSS, JavaScript

### AI Integration

* OpenAI API

---

## 📁 Project Structure

```bash id="quiz001"
quiz_app/
├── database/
│   ├── schema.sql
│   ├── admin_auth.sql
│   ├── admin_signup_patch.sql
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│
├── templates/
│
├── app.py
├── requirements.txt
├── .env.example
```

---

## ⚙️ Quick Start

### 1. Setup Database

Import schema:

```bash id="quiz002"
database/schema.sql
```

---

### 2. Configure Environment

Create `.env` file:

```env id="quiz003"
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/quiz_app
OPENAI_API_KEY=your_api_key_here
```

---

### 3. Install Dependencies

```bash id="quiz004"
pip install -r requirements.txt
```

---

### 4. Run Application

```bash id="quiz005"
python app.py
```

---

### 5. Open in Browser

```text id="quiz006"
http://127.0.0.1:5000
```

---

## 🛠️ Admin Setup

* Admin Register:

  ```text id="quiz007"
  http://127.0.0.1:5000/admin/register
  ```

* Admin Login:

  ```text id="quiz008"
  http://127.0.0.1:5000/admin/login
  ```

---

### ⚠️ If Admin Tables Missing

Run:

```bash id="quiz009"
database/admin_signup_patch.sql
```

---

## 📝 Notes

* Uses `OPENAI_API_KEY` from environment
* Do NOT hardcode API keys
* Works with XAMPP MySQL setup

---

## 🚀 Future Improvements

* Multiplayer quiz mode
* Real-time competition
* AI difficulty adjustment
* Mobile-first optimization

---

## 👨‍💻 Author

**Saksham Pandey**

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!
  
