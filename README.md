# 🏠 FloorAI – Intelligent Floor Plan Analyzer & 3D Visualizer

## 🚀 Overview
**FloorAI** is an AI-powered web application that transforms 2D floor plans into structured data and interactive 3D visualizations. It helps users extract measurements, understand layouts, and get material recommendations — all from a simple blueprint upload.

Built during a **24-hour hackathon**, this project focuses on combining **Computer Vision + Web Development + Practical Engineering Insights**.

---

## ✨ Features

- 📤 **Upload Floor Plan**
  - Drag & drop or upload blueprint images
- 🧠 **AI-Based Parsing**
  - Detects walls, rooms, and layout structure using OpenCV
- 📏 **Accurate Measurements**
  - Extracts coordinates and dimensions from floor plans
- 🏗️ **3D Model Generation**
  - Converts 2D layouts into basic 3D structures
- 🧱 **Material Recommendations**
  - Suggests construction materials based on layout
- 🌐 **Interactive Web UI**
  - Clean frontend with real-time feedback

---

## 🛠️ Tech Stack

### 👨‍💻 Backend
- Python
- Flask
- OpenCV
- NumPy

### 🎨 Frontend
- HTML
- CSS
- JavaScript

### 🧩 Modules
- `parser.py` → Floor plan image processing  
- `model3d.py` → 3D structure generation  
- `materials.py` → Material recommendation logic  
- `app.py` → Main Flask application  

---

## 📂 Project Structure

    floor_ai_project/
    ├── app.py
    ├── parser.py
    ├── model3d.py
    ├── materials.py
    ├── templates/
    │   └── index.html
    ├── static/
    │   └── script.js
    └── README.md

---

## ⚙️ Installation & Setup
1️⃣ Clone the Repository

git clone <your-repo-link>

cd floor_ai_project

2️⃣ Create Virtual Environment

python -m venv venv

venv\Scripts\activate   # Windows

3️⃣ Install Dependencies

pip install flask opencv-python numpy

4️⃣ Run the Application

python app.py

5️⃣ Open in Browser

http://127.0.0.1:5000

---

## 🧠 How It Works

User uploads a floor plan image

parser.py processes the image using OpenCV:

Edge detection

Contour extraction

Wall identification

Coordinates and measurements are extracted

model3d.py converts data into a 3D representation

materials.py suggests suitable construction materials

Results are displayed on the frontend

---

## 🎯 Use Cases

-🏗️ Civil Engineering Students

-🏡 Architects & Designers

-🧑‍💻 Real Estate Visualization

-📚 Educational Tools for Geometry & Layout Understanding

---

## ⚠️ Limitations
Works best with clear, high-quality floor plans
Complex architectural drawings may need further optimization
3D models are currently basic representations

---

## 🔮 Future Improvements
AI-based room classification (Bedroom, Kitchen, etc.)
Advanced 3D rendering (Three.js integration)
Real-world scale calibration
Export to CAD formats
ML model for better detection accuracy

---

## 👥 Team Alpha   
-Payash Sonbarsa

-Riya Garg

---

## 🏆 Hackathon Note

This project was built under strict time constraints with a focus on:

Problem-solving
System design
Rapid prototyping

---

### 📜 License

This project is for educational and hackathon purposes.

---

## 💡 Final Thought

“Turning blueprints into intelligence — making construction smarter with AI.”
