# AIVOA.AI — AI-Powered Deviation Intake Module

**AIVOA.AI** is an advanced, AI-powered deviation intake module built for pharmaceutical and API manufacturing QA teams. It revolutionizes the process of logging manufacturing deviations, non-conformances, and out-of-specification events by using Generative AI to automatically extract critical data from raw incident reports or PDF documents. 

Designed with a strict **Human-in-the-Loop** approach, the system empowers QA reviewers by pre-populating GMP-aligned forms and proposing risk assessments, while keeping the final decision strictly in the hands of the human expert.

## Key Features

* **Pasted Deviation Text Input**: Quickly paste raw, unstructured text directly from emails, logs, or informal reports.
* **PDF Deviation Document Extraction**: Upload PDF documents to automatically extract the underlying text.
* **AI-Powered Deviation Field Extraction**: Automatically structure raw text into GMP fields like Batch/Lot Number, Site/Plant, Date of Occurrence, and Detailed Description.
* **AI Impact & Severity Assessment**: Automatically calculates Initial Severity (Critical, Major, Minor) and Initial Impact based on GMP guidelines.
* **Severity Reasoning, Confidence & Suggested Next Action**: Provides the "why" behind the AI's risk assessment, its self-reported confidence score, and immediate recommended actions.
* **Human Review & Manual Correction**: Fully editable interface allowing the user to inspect, modify, and finalize all AI-generated fields.
* **Conversational Edit Interaction**: A built-in AI Assistant allows users to correct data via natural language (e.g., *"Actually, the batch number is X102"*).
* **Risk Reassessment on Edit**: If conversational edits impact risk-relevant fields, the AI automatically reassesses the severity and impact.
* **Save and Retrieve**: Saves fully reviewed deviations to a relational database for audit trails.
* **Extraction Summary & Indicators**: A visual "Extraction Summary" widget tracks exactly how many fields are populated, empty, or human-reviewed, alongside clear "AI Suggested" and "Reviewed" field badges.

---

## Complete Workflow

1. **Deviation Input**: The user pastes raw text or uploads a PDF document (which extracts raw text using PyMuPDF).
2. **AI Extraction**: The text is sent to the AI pipeline. The `Extract Node` parses the unstructured text and maps it to structured Pydantic fields.
3. **AI Risk Assessment**: The pipeline moves to the `Assess Node`, which evaluates the extracted data to determine GMP Severity, Impact, Reasoning, and Next Actions.
4. **Human Review / Edit**: The structured data populates the React form. 
   - The user can manually edit the form fields.
   - Alternatively, the user can type natural language corrections in the AI Assistant chat. The `Edit Node` applies these corrections, and if they change the nature of the deviation, re-triggers the `Assess Node`.
5. **Save**: Once the user has reviewed the fields (updating the "Reviewed" counter), they save the finalized deviation to the MySQL database.

---

## Technology Stack

**Frontend:**
* React (Vite)
* TypeScript
* Redux Toolkit
* Axios
* Lucide React (Icons)
* Vanilla CSS (Modern, premium styling)

**Backend:**
* Python
* FastAPI
* LangGraph & LangChain
* Groq API
* Pydantic
* PyMuPDF (PDF Text Extraction)

**Database:**
* MySQL
* SQLAlchemy (ORM)
* Alembic (Migrations)

---

## Architecture

```mermaid
graph TD
    UI[React + Redux UI]
    FA[FastAPI Backend]
    LG[LangGraph Pipeline]
    LLM[Groq API: openai/gpt-oss-120b]
    DB[(MySQL Database)]

    UI -- "POST /process (Raw Text)" --> FA
    FA -- "Text" --> LG
    LG -- "Extract & Assess Prompts" --> LLM
    LLM -- "Structured Output" --> LG
    LG -- "AIProcessResult Schema" --> FA
    FA -- "JSON Response" --> UI
    UI -- "POST /deviations (Reviewed Form)" --> FA
    FA -- "SQLAlchemy ORM" --> DB
```

---

## LangGraph AI Workflow

The backend uses a compiled **LangGraph** state machine to orchestrate the AI workflow:
1. **`extract_node`**: Analyzes the raw text and extracts core deviation details into a strict `ExtractedDeviation` Pydantic schema using structured output.
2. **`assess_node`**: Takes the extracted details and evaluates the GMP risk, returning an `AssessedDeviation` schema (Severity, Impact, Reason, Confidence, Next Action).
3. **`edit_node`**: When a user submits a conversational edit (e.g., *"Change the site to Reactor B"*), this node applies the change to the current form state. If the edit alters risk-relevant context, the graph loops back to the `assess_node` to ensure the risk rating remains accurate.

---

## AI Model

The project utilizes the Groq API for ultra-fast inference. 
* **Currently Configured Model**: `openai/gpt-oss-120b`
* **Note**: The originally intended model (`llama-3.3-70b-versatile`) was unavailable in the provided Groq environment. After checking available models, the largest/most capable available model (`gpt-oss-120b`) was selected as a drop-in replacement to maintain high-quality structured extraction.

---

## Project Structure

```text
AI Powered_Deviation Intake/
├── backend/
│   ├── alembic/                # Database migration scripts
│   ├── app/
│   │   ├── ai/
│   │   │   ├── pipeline.py     # LangGraph workflow definition
│   │   │   ├── nodes.py        # LangGraph nodes (extract, assess, edit)
│   │   │   ├── prompts.py      # LLM prompt templates
│   │   │   └── state.py        # Graph state definitions
│   │   ├── routers/
│   │   │   └── deviations.py   # FastAPI route definitions
│   │   ├── config.py           # Environment variable loading
│   │   ├── database.py         # SQLAlchemy engine & session
│   │   ├── main.py             # FastAPI entry point
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── .env                    # Environment variables
│   └── requirements.txt        # Python dependencies
└── frontend/
    ├── src/
    │   ├── api/
    │   │   └── client.ts       # Axios API client
    │   ├── components/         # React components (DeviationForm, AssistantPanel, etc.)
    │   ├── store/
    │   │   ├── store.ts        # Redux store configuration
    │   │   └── deviationSlice.ts # Redux state slice for deviation workflow
    │   ├── App.tsx             # Main application layout
    │   └── index.css           # Global custom styling
    ├── package.json            # Node dependencies
    └── vite.config.ts          # Vite configuration
```

---

## Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check to verify API and DB connectivity. |
| `POST` | `/extract/pdf` | Extracts raw text from an uploaded PDF/DOCX using PyMuPDF. Does not trigger AI. |
| `POST` | `/process` | Runs the AI pipeline (`extract` → `assess`) on raw text and returns structured fields. |
| `POST` | `/process/pdf` | Convenience endpoint: extracts text from PDF and runs the AI pipeline immediately. |
| `POST` | `/deviations/edit` | Applies conversational edits to the current form state via the `edit_node`. |
| `POST` | `/deviations` | Saves a finalized, human-reviewed deviation record to the MySQL database. |
| `GET` | `/deviations` | Retrieves a list of all logged deviation records. |
| `GET` | `/deviations/{id}` | Retrieves a specific logged deviation by ID. |

---

## Database

The application uses **MySQL** managed via SQLAlchemy ORM and Alembic migrations.
* **Table**: `deviations`
* **Structure**: A single, wide table that stores system-managed fields (status, input_source, raw_input_text), user-editable AI-populated fields (title, site, batch, detailed description, etc.), and AI risk assessment fields (severity, impact, reasoning, confidence).

---

## Human-in-the-Loop Design

AIVOA.AI is strictly designed as an *assistant*, not an autonomous decision-maker. 
* AI outputs are never directly saved to the database.
* The frontend visually distinguishes AI-populated fields with a purple `✦ AI Suggested` badge.
* The user must review the fields, which transitions the badges to a green `✓ Reviewed` state.
* The "Save Deviation" action represents the final human approval of the data.

---

## PDF Processing

Text extraction is handled entirely locally on the backend using **PyMuPDF** (`fitz`). 
* This allows for extremely fast, secure extraction of text-based PDFs.
* *Note: OCR (Optical Character Recognition) for scanned, image-only PDFs is not currently implemented in this module.*

---

## Validation & Error Handling

* **Pydantic Validation**: Ensures the AI strictly adheres to the expected schemas, utilizing `with_structured_output()` to guarantee type safety and constrained enumerations (e.g., Severity must be exactly "Critical", "Major", or "Minor").
* **Ambiguity Handling**: If the AI cannot confidently extract a field (e.g., missing batch number), it returns `None`, allowing the frontend to highlight it as an "Empty Field" needing human attention.
* **Graceful Degradation**: If the AI pipeline fails, the backend returns clean HTTP 500 exceptions, which the React frontend catches and displays as friendly error banners without breaking the UI.

---

## Setup & Installation

### 1. Database Setup
Ensure you have MySQL installed and running. Create a database for the project:
```sql
CREATE DATABASE deviation_intake;
```

### 2. Backend Setup
Clone the repository and open the `backend` directory:
```bash
cd backend
```
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the `.env.example` file to `.env` inside the `backend` directory:
```bash
cp .env.example .env
```
Update the `.env` file with your MySQL credentials and Groq API key (see Environment Variables section).

### 4. Database Migrations
Run Alembic to create the database tables:
```bash
alembic upgrade head
```

### 5. Start Backend Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

### 6. Frontend Setup
Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## Environment Variables

Required variables in `backend/.env`:

```env
# MySQL connection string
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/deviation_intake

# Groq API key (get from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here
```

---

## Usage

1. **Input Data**: Open the application and either paste raw deviation text into the AI Assistant chat box, or click the paperclip icon to upload a text-based PDF.
2. **Process**: Click **Process with AI**. The system will analyze the text.
3. **Review Extraction**: The left panel will populate with the extracted data. Review the "Extraction Summary" to see how many fields were populated or left empty.
4. **Review Assessment**: Check the highlighted blue "AI Risk Assessment" card for the severity, impact, and reasoning.
5. **Make Corrections**: Edit the form directly, or type a natural language correction into the AI Assistant (e.g., *"Update the site to Plant B"*).
6. **Save**: Once all fields are reviewed and correct, click **Save Deviation** to log the record to the database.

---

## Scope & Limitations

* **PDF Parsing**: Text extraction relies on PyMuPDF. It does not support Optical Character Recognition (OCR) for scanned, image-only PDFs.
* **Authentication**: This module focuses entirely on the AI pipeline and UI workflow; user authentication and role-based access control (RBAC) are not implemented.
* **Autonomy**: The AI does not auto-log deviations. Human review is a mandatory part of the workflow by design.

---

## Future Enhancements

* Integration with an OCR engine (e.g., Tesseract or AWS Textract) to support scanned documents.
* User authentication and role management to track *who* reviewed and approved the AI suggestions.
* AI-driven historical search to detect recurring deviations based on past database records.

---

## Author

**Aritray Das**  
B.E. Computer Science Engineering
