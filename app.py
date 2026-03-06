import os
from flask import Flask, render_template, request, jsonify
import requests
import urllib.parse
import warnings

# Protobuf import with try-except for safety
PROTO_READY = False
try:
    import my_pb2
    import output_pb2
    PROTO_READY = True
except ImportError:
    print("[!] Warning: PB2 files missing, nickname fetching might fail.")

app = Flask(__name__)
warnings.filterwarnings('ignore')

CLIENT_ID = "100067"
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
USER_AGENT = "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)"

def inspect_token_logic(token):
    """Internal logic to inspect and format token data."""
    url = f"https://100067.connect.garena.com/oauth/token/inspect?token={token}"
    try:
        res = requests.get(url, headers={'ReleaseVersion': 'OB52'}, verify=False, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "status": "success",
                "uid": data.get('uid') or data.get('open_id'),
                "nickname": data.get('nickname', 'N/A'),
                "platform": data.get('platform', 'Garena'),
                "token": token
            }
    except:
        pass
    return {"status": "error", "message": "Valid token, but details not fetched."}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    mode = request.json.get('mode')
    
    if mode == 'id_pass':
        uid = request.json.get('uid')
        pw = request.json.get('password')
        if not uid or not pw:
            return jsonify({"status": "error", "message": "UID and Password are required."})
            
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        payload = {
            'uid': uid, 'password': pw,
            'response_type': "token", 'client_type': "2",
            'client_secret': CLIENT_SECRET, 'client_id': CLIENT_ID
        }
        try:
            res = requests.post(url, data=payload, headers={'User-Agent': USER_AGENT}, verify=False).json()
            if 'access_token' in res:
                return jsonify(inspect_token_logic(res['access_token']))
            else:
                return jsonify({"status": "error", "message": res.get('error_description', 'Invalid Credentials')})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Connection Error: {str(e)}"})

    elif mode == 'eat_url':
        input_data = request.json.get('data')
        if not input_data:
            return jsonify({"status": "error", "message": "Input is required."})
            
        eat_token = input_data
        if 'http' in input_data:
            parsed = urllib.parse.urlparse(input_data)
            params = urllib.parse.parse_qs(parsed.query)
            eat_token = params.get('eat', [None])[0] or params.get('access_token', [None])[0]
        
        if not eat_token:
            return jsonify({"status": "error", "message": "Invalid EAT Token or URL."})
        
        # Garena Support Callback Logic
        url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        try:
            # We need to capture the redirect URL, which contains the final access_token
            res = requests.get(url, allow_redirects=True, verify=False, timeout=15)
            # Inspect the *final* URL after all redirects
            parsed_res = urllib.parse.urlparse(res.url)
            at_params = urllib.parse.parse_qs(parsed_res.query)
            access_token = at_params.get('access_token', [None])[0]
            
            if access_token:
                return jsonify(inspect_token_logic(access_token))
            else:
                return jsonify({"status": "error", "message": "Conversion failed. EAT token might be expired."})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Garena Server Error: {str(e)}"})

    return jsonify({"status": "error", "message": "Invalid Mode"})

if __name__ == '__main__':
    # For local testing, on Render this will be overridden
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
