# 🎙️ VocalChaos — AI Supervisor for Voice Agents

**VocalChaos** is a lightweight, real-time AI stress-testing and auditing system designed to evaluate conversational voice customer support agents.

It pits an **Adversarial Supervisor Agent** (acting as a tricky/demanding customer) against a **Target Customer-Support Agent** in a real-time spoken voice dialogue, followed by an **Automated Evidence-Based AI Auditor** that evaluates adherence to company ground truth.

---

## 🔑 Required API Keys & Architecture

### What API Key is Required?
To run this project on any system, you **MUST** provide a **Google Gemini API Key**.

* **Required Key**: `GEMINI_API_KEY`
* **Get Free Key**: Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
* **Where to place it**: In a `.env` file at the root of the project directory.

> ℹ️ **Note on Audio & Speech APIs**: Speech-to-Text (STT) and Text-to-Speech (TTS) use the browser-native **Web Speech API** built into Google Chrome (`window.SpeechRecognition` & `window.speechSynthesis`). **No external speech API key is required!**

---

## 🛠️ API & System Flow Architecture

```text
[ Browser / Streamlit UI (Chrome) ]
  │
  ├── 1. Web Speech STT (Mic input -> Text)
  ├── 2. Web Speech TTS (Audio playback of responses)
  │
  ▼  HTTP REST Requests (JSON)
[ FastAPI Backend (localhost:8000) ]
  │
  ├── Target Agent        ---> Google Gemini API (gemini-3.6-flash)
  ├── Supervisor Agent    ---> Google Gemini API (gemini-3.6-flash)
  └── Evaluator Auditor   ---> Google Gemini API (gemini-3.6-flash)
```

### Endpoints Breakdown:
* **`POST /chat`**: Target Agent query endpoint. Answers customer questions strictly using the knowledge base.
* **`GET /supervisor/scenarios`**: Retrieves available stress-test scenarios.
* **`POST /supervisor/start` & `POST /supervisor/step`**: Supervisor Agent turn-by-turn line generation.
* **`POST /supervisor/simulate`**: Runs multi-turn simulation between Supervisor and Target Agent.
* **`POST /evaluate`**: Independent AI Auditor endpoint. Audits transcript against Knowledge Base rules (**NO EVIDENCE = NO CREDIT** principle).
* **`GET /history/{conversation_id}`**: Retrieves conversation history for session sync.
* **`GET /health`**: System health check.

---

## 📁 Project Structure

```text
VocalChaos/
│
├── app/
│   ├── main.py                     # FastAPI server & REST API endpoints
│   ├── config.py                   # Environment configuration & API key resolver
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── target_agent.py         # Support AI bounded by Knowledge Base
│   │   └── supervisor_agent.py     # Adversarial customer generator (5 scenarios)
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── evaluator.py            # Strict evidence-based compliance auditor
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   └── knowledge_base.py       # Official E-Commerce support policies
│   │
│   └── models/
│       ├── __init__.py
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

## 🚀 How to Run on Any System (ZIP Export Instructions)

Follow these simple step-by-step instructions to run VocalChaos on Windows, macOS, or Linux.

### Prerequisites:
1. **Python 3.9+** installed on your system.
2. **Google Chrome** browser (recommended for Web Speech API microphone and TTS support).
3. **Google Gemini API Key** ([Get free key here](https://aistudio.google.com/)).

---

### Step 1: Extract Project Files
Extract the ZIP archive (or clone the repository) into a folder on your computer and open a terminal inside that folder.

```bash
cd VocalChaos
```

---

### Step 2: Create & Activate Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt - cmd):
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
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

```bash
cp .env.example .env
```

Open `.env` in any text editor and add your **Gemini API Key**:

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

#### Windows:
```powershell
.\venv\Scripts\Activate.ps1
streamlit run ui/streamlit_app.py
```

#### macOS / Linux:
```bash
source venv/bin/activate
streamlit run ui/streamlit_app.py
```

Streamlit will open automatically in your browser at: **`http://localhost:8501`**.

---

## 🎯 How to Use VocalChaos

### 1. 🔴 Real-Time Voice-to-Voice Simulation & Auditor
* Select a stress-test scenario in the sidebar (e.g., *Refund Pressure*, *Fake Delivery Information*, *Hallucinated Refund Amount*, *Policy Manipulation*, *Aggressive Customer*).
* Click **🚀 Start Live Voice Simulation**.
* Both agents speak aloud turn-by-turn with distinct voices and dynamic status indicators (`🟢 LIVE`, `🟡 Thinking...`, `🔊 Speaking...`).
* As soon as dialogue finishes, the **AI Auditor** automatically inspects the transcript and renders the **`🔎 WHY THIS SCORE?` Ground Truth Audit Card**:
  * **Overall Compliance Score** (out of 10) & Result Badge (`EXCELLENT`, `PASSED`, `WARNING`, `FAILED`, `CRITICAL FAILURE`).
  * **Attack Vector** tested.
  * **Exact Target Words Audited**.
  * **Applied Knowledge Base Policy**.
  * **Category Breakdown** (Hallucination Resistance, Policy Compliance, Unsupported Claims, Missing Info Handling, Professionalism).
  * **Detected Failure Cards** featuring exact quote evidence and policy violation explanations.

### 2. 🎙️ Target Agent Manual Voice & Text Testing
* Click **Click to Speak to Agent** to speak directly to the Target Agent via microphone.
* Speak your query (e.g., *"I want to return an item I received 5 days ago"*).
* The Target Agent responds verbally and both turns immediately appear in the **💬 Manual Chat Transcript Log**.
* Click **🔍 Run AI Audit on Manual Transcript** to evaluate your manual session against company ground truth.

---

## 🔧 Troubleshooting & Common Issues

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
* Click the lock icon 🔒 next to `http://localhost:8501` in the Chrome address bar and set **Microphone** to **Allow**.

### Issue 3: Gemini API Quota Limit (HTTP 429)
* VocalChaos automatically uses a fallback chain (`gemini-3.6-flash` -> `gemini-3.5-flash-lite` -> `gemini-flash-latest` -> `gemini-3.1-flash-lite`).
* If you hit rate limits on free-tier Gemini API, wait 60 seconds or switch keys.

---

## 📜 License & Acknowledgments

Built for hackathon demonstration of AI Voice Agent Supervision & Hallucination Prevention. Uses Google Gemini LLM API and Web Speech API.
