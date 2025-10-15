from flask import Flask, render_template, request, session, jsonify
from agent import ask_agent

app = Flask(__name__)
app.secret_key = 'ai_med_agent_secret_key'

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        history = session.get('history', [])
        user_input = request.form.get("query")
        if user_input:
            answer = ask_agent(user_input)
            history.append({'query': user_input, 'answer': answer})
            if len(history) > 10:
                history = history[-10:]
            session['history'] = history
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'answer': answer})
    else:
        session['history'] = []
    history = session.get('history', [])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'history': history})
    return render_template("index.html", history=history)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
