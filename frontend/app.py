"""
Flask Application - Frontend Server

Serves HTML pages for admin and user interfaces.
Proxies API calls to FastAPI backend.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from functools import wraps

from frontend.config import Config


app = Flask(__name__)
app.config.from_object(Config)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            return redirect(url_for('login'))
        if session.get('role') not in ['admin', 'prompt_engineer']:
            return render_template('error.html', error="Admin access required"), 403
        return f(*args, **kwargs)
    return decorated_function


# Root route
@app.route('/')
def index():
    """Homepage - redirect based on login status"""
    if 'token' in session:
        if session.get('role') in ['admin', 'prompt_engineer']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_chat'))
    return redirect(url_for('login'))


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        # Call FastAPI auth endpoint
        try:
            response = requests.post(
                f"{app.config['FASTAPI_URL']}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                token_data = response.json()
                token = token_data['access_token']

                # Get user info
                user_response = requests.get(
                    f"{app.config['FASTAPI_URL']}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )

                if user_response.status_code == 200:
                    user_info = user_response.json()
                    session['token'] = token
                    session['username'] = user_info['username']
                    session['role'] = user_info['role']

                    if request.is_json:
                        return jsonify({"success": True, "role": user_info['role']})
                    return redirect(url_for('index'))

            error = response.json().get('detail', 'Login failed')
            if request.is_json:
                return jsonify({"success": False, "error": error}), 401
            return render_template('user/login.html', error=error)

        except Exception as e:
            error = f"Connection error: {str(e)}"
            if request.is_json:
                return jsonify({"success": False, "error": error}), 500
            return render_template('user/login.html', error=error)

    return render_template('user/login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


# User routes
@app.route('/user/chat')
@login_required
def user_chat():
    """User chat interface"""
    return render_template('user/chat.html', username=session.get('username'))


@app.route('/user/variables')
@login_required
def user_variables():
    """User variables management"""
    return render_template('user/variables.html', username=session.get('username'))


# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin/index.html', username=session.get('username'))


@app.route('/admin/prompts')
@admin_required
def admin_prompts():
    """Prompt editor page"""
    return render_template('admin/prompts.html', username=session.get('username'))


@app.route('/admin/examples')
@admin_required
def admin_examples():
    """Learning examples manager"""
    return render_template('admin/examples.html', username=session.get('username'))


@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Analytics dashboard"""
    return render_template('admin/analytics.html', username=session.get('username'))


@app.route('/admin/llm-config')
@admin_required
def admin_llm_config():
    """LLM provider configuration"""
    return render_template('admin/llm_config.html', username=session.get('username'))


# API Proxy routes (to avoid CORS issues from frontend)
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_proxy(path):
    """Proxy API requests to FastAPI backend"""
    token = session.get('token')
    url = f"{app.config['FASTAPI_URL']}/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, params=request.args, timeout=200)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.get_json(), timeout=200)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.get_json(), timeout=200)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=200)

        return jsonify(response.json()), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
