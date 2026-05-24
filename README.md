# What's Up Bay Area

> Every camera. Every road. One conversation.

The Bay Area has hundreds of live traffic cameras, zoo livestreams, and real-time road data — but it's all raw, scattered, and unreadable. **What's Up Bay Area** connects to those public feeds and lets Google Gemini tell you what's actually happening, right now, in plain English.

---

## Features

### 🚦 Live Traffic Feeds
Browse 150+ real Caltrans highway cameras across the Bay Area. Ask Gemini anything about what it sees — traffic density, hazards, weather visibility. Filter by route or county, click any camera to open an AI sandbox.

### 🐼 Zoo Animal Cams
Watch live zoo feeds from California and let Gemini narrate the action — whether the pandas are napping or the penguins are putting on a show.

### ✨ What's Ahead
Enter your origin and destination and Gemini scans every camera along your actual road path — surfacing construction, fog, stalled vehicles, or anything worth knowing before you drive. Findings are plotted on a live map and shown as a categorised list you can click into.

---

## Getting Started

### Prerequisites
- Python 3.11+
- A `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com)
- Optionally a `GOOGLE_MAPS_API_KEY` for the map embed

### Setup

```bash
git clone https://github.com/adityajain93/google-hackathon.git
cd google-hackathon
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_key_here   # optional
```

### Run

```bash
python server.py
```

Open [http://localhost:8000](http://localhost:8000).

---

## Project Structure

```
inputs/          # Data ingestion (Caltrans CCTV feed, Zoo feeds)
intelligence/    # Gemini client and analyzer
agents/          # Background agents (safety, car count, scavenger)
outputs/
  ui/            # Frontend (index.html, scavenger.html, about.html)
  notifier.py    # Alert dispatcher
server.py        # HTTP server + API routes
```

---

## Built With

- **Google Gemini Vision** — multimodal image analysis
- **Caltrans District 4 CCTV Feed** — 150+ live Bay Area highway cameras
- **Leaflet.js + CartoDB** — interactive dark map, no API key required
- **OpenStreetMap / Nominatim** — free geocoding and address autocomplete
- **OSRM** — open-source routing engine for road path geometry
- **Python `http.server`** — lightweight backend, zero framework dependencies
