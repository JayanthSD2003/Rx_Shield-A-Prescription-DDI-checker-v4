# RxShield: AI-Powered Prescription Analysis & DDI Checker

RxShield is a cutting-edge desktop application designed to empower patients and healthcare providers with instant, AI-driven analysis of medical prescriptions. By leveraging advanced computer vision and large language models, RxShield digitizes prescriptions, identifies medications, checks for Drug-Drug Interactions (DDIs), and visualizes complex health data through an interactive Knowledge Graph.

## 🚀 Key Features

### 🔍 AI-Powered OCR & Analysis
- **Instant Digitization**: Converts scanned prescription images into editable digital text with high accuracy.
- **Smart Extraction**: Automatically identifies drug names, dosages, and instructions.
- **Manual Entry Support**: Allows users to manually input prescription text for verification.

### ⚠️ Advanced Safety Checks (DDI)
- **Interaction Detection**: Analyzes multiple medications to identify potential adverse drug-drug interactions.
- **Patient-Centric Context**: Tailors warnings based on specific patient details (Age, Gender, Weight, Body Type).
- **Strict Validation**: Enforces mandatory patient data entry to ensure every analysis is contextually accurate.

### 🧠 Knowledge Graph Visualization
- **Visual Intelligence**: Generates a dynamic Knowledge Graph connecting the Patient, Diagnosed Conditions, and Prescribed Drugs.
- **Risk Assessment**: Color-coded edges instantly highlight relationships:
  - 🟢 **Green**: Protective/Therapeutic effects
  - 🔴 **Red**: Risk/Adverse interactions
  - 🔵 **Blue**: Standard associations

### 📄 Professional Reporting
- **Multi-Format Export**: Save comprehensive reports as **PDF**, **Word**, or **Markdown**.
- **Medical-Grade Formatting**: PDF reports are styled with professional headers, layouts, and embedded visualizations suitable for clinical review.

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- A standard desktop environment (Windows/Linux/macOS)

### Setup Steps
1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd RxShield_PyApp_v4
    ```

2.  **Create a Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory and add your API credentials:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    ```
    *(Note: Additional keys for specific OCR services may be required depending on configuration)*

## 💻 Usage

1.  **Launch the Application**
    ```bash
    python main.py
    ```

2.  **Start Analysis**
    - **Dashboard**: Click to upload a prescription image.
    - **Manual Entry**: Select "Manual Entry" to type text directly.

3.  **Enter Patient Details**
    - Fill in the required fields: **Name**, **Age**, **Gender**, **Weight**.
    - *Note: Analysis cannot proceed without these details.*

4.  **Review Results**
    - View the extract medications and safety warnings.
    - Examine the **Knowledge Graph** to understand the treatment plan visually.

5.  **Export Report**
    - Click **"Export PDF"** to save a detailed report to the `reports/` folder.

## 🏗️ Technology Stack

- **Core Framework**: Python & Kivy (UI)
- **AI Engine**: Google GenAI (Flash Models) for Reasoning & OCR
- **Visualization**: NetworkX & Matplotlib (Knowledge Graphs)
- **Reporting**: ReportLab (PDF Generation) & Python-Docx
- **Data Handling**: Pandas & SQLite

## 🔒 Privacy & Security

RxShield is designed with privacy in mind. Patient data is processed for the duration of the analysis session and is not persistently stored on external servers. The "Unknown Patient" feature has been removed to strictly enforce verified data processing.

---
*Disclaimer: RxShield is an AI-assisted tool intended for informational purposes only. It does not reproduce or replace professional medical advice, diagnosis, or treatment. Always verify results with a certified healthcare professional.*
