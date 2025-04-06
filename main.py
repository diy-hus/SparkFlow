from flask import Flask, request, render_template
import sqlite3
from datetime import datetime
import requests
import os

app = Flask(__name__)

# Lấy API Key từ Secrets
GEMINI_API_KEY = os.getenv("AIzaSyA1H4Oa2CJ362v9ySlid4ISJb6PTVkZDXs")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def init_db():
    conn = sqlite3.connect('plans.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plans 
                 (id INTEGER PRIMARY KEY, schedule TEXT, stress INTEGER, hobbies TEXT, plan TEXT, timestamp TEXT)'''
              )
    conn.commit()
    conn.close()


@app.route('/')
def home():
    init_db()
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_plan():
    try:
        if not GEMINI_API_KEY:
            raise ValueError(
                "Gemini API Key is missing. Add it to Secrets as GEMINI_API_KEY."
            )

        schedule = request.form['schedule']
        stress = int(request.form['stress'])
        hobbies = request.form['hobbies']
        timestamp = datetime.now().strftime('%Y-%m-d %H:%M:%S')

        # Tạo prompt cho Gemini
        prompt = f"""
        Create a concise relaxation plan based on:
        - Daily schedule: {schedule}
        - Stress level (1-10): {stress}
        - Hobbies: {hobbies}
        Suggest specific activities with times that fit the schedule and reduce stress.
        Format as a bullet list (e.g., - 15 mins activity at 6 PM).
        """

        # Gọi Gemini API
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                                 json=payload,
                                 headers=headers)
        response.raise_for_status()  # Ném lỗi nếu không thành công
        plan = response.json(
        )['candidates'][0]['content']['parts'][0]['text'].strip()

        # Lưu vào cơ sở dữ liệu
        conn = sqlite3.connect('plans.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO plans (schedule, stress, hobbies, plan, timestamp) VALUES (?, ?, ?, ?, ?)",
            (schedule, stress, hobbies, plan, timestamp))
        conn.commit()
        conn.close()

        return render_template('result.html', plan=plan)
    except Exception as e:
        return f"Error in generate_plan: {str(e)}", 500


@app.route('/history')
def history():
    try:
        conn = sqlite3.connect('plans.db')
        c = conn.cursor()
        c.execute(
            "SELECT schedule, stress, hobbies, plan, timestamp FROM plans")
        plans = c.fetchall()
        conn.close()
        return render_template('history.html', plans=plans)
    except Exception as e:
        return f"Error in history: {str(e)}", 500


@app.route('/stats')
def stats():
    try:
        conn = sqlite3.connect('plans.db')
        c = conn.cursor()
        c.execute("SELECT stress, timestamp FROM plans ORDER BY timestamp")
        data = c.fetchall()
        conn.close()

        if data:
            stress_levels = [row[0] for row in data]
            timestamps = [row[1] for row in data]
            avg_stress = sum(stress_levels) / len(stress_levels)
        else:
            stress_levels = []
            timestamps = []
            avg_stress = 0

        return render_template('stats.html',
                               avg_stress=avg_stress,
                               stress_levels=stress_levels,
                               timestamps=timestamps)
    except Exception as e:
        return f"Error in stats: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
