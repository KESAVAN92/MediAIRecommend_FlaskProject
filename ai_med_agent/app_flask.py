import sqlite3
import pandas as pd
import os
import logging
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from agent import ask_agent

app = Flask(__name__)
app.secret_key = 'ai_med_agent_secret_key'


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    medicine TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()


medicines_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'medicines.csv'))

def save_query(query, medicine, answer):
    medicines_list = medicines_df['Medicine'].tolist()
    medicine = 'Unknown'
    for med in medicines_list:
        if med.lower() in answer.lower():
            medicine = med
            break
    db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO queries (query, medicine, answer, timestamp) VALUES (?, ?, ?, ?)",
              (query, medicine, answer, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_recent_queries(limit=10):
    db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT query, medicine, answer FROM queries ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_top_medicines(limit=5):
    db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT medicine, COUNT(*) as count FROM queries WHERE medicine != 'Unknown' GROUP BY medicine ORDER BY count DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/bot", methods=["GET", "POST"])
def bot():
    if request.method == "POST":
        user_input = request.form.get("query")
        if user_input:
            answer = ask_agent(user_input)
            save_query(user_input, '', answer)  # Pass empty medicine, will be extracted in save_query
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'answer': answer})
    history = get_recent_queries(10)
    return render_template("index.html", history=[{'query': q, 'answer': a} for q, _, a in history])

@app.route("/recommendations")
def recommendations():
    recommendations_data = medicines_df[['Symptom', 'Medicine', 'Alternatives']].to_dict('records')
    recent_queries = get_recent_queries(5)
    top_medicines = get_top_medicines(5)
    similar_medicines = [m for _, m, _ in recent_queries]
    return render_template("recommendations.html", recommendations=recommendations_data,
                           recent=recent_queries, top=top_medicines, similar=similar_medicines)

@app.route("/history")
def history():
    queries = get_recent_queries(50)
    return render_template("history.html", queries=queries)

@app.route("/clear_history", methods=["POST"])
def clear_history():
    db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM queries")
    conn.commit()
    conn.close()
    return redirect(url_for('history'))

@app.route("/welcome")
def welcome():
    logging.info(f"Request received: {request.method} {request.path}")
    return jsonify({"message": "Welcome to the AI Med Agent API!"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
