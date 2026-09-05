# VocalChaos — AI Supervisor & Voice Agent Auditor

**VocalChaos** is an AI stress-testing and auditing system designed to evaluate conversational voice customer support agents against verified ground-truth data.

It pits an **Adversarial Supervisor Agent** (acting as a demanding customer) against a **Target Customer-Support Agent** in a real-time spoken voice dialogue, followed by an **Automated Evidence-Based AI Auditor** that evaluates adherence to company database records and policies.

---

## Required API Keys & Architecture

### What API Key is Required?
To run this project on any system, you **MUST** provide a **Google Gemini API Key**.

* **Required Key**: `GEMINI_API_KEY`
* **Get Free Key**: Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
* **Where to place it**: In a `.env` file at the root of the project directory.

> **Note on Audio & Speech APIs**: Speech-to-Text (STT) and Text-to-Speech (TTS) use the browser-native **Web Speech API** built into Google Chrome (`window.SpeechRecognition` & `window.speechSynthesis`). **No external speech API key is required!**

---

## API & System Flow Architecture

```text
[ Browser / Streamlit UI (Chrome) ]
  │
  ├── 1. Web Speech STT (Mic input -> Text)
  ├── 2. Web Speech TTS (Audio playback of responses)
  │
  ▼  HTTP REST Requests (JSON)
[ FastAPI Backend (localhost:8000) ]
  │
  ├── Target Agent        ---> Grounded Synthetic DB + Google Gemini API (gemini-3.6-flash)
  ├── Supervisor Agent    ---> Google Gemini API (gemini-3.6-flash)
  └── Evaluator Auditor   ---> Ground-Truth Verification + Google Gemini API (gemini-3.6-flash)
```

### Endpoints Breakdown:
* **`POST /chat`**: Target Agent query endpoint. Answers customer questions strictly using grounded dataset.
* **`GET /supervisor/scenarios`**: Retrieves available stress-test scenarios.
* **`POST /supervisor/start` & `POST /supervisor/step`**: Supervisor Agent turn-by-turn line generation.
* **`POST /supervisor/simulate`**: Runs multi-turn simulation between Supervisor and Target Agent.
* **`POST /evaluate`**: Independent AI Auditor endpoint. Audits transcript against Ground Truth records and policies.
* **`GET /knowledge/lookup`**: Queries database records (orders, products, customers, shipments).
* **`GET /history/{conversation_id}`**: Retrieves conversation history for session sync.
* **`GET /health`**: System health check.

---

## Project Structure

```text
VocalChaos/
│
├── app/
│   ├── main.py                     # FastAPI server & REST API endpoints
│   ├── config.py                   # Environment configuration & API key resolver
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── target_agent.py         # Grounded Support AI bounded by DB & Policies
│   │   └── supervisor_agent.py     # Adversarial customer generator (13 scenarios)
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── evaluator.py            # Strict evidence-based compliance auditor
│   │
│   ├── knowledge/
│   │   ├── data/                   # Synthetic E-Commerce Datasets (JSON)
│   │   │   ├── company_policies.json
│   │   │   ├── customers.json
│   │   │   ├── orders.json
│   │   │   ├── products.json
│   │   │   └── shipments.json
│   │   ├── data_loader.py          # Dataset memory loader
│   │   ├── retriever.py            # Entity extraction & DB lookup layer
│   │   └── knowledge_base.py       # E-Commerce support policies & grounding helper
│   │
│   └── models/
│       └── schemas.py              # Pydantic data schemas & response models
│
├── ui/
│   └── streamlit_app.py            # Streamlit interactive dashboard & voice player
│
├── .env.example                    # Template for environment variables
├── .env                            # Your local environment variables (contains API key)
├── requirements.txt                # Python package dependencies
└── README.md                       # Complete setup & operational documentation
```

---

## How to Run on Any System

Follow these simple step-by-step instructions to run VocalChaos on Windows, macOS, or Linux.

### Prerequisites:
1. **Python 3.9+** installed on your system.
2. **Google Chrome** browser (recommended for Web Speech API microphone and TTS support).
3. **Google Gemini API Key** ([Get free key here](https://aistudio.google.com/)).

---

### Step 1: Clone Repository
```bash
git clone https://github.com/Sukhpreet2572/AI_Risk_Manager.git
cd AI_Risk_Manager
```

---

### Step 2: Create & Activate Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Your API Key (`.env`)

Create a file named `.env` in the root folder (or copy from `.env.example`):

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
LLM_MODEL=gemini-3.6-flash
HOST=0.0.0.0
PORT=8000
FASTAPI_BACKEND_URL=http://localhost:8000
```

---

### Step 5: Start the FastAPI Backend Server

Run the backend server from your terminal:

```bash
uvicorn app.main:app --reload --port 8000
```

Verify backend is running by opening:
- **Health Check**: http://localhost:8000/health
- **Interactive Swagger Docs**: http://localhost:8000/docs

---

### Step 6: Start the Streamlit UI (New Terminal)

Open a **second terminal window**, activate your virtual environment, and start Streamlit:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run ui/streamlit_app.py
```

Streamlit will open automatically in your browser at: **`http://localhost:8501`**.

---

## How to Use VocalChaos

### 1. Real-Time Voice-to-Voice Simulation & Auditor
* Select a stress-test scenario in the sidebar (e.g., *Wrong Customer Claim*, *Fake Manager Approval Claim*, *Non-Existent Order Query*, *Refund Pressure*).
* Click **Start Live Voice Simulation**.
* Both agents speak aloud turn-by-turn with distinct voices and dynamic status indicators.
* As soon as dialogue finishes, the **AI Auditor** automatically inspects the transcript and renders the **Ground Truth Audit Card**:
  * **Overall Compliance Score** (out of 10) & Result Badge (`EXCELLENT`, `PASSED`, `WARNING`, `FAILED`).
  * **Attack Vector** tested.
  * **Target Response Audited**.
  * **Applied Knowledge Base Policy**.
  * **Category Breakdown** (Hallucination Resistance, Policy Compliance, Unsupported Claims, Handling Missing Info, Professionalism).
  * **Detected Failure Cards** featuring exact quote evidence and policy violation explanations.

### 2. Target Agent Manual Voice & Text Testing
* Click **Click to Speak to Agent** to speak directly to the Target Agent via microphone.
* Speak your query (e.g., *"What is the status of order ORD-2400321?"*).
* The Target Agent responds verbally and both turns immediately appear in the **Manual Chat Transcript Log**.
* Click **Run AI Audit on Manual Transcript** to evaluate your manual session against company ground truth.

---

## Troubleshooting & Common Issues

### Issue 1: Port 8000 in Use / Timed Out
If port 8000 is occupied by a frozen process:

* **Windows**:
  ```cmd
  netstat -ano | findstr :8000
  taskkill /F /PID <PID_NUMBER>
  ```
* **macOS / Linux**:
  ```bash
  lsof -i :8000
  kill -9 <PID_NUMBER>
  ```

### Issue 2: Microphone Permission Denied
* Ensure you are running the application in **Google Chrome**.
* Click the lock icon next to `http://localhost:8501` in the Chrome address bar and set **Microphone** to **Allow**.

---

## License & Acknowledgments

Built for demonstration of AI Voice Agent Supervision, Grounding & Hallucination Prevention. Uses Google Gemini LLM API and Web Speech API.
