# 📑 Resume ATS Score Predictor - Analyse and Improve Your Resume 🚀 

---

## 🌐 Live Demo
🔗 Try it here: [Resume ATS Score Predictor](https://resume-ats-score-predictor.onrender.com/)  

---

**Project Overview**  
The **Resume ATS Score Predictor** is a web-based tool designed to help job seekers optimize their resumes for Applicant Tracking Systems (ATS). Users can upload their resume as a PDF and specify the job type they are applying for. The application then leverages advanced AI capabilities to provide an **ATS compatibility score (out of 100)** and offers actionable suggestions for improvement, helping candidates tailor their applications more effectively.

---

## ✨ Features
- 📄 **Resume Upload** – Seamlessly upload resumes in PDF format.  
- 🎯 **Job Type Specific Analysis** – Get ATS score and tailored suggestions for a chosen job role.  
- 📊 **ATS Score Calculation** – Receive a compatibility score (0–100).  
- 💡 **Actionable Suggestions** – Improve resume keywords, formatting, and relevance.  
- 💾 **Data Persistence** – All analysis results (resume text, job type, score, suggestions) are stored in an **SQLite database**.  

---

## 🛠️ Technologies Used

### Backend
- **Python 🐍** – Core programming language  
- **Flask** – Lightweight backend framework  
- **Google Gemini API** – AI-powered resume analysis & scoring  
- **PyPDF2** – PDF text extraction  
- **SQLite** – Lightweight relational database  
- **Gunicorn** – Production WSGI server  

### Frontend
- **HTML5** – App structure  
- **Tailwind CSS** – Responsive UI styling  
- **JavaScript** – Dynamic client-side interactions & AJAX  

### Deployment
- **Render** – Continuous deployment & hosting  

---

## ⚙️ How It Works
1. **User Uploads** – A PDF resume and job type are submitted via the web interface.  
2. **PDF Text Extraction** – Flask backend extracts text using `PyPDF2`.  
3. **AI Analysis** – Resume text + job type sent to **Google Gemini API** for ATS scoring and suggestions.  
4. **Data Storage** – Results stored in **SQLite database**.  
5. **Results Display** – Score and improvement tips returned to frontend and displayed to the user.  

---

# 🙋‍♂️ Author
- **Juhil Kikani**
- [LinkedIn](https://www.linkedin.com/in/juhilkikani)
- Email: [juhilkikani07@gmail.com](mailto:juhilkikani07@gmail.com)

# ⭐️ Give it a Star
  If you liked this project, don’t forget to ⭐️ the repo!
