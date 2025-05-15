import os
import io
import uuid
import json
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, url_for
from PIL import Image, ImageOps
import requests
from urllib.parse import urlparse

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

# Create the upload and output folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store sessions in memory (would use Redis or a database in production)
SESSIONS = {}

def create_transition_frames(prev_img, next_img, transition_type, num_frames):
    frames = []
    
    # Ensure both images are the same size
    if prev_img.size != next_img.size:
        next_img = next_img.resize(prev_img.size, Image.LANCZOS)
    
    width, height = prev_img.size
    
    # Skip transition if None or Instant is selected, or if num_frames is 0
    if transition_type == "None" or transition_type == "Instant" or num_frames == 0:
        return []
    
    if transition_type == "Fade in":
        # Create a series of images that gradually fade from prev to next
        for i in range(num_frames):
            alpha = i / num_frames
            frame = Image.blend(prev_img.convert("RGBA"), next_img.convert("RGBA"), alpha)
            frames.append(frame.convert("RGB") if frame.mode == "RGBA" else frame)
            
    elif transition_type == "Slide up":
        # Next image slides up from the bottom
        for i in range(num_frames):
            frame = Image.new("RGB", prev_img.size, (255, 255, 255))
            offset = int(height * (1 - i/num_frames))
            # Put the previous image fully visible
            frame.paste(prev_img, (0, 0))
            # Slide the next image up from the bottom
            visible_part = next_img.crop((0, 0, width, height - offset))
            frame.paste(visible_part, (0, offset))
            frames.append(frame)
    
    elif transition_type == "Slide down":
        # Next image slides down from the top
        for i in range(num_frames):
            frame = Image.new("RGB", prev_img.size, (255, 255, 255))
            offset = int(height * (i/num_frames))
            # Put the previous image fully visible
            frame.paste(prev_img, (0, 0))
            # Slide the next image down from the top
            visible_part = next_img.crop((0, offset, width, height))
            frame.paste(visible_part, (0, 0))
            frames.append(frame)
    
    elif transition_type == "Slide right":
        # Next image slides from the left
        for i in range(num_frames):
            frame = Image.new("RGB", prev_img.size, (255, 255, 255))
            offset = int(width * (1 - i/num_frames))
            # Put the previous image fully visible
            frame.paste(prev_img, (0, 0))
            # Slide the next image from the left
            visible_part = next_img.crop((0, 0, width - offset, height))
            frame.paste(visible_part, (offset, 0))
            frames.append(frame)
    
    elif transition_type == "Slide left":
        # Next image slides from the right
        for i in range(num_frames):
            frame = Image.new("RGB", prev_img.size, (255, 255, 255))
            offset = int(width * (i/num_frames))
            # Put the previous image fully visible
            frame.paste(prev_img, (0, 0))
            # Slide the next image from the right
            visible_part = next_img.crop((offset, 0, width, height))
            frame.paste(visible_part, (0, 0))
            frames.append(frame)
    
    elif transition_type == "Grow":
        # Next image grows from center
        for i in range(num_frames):
            frame = Image.new("RGB", prev_img.size, (255, 255, 255))
            scale = i / num_frames
            # Start with previous image
            frame.paste(prev_img, (0, 0))
            # Calculate the size and position of the growing image
            new_width = int(width * scale)
            new_height = int(height * scale)
            left = (width - new_width) // 2
            top = (height - new_height) // 2
            
            if new_width > 0 and new_height > 0:
                growing_img = next_img.resize((new_width, new_height), Image.LANCZOS)
                frame.paste(growing_img, (left, top))
            
            frames.append(frame)
    
    elif transition_type == "Shrink":
        # Previous image shrinks to center
        for i in range(num_frames):
            scale = 1 - (i / num_frames)
            
            # Create a blank frame with next image
            frame = Image.new("RGB", next_img.size, (255, 255, 255))
            frame.paste(next_img, (0, 0))
            
            # Calculate the size and position of the shrinking image
            new_width = max(1, int(width * scale))
            new_height = max(1, int(height * scale))
            left = (width - new_width) // 2
            top = (height - new_height) // 2
            
            if new_width > 0 and new_height > 0:
                shrinking_img = prev_img.resize((new_width, new_height), Image.LANCZOS)
                frame.paste(shrinking_img, (left, top))
            
            frames.append(frame)
    
    return frames

def create_gif(session_id, duration, loop, transition_frames):
    session = SESSIONS.get(session_id)
    if not session or not session.get('images'):
        return None, "No images found in session"
    
    try:
        # Get all images and their animations
        images = session['images']
        animations = session.get('animations', [])
        
        # Set default animations if not provided
        while len(animations) < len(images):
            animations.append("None")
        
        # Resize all images to the same size (using the size of the first image)
        first_img = Image.open(images[0]['path'])
        base_width, base_height = first_img.size
        first_img.close()
        
        resized_images = []
        
        for img_data in images:
            img = Image.open(img_data['path'])
            if img.size != (base_width, base_height):
                resized = img.resize((base_width, base_height), Image.LANCZOS)
                resized_images.append(resized)
            else:
                resized_images.append(img.copy())
        
        # Create the final frames including transitions
        final_frames = []
        
        for i in range(len(resized_images)):
            # Add the current frame
            final_frames.append(resized_images[i])
            
            # Add transition to the next frame if it's not the last frame
            if i < len(resized_images) - 1:
                # Get animation type for the current image
                animation_type = animations[i] if i < len(animations) else "None"
                
                # Create transition frames
                transition = create_transition_frames(
                    resized_images[i], 
                    resized_images[(i + 1) % len(resized_images)],
                    animation_type,
                    transition_frames
                )
                
                # Add transition frames
                final_frames.extend(transition)
        
        # Generate a random filename
        filename = f"gif_{uuid.uuid4().hex}.gif"
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        # Save as gif
        final_frames[0].save(
            filepath,
            format='GIF',
            append_images=final_frames[1:],
            save_all=True,
            duration=duration,
            loop=loop,
            optimize=False
        )
        
        # Close all the images
        for img in resized_images:
            img.close()
        
        return filename, None
    
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        'images': [],
        'animations': []
    }
    return jsonify({'session_id': session_id})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    session_id = request.form.get('session_id')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # Open the image to validate and get dimensions
            with Image.open(filepath) as img:
                width, height = img.size
            
            # Add to session
            image_data = {
                'id': len(SESSIONS[session_id]['images']),
                'filename': file.filename,
                'path': filepath,
                'width': width,
                'height': height
            }
            
            SESSIONS[session_id]['images'].append(image_data)
            SESSIONS[session_id]['animations'].append("None")
            
            # Create thumbnail for preview
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], f"thumb_{filename}")
            with Image.open(filepath) as img:
                img.thumbnail((200, 200))
                img.save(thumbnail_path)
            
            return jsonify({
                'success': True,
                'image': {
                    'id': image_data['id'],
                    'filename': image_data['filename'],
                    'thumbnail': f"/uploads/thumb_{filename}",
                    'width': width,
                    'height': height
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Unknown error'}), 500

@app.route('/api/fetch-image', methods=['POST'])
def fetch_image():
    session_id = request.json.get('session_id')
    image_url = request.json.get('url')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if not image_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return jsonify({'error': f"URL does not point to an image: {content_type}"}), 400
        
        # Generate a filename from URL
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = f"image_{len(SESSIONS[session_id]['images'])}.jpg"
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Open the image to validate and get dimensions
        with Image.open(io.BytesIO(response.content)) as img:
            width, height = img.size
            
            # Save thumbnail for preview
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], f"thumb_{unique_filename}")
            img.thumbnail((200, 200))
            img.save(thumbnail_path)
        
        # Add to session
        image_data = {
            'id': len(SESSIONS[session_id]['images']),
            'filename': filename,
            'path': filepath,
            'width': width,
            'height': height
        }
        
        SESSIONS[session_id]['images'].append(image_data)
        SESSIONS[session_id]['animations'].append("None")
        
        return jsonify({
            'success': True,
            'image': {
                'id': image_data['id'],
                'filename': image_data['filename'],
                'thumbnail': f"/uploads/thumb_{unique_filename}",
                'width': width,
                'height': height
            }
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f"Failed to fetch image: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-animation', methods=['POST'])
def set_animation():
    session_id = request.json.get('session_id')
    image_id = request.json.get('image_id')
    animation_type = request.json.get('animation_type')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if image_id is None:
        return jsonify({'error': 'No image ID provided'}), 400
    
    if not animation_type:
        return jsonify({'error': 'No animation type provided'}), 400
    
    if image_id >= len(SESSIONS[session_id]['images']):
        return jsonify({'error': 'Invalid image ID'}), 400
    
    # Update the animation
    while len(SESSIONS[session_id]['animations']) <= image_id:
        SESSIONS[session_id]['animations'].append("None")
    
    SESSIONS[session_id]['animations'][image_id] = animation_type
    
    return jsonify({'success': True})

@app.route('/api/set-all-animations', methods=['POST'])
def set_all_animations():
    session_id = request.json.get('session_id')
    animation_type = request.json.get('animation_type')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if not animation_type:
        return jsonify({'error': 'No animation type provided'}), 400
    
    # Update all animations
    num_images = len(SESSIONS[session_id]['images'])
    SESSIONS[session_id]['animations'] = [animation_type] * num_images
    
    return jsonify({'success': True})

@app.route('/api/remove-image', methods=['POST'])
def remove_image():
    session_id = request.json.get('session_id')
    image_id = request.json.get('image_id')
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if image_id is None:
        return jsonify({'error': 'No image ID provided'}), 400
    
    if image_id >= len(SESSIONS[session_id]['images']):
        return jsonify({'error': 'Invalid image ID'}), 400
    
    # Remove the image and its animation
    removed_image = SESSIONS[session_id]['images'].pop(image_id)
    
    if image_id < len(SESSIONS[session_id]['animations']):
        SESSIONS[session_id]['animations'].pop(image_id)
    
    # Update the IDs of the remaining images
    for i in range(image_id, len(SESSIONS[session_id]['images'])):
        SESSIONS[session_id]['images'][i]['id'] = i
    
    # Remove the actual file (optional)
    try:
        if os.path.exists(removed_image['path']):
            os.remove(removed_image['path'])
    except:
        pass
    
    return jsonify({'success': True})

@app.route('/api/create-gif', methods=['POST'])
def generate_gif():
    session_id = request.json.get('session_id')
    duration = request.json.get('duration', 200)
    loop = request.json.get('loop', 0)
    transition_frames = request.json.get('transition_frames', 10)
    
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if not SESSIONS[session_id]['images']:
        return jsonify({'error': 'No images in the session'}), 400
    
    try:
        duration = int(duration)
        loop = int(loop)
        transition_frames = int(transition_frames)
        
        if duration <= 0:
            return jsonify({'error': 'Duration must be greater than 0'}), 400
        
        if transition_frames < 0:
            return jsonify({'error': 'Transition frames must be 0 or greater'}), 400
    
    except ValueError:
        return jsonify({'error': 'Invalid numerical values'}), 400
    
    filename, error = create_gif(session_id, duration, loop, transition_frames)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'success': True,
        'gif_url': f"/output/{filename}",
        'filename': filename
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True) 