from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from PIL import Image
import io
import base64
import uuid
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# For Vercel, we'll use in-memory storage since we can't write to filesystem
SESSIONS = {}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Serve the main page for all routes
    return render_template('index.html')

@app.route('/api/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {'images': []}
    return jsonify({'session_id': session_id})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # Get the session ID from the request
    session_id = request.form.get('session_id')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if the file has a name
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read the image
        img_data = file.read()
        img = Image.open(io.BytesIO(img_data))
        
        # Resize if needed (optional)
        max_size = (800, 800)
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Save image in memory (base64)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Add to session
        image_id = str(uuid.uuid4())
        SESSIONS[session_id]['images'].append({
            'id': image_id,
            'name': file.filename,
            'data': img_str  # Store base64 data instead of file path
        })
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'image_id': image_id,
            'image_url': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-image', methods=['POST'])
def fetch_image():
    # Get the session ID and URL from the request
    data = request.json
    session_id = data.get('session_id')
    url = data.get('url')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Parse the URL to get the filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Download the image
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download image'}), 400
        
        # Open the image
        img_data = response.content
        img = Image.open(io.BytesIO(img_data))
        
        # Resize if needed
        max_size = (800, 800)
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Save image in memory (base64)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Add to session
        image_id = str(uuid.uuid4())
        SESSIONS[session_id]['images'].append({
            'id': image_id,
            'name': filename or 'downloaded_image.png',
            'data': img_str  # Store base64 data instead of file path
        })
        
        return jsonify({
            'success': True,
            'message': 'Image fetched successfully',
            'image_id': image_id,
            'image_url': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-gif', methods=['POST'])
def generate_gif():
    # Simplified version that just returns a message for now
    return jsonify({
        'success': True,
        'message': 'This is a preview version. Full GIF creation is available in the downloadable version.'
    })

# Vercel handler
def handler(environ, start_response):
    return app(environ, start_response) 