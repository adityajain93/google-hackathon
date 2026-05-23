# AI Agent Testing & Verification Guide

Welcome! If you are an AI agent tasked with modifying, maintaining, or testing this repository, use this guide to verify code changes, debug the application, and run integration checks.

---

## 1. Directory Structure Validation

Verify that the modular structure matches the expected format.
* **`inputs/`**: Contains ingestion logic (`base.py`, `caltrans.py`, `zoo_feed.py`).
* **`intelligence/`**: Contains ML/AI layers (`analyzer.py`, `gemini_client.py`).
* **`agents/`**: Contains monitoring agents (`traffic_agent.py`, `zoo_agent.py`).
* **`outputs/`**: Contains notifications (`notifier.py`) and UI assets (`ui/index.html`, `ui/style.css`, `ui/app.js`).
* **`server.py`**: Main server script.

To check structure:
```bash
ls -R inputs/ intelligence/ agents/ outputs/
```

---

## 2. Environment Verification

Check if `.env` exists and contains appropriate credentials. Do NOT commit `.env` modifications to git.
* **`GOOGLE_MAPS_API_KEY`**: Maps render key.
* **`GEMINI_API_KEY`**: Auth key for Gemini 1.5/2.5 Flash models. (If missing, the system automatically defaults to simulation responses).

---

## 3. Launching & Port Management

The web server binds to port `8000` by default.

### Check if Port 8000 is occupied:
```bash
lsof -i :8000
```

### Terminate existing server processes (if binding fails):
```bash
kill $(lsof -t -i:8000)
```

### Run Server:
```bash
python3 server.py
```

---

## 4. API Endpoint Integration Tests

Run the following commands using `curl` while `server.py` is running to verify backend APIs:

### A. Root Page Server Check
```bash
curl -I http://localhost:8000/
# Expected: HTTP/1.0 200 OK
```

### B. Traffic Camera Feed Node List
```bash
curl -s "http://localhost:8000/api/cameras?feed=traffic"
# Expected: JSON object with keys "last_updated" and "cameras" (active highway cams)
```

### C. Zoo Camera Feed Node List
```bash
curl -s "http://localhost:8000/api/cameras?feed=zoo"
# Expected: JSON object with 5 mock animal node IDs (zoo_panda, zoo_tiger, etc.)
```

### D. AI Analysis Playground (Simulated/Mock Check)
```bash
curl -s "http://localhost:8000/api/analyze?feed=zoo&url=https://images.unsplash.com/photo-1564349683136-77e08dba1ef7&prompt=describe"
# Expected: {"status": "success", "result": "[SIMULATION] ..."}
```

---

## 5. UI Asset Verification

Verify that the dashboard assets load properly:
* Open `http://localhost:8000` in a browser or test tool.
* Inspect console for Maps API key failures or missing file assets.
* Check feed switching trigger (re-evaluates map centers and sidebar lists dynamically).
