# ⚖️ Legal Document Search and Clause Finder

## 📌 Project Title

**Legal Document Search and Clause Finder**

---

## 🎯 Objective

The objective of this project is to develop a Flask-based web application that enables efficient searching within legal documents.
The system allows users to upload legal files and instantly retrieve relevant clauses using intelligent keyword searching and Boolean query processing.

This application reduces manual effort required to review lengthy legal documents such as contracts, agreements, and policy files.

---

## 🧠 Algorithms Used

The search engine is implemented using the following Information Retrieval techniques:

* **Inverted Index** — Enables fast keyword lookup across documents
* **Boolean Retrieval Model** — Supports `AND`, `OR`, and `NOT` queries
* **TF-IDF Ranking** — Ranks documents based on relevance score

---

## 🚀 Features

* 📄 Upload legal documents (PDF, DOCX, TXT)
* 🔍 Boolean keyword search
* 📊 TF-IDF based relevance ranking
* 📑 Automatic clause extraction
* 🗑️ Document management and deletion
* 💾 Persistent indexing using JSON storage
* 🖥️ Interactive web interface

---

## 🛠️ Tools and Technologies Used

| Technology              | Purpose              |
| ----------------------- | -------------------- |
| Python                  | Backend programming  |
| Flask                   | Web framework        |
| HTML / CSS / JavaScript | Frontend interface   |
| PyPDF2                  | PDF text extraction  |
| python-docx             | DOCX file processing |
| JSON                    | Data storage         |
| TF-IDF                  | Document ranking     |
| Inverted Index          | Fast searching       |

---

## 📁 Project Structure

```
LEGAL/
├── app.py
├── templates/
│   └── index.html
├── uploads/
├── inverted_index.json
├── documents_metadata.json
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation Steps

### 1. Clone Repository

```
git clone https://github.com/YOUR_USERNAME/legal-document-search.git
cd legal-document-search
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

---

## ▶️ Instructions to Run the Application

Run the Flask server:

```
python app.py
```

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## 🔎 How to Use

1. Upload legal documents using drag-and-drop or file selection.
2. Enter keywords or Boolean queries in the search bar.
3. Example searches:

   * `liability AND indemnification`
   * `termination OR cancellation`
   * `contract NOT penalty`
4. View ranked results and matching clauses.
5. Delete documents if required.

---

## 📦 Dependencies

Install all required packages using:

```
pip install -r requirements.txt
```

Main libraries:

* Flask
* PyPDF2
* python-docx

---

## 📸 Execution Screenshots

*(Add screenshots before submission)*

* Flask server running in terminal
* Application running in web browser
* GitHub repository with commit history

---

## 👤 Student Information

**Name:** Gopika
**Register Number:** 2303121012
**Course:** Information Science and Engineering


## 📘 License

This project is developed for academic purposes as part of coursework submission.
