from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import io
import requests
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
from urllib.parse import urlparse
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store images and their animation types in memory
# In production, you'd want to use a database or session
session_storage = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fetch-image', methods=['POST'])
def fetch_image():
    if 'url' not in request.json:
        return jsonify({'status': 'error', 'message': 'No URL provided'}), 400
    
    url = request.json['url']
    
    # Validate URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return jsonify({'status': 'error', 'message': 'Invalid URL format'}), 400
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid URL format'}), 400
    
    try:
        # Fetch the image
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return jsonify({'status': 'error', 'message': f'URL does not point to an image: {content_type}'}), 400
        
        # Generate a filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename or '.' not in filename:
            filename = f"image_{uuid.uuid4().hex}.jpg"
        
        # Make the filename safe
        filename = secure_filename(filename)
        
        # Generate a session ID if not present
        session_id = request.json.get('session_id')
        if not session_id:
            session_id = uuid.uuid4().hex
            session_storage[session_id] = {'images': [], 'animations': []}
        elif session_id not in session_storage:
            session_storage[session_id] = {'images': [], 'animations': []}
        
        # Save the image
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Generate a base64 preview for immediate display
        image = Image.open(io.BytesIO(response.content))
        # Resize for preview if needed
        image.thumbnail((400, 400))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Add to session storage
        session_storage[session_id]['images'].append(file_path)
        session_storage[session_id]['animations'].append("None")
        
        return jsonify({
            'status': 'success', 
            'filename': filename,
            'path': file_path,
            'preview': img_str,
            'session_id': session_id,
            'index': len(session_storage[session_id]['images']) - 1
        })
        
    except requests.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Failed to fetch image: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error processing image: {str(e)}'}), 500


@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    
    try:
        # Generate a session ID if not present
        session_id = request.form.get('session_id')
        if not session_id:
            session_id = uuid.uuid4().hex
            session_storage[session_id] = {'images': [], 'animations': []}
        elif session_id not in session_storage:
            session_storage[session_id] = {'images': [], 'animations': []}
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Generate a base64 preview
        image = Image.open(file_path)
        # Resize for preview
        image.thumbnail((400, 400))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Add to session storage
        session_storage[session_id]['images'].append(file_path)
        session_storage[session_id]['animations'].append("None")
        
        return jsonify({
            'status': 'success', 
            'filename': filename,
            'path': file_path,
            'preview': img_str,
            'session_id': session_id,
            'index': len(session_storage[session_id]['images']) - 1
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error processing image: {str(e)}'}), 500


@app.route('/remove-image', methods=['POST'])
def remove_image():
    session_id = request.json.get('session_id')
    index = request.json.get('index')
    
    if not session_id or session_id not in session_storage:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    try:
        index = int(index)
        if index < 0 or index >= len(session_storage[session_id]['images']):
            return jsonify({'status': 'error', 'message': 'Invalid image index'}), 400
        
        # Remove the image from session storage
        del session_storage[session_id]['images'][index]
        if index < len(session_storage[session_id]['animations']):
            del session_storage[session_id]['animations'][index]
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error removing image: {str(e)}'}), 500


@app.route('/update-animation', methods=['POST'])
def update_animation():
    session_id = request.json.get('session_id')
    index = request.json.get('index')
    animation = request.json.get('animation')
    
    if not session_id or session_id not in session_storage:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    try:
        index = int(index)
        if index < 0 or index >= len(session_storage[session_id]['images']):
            return jsonify({'status': 'error', 'message': 'Invalid image index'}), 400
        
        # Update the animation type
        session_storage[session_id]['animations'][index] = animation
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating animation: {str(e)}'}), 500


@app.route('/update-all-animations', methods=['POST'])
def update_all_animations():
    session_id = request.json.get('session_id')
    animation = request.json.get('animation')
    
    if not session_id or session_id not in session_storage:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    try:
        # Update all animation types
        num_images = len(session_storage[session_id]['images'])
        session_storage[session_id]['animations'] = [animation] * num_images
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating animations: {str(e)}'}), 500


@app.route('/create-gif', methods=['POST'])
def create_gif():
    session_id = request.json.get('session_id')
    duration = request.json.get('duration')
    loop = request.json.get('loop')
    transition_frames = request.json.get('transition_frames')
    
    if not session_id or session_id not in session_storage:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    try:
        duration = int(duration)
        loop = int(loop)
        transition_frames = int(transition_frames)
        
        if duration <= 0:
            return jsonify({'status': 'error', 'message': 'Duration must be greater than 0'}), 400
        
        if transition_frames < 0:
            return jsonify({'status': 'error', 'message': 'Transition frames must be 0 or greater'}), 400
        
        # Get the images
        image_paths = session_storage[session_id]['images']
        animations = session_storage[session_id]['animations']
        
        if not image_paths:
            return jsonify({'status': 'error', 'message': 'No images to create GIF'}), 400
        
        # Load images
        images = [Image.open(path) for path in image_paths]
        
        # Resize all images to the same size (using the size of the first image)
        base_width, base_height = images[0].size
        resized_images = []
        
        for img in images:
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
        
        # Create a unique filename for the GIF
        output_filename = f"output_{uuid.uuid4().hex}.gif"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Save as gif
        final_frames[0].save(
            output_path,
            format='GIF',
            append_images=final_frames[1:],
            save_all=True,
            duration=duration,
            loop=loop,
            optimize=False
        )
        
        return jsonify({
            'status': 'success', 
            'filename': output_filename,
            'path': output_path
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error creating GIF: {str(e)}'}), 500


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


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True) 