import os, subprocess, zipfile, shutil
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
BASE_DIR = "all_bots"
os.makedirs(BASE_DIR, exist_ok=True)
procs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    bot_id = request.form.get('bot_id')
    if not file: return jsonify({"error": "No file"}), 400
    
    bot_path = os.path.join(BASE_DIR, bot_id)
    if os.path.exists(bot_path): shutil.rmtree(bot_path)
    os.makedirs(bot_path)

    zip_path = os.path.join(bot_path, "bot.zip")
    file.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(bot_path)
    return jsonify({"msg": "Deployed Successfully!"})

@app.route('/start/<bot_id>')
def start(bot_id):
    main_py = os.path.join(BASE_DIR, bot_id, "main.py")
    if os.path.exists(main_py):
        p = subprocess.Popen(['python3', main_py], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs[bot_id] = p
        return jsonify({"msg": "Bot Online"})
    return jsonify({"error": "main.py not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
