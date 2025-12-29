from flask import Flask, render_template_string, jsonify
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import random
import json
import os

app = Flask(__name__)

# Community page URL (replace with actual)
URL = "https://www.adopt-me-values.com/pets"

# History file
HISTORY_FILE = "pet_values_history.json"

# Load history if exists
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
else:
    history = []

def fetch_pet_values():
    try:
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, "html.parser")

        pet_values = {}
        for pet_div in soup.find_all("div", class_="pet"):
            name = pet_div.find("h2").text
            value = pet_div.find("p").text.replace(",", "")
            try:
                value = int(value)
            except:
                value = 0
            pet_values[name] = value

        timestamp = str(datetime.now())
        history.append({"timestamp": timestamp, "values": pet_values})

        # Save to JSON
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

        print(f"[{timestamp}] Pet values updated.")
    except Exception as e:
        print(f"Error fetching values: {e}")

# Scheduler: daily at random time 1-5 AM
scheduler = BackgroundScheduler()
hour = random.randint(1,5)
minute = random.randint(0,59)
scheduler.add_job(fetch_pet_values, 'cron', hour=hour, minute=minute)
scheduler.start()

# Initial fetch
fetch_pet_values()

# HTML template with Plotly chart
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Adopt Me Pet Values - Stock Chart</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Adopt Me Pet Values (Stock Chart)</h1>
    <div id="chart" style="width:90%;height:600px;"></div>
    <script>
        const history = {{ history | safe }};
        const pets = new Set();
        history.forEach(entry => {
            Object.keys(entry.values).forEach(pet => pets.add(pet));
        });

        const traces = [];
        pets.forEach(pet => {
            const x = [];
            const y = [];
            history.forEach(entry => {
                if (entry.values[pet] !== undefined) {
                    x.push(entry.timestamp);
                    y.push(entry.values[pet]);
                }
            });
            traces.push({
                x: x,
                y: y,
                mode: 'lines+markers',
                name: pet
            });
        });

        const layout = {
            title: 'Adopt Me Pet Values Over Time',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Value', autorange: true },
            height: 600
        };

        Plotly.newPlot('chart', traces, layout);
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, history=history)

# API endpoints
@app.route("/api/latest")
def api_latest():
    return jsonify(history[-1] if history else {})

@app.route("/api/history")
def api_history():
    return jsonify(history)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
