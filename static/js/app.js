document.addEventListener('DOMContentLoaded', function() {
    // Variables
    let sessionId = null;
    let images = [];
    let currentPreviewIndex = -1;
    let isCreatingGif = false;

    // DOM elements
    const imageUrlInput = document.getElementById('imageUrl');
    const fetchImageBtn = document.getElementById('fetchImage');
    const imageFileInput = document.getElementById('imageFile');
    const animationTypeSelect = document.getElementById('animationType');
    const applyToSelectedBtn = document.getElementById('applyToSelected');
    const applyToAllBtn = document.getElementById('applyToAll');
    const frameDurationInput = document.getElementById('frameDuration');
    const loopCountInput = document.getElementById('loopCount');
    const transitionFramesInput = document.getElementById('transitionFrames');
    const createGifBtn = document.getElementById('createGif');
    const previewArea = document.getElementById('previewArea');
    const previewControls = document.querySelector('.preview-controls');
    const prevImageBtn = document.getElementById('prevImage');
    const nextImageBtn = document.getElementById('nextImage');
    const imageCounter = document.getElementById('imageCounter');
    const imageList = document.getElementById('imageList');
    const removeSelectedBtn = document.getElementById('removeSelected');
    const resultCard = document.getElementById('resultCard');
    const resultGif = document.getElementById('resultGif');
    const downloadLink = document.getElementById('downloadLink');
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    const bsToast = new bootstrap.Toast(toast);

    // Initialize session
    createSession();

    // Event listeners
    fetchImageBtn.addEventListener('click', fetchImage);
    imageFileInput.addEventListener('change', uploadImages);
    applyToSelectedBtn.addEventListener('click', applyAnimationToSelected);
    applyToAllBtn.addEventListener('click', applyAnimationToAll);
    createGifBtn.addEventListener('click', createGif);
    prevImageBtn.addEventListener('click', showPreviousImage);
    nextImageBtn.addEventListener('click', showNextImage);
    removeSelectedBtn.addEventListener('click', removeSelectedImage);

    // Functions
    function createSession() {
        fetch('/api/session', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            sessionId = data.session_id;
            console.log('Session created:', sessionId);
        })
        .catch(error => {
            showToast('Error', 'Failed to create session: ' + error.message);
        });
    }

    function fetchImage() {
        const url = imageUrlInput.value.trim();
        if (!url) {
            showToast('Error', 'Please enter an image URL');
            return;
        }

        if (!sessionId) {
            showToast('Error', 'No active session');
            return;
        }

        showLoading(true);
        fetch('/api/fetch-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                url: url
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.error) {
                showToast('Error', data.error);
                return;
            }
            
            addImageToUI(data.image);
            imageUrlInput.value = '';
            showToast('Success', 'Image fetched successfully');
        })
        .catch(error => {
            showLoading(false);
            showToast('Error', 'Failed to fetch image: ' + error.message);
        });
    }

    function uploadImages() {
        if (!sessionId) {
            showToast('Error', 'No active session');
            return;
        }

        const files = imageFileInput.files;
        if (files.length === 0) return;

        showLoading(true);
        let uploadedCount = 0;

        Array.from(files).forEach(file => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', sessionId);

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                uploadedCount++;
                if (data.error) {
                    showToast('Error', `Failed to upload ${file.name}: ${data.error}`);
                } else {
                    addImageToUI(data.image);
                }
                
                if (uploadedCount === files.length) {
                    showLoading(false);
                    if (uploadedCount > 0) {
                        showToast('Success', `${uploadedCount} image(s) uploaded successfully`);
                    }
                    imageFileInput.value = '';
                }
            })
            .catch(error => {
                uploadedCount++;
                showToast('Error', `Failed to upload ${file.name}: ${error.message}`);
                
                if (uploadedCount === files.length) {
                    showLoading(false);
                    imageFileInput.value = '';
                }
            });
        });
    }

    function addImageToUI(image) {
        // Add to our array
        images.push({
            id: image.id,
            filename: image.filename,
            thumbnail: image.thumbnail,
            animation: 'None'
        });

        // Update image list
        updateImageList();

        // Show image preview if this is the first image
        if (images.length === 1) {
            currentPreviewIndex = 0;
            updatePreview();
        }
    }

    function updateImageList() {
        // Clear the list
        imageList.innerHTML = '';

        // Add each image
        images.forEach((image, index) => {
            const item = document.createElement('a');
            item.className = `list-group-item image-item ${index === currentPreviewIndex ? 'active' : ''}`;
            item.href = 'javascript:void(0)';
            item.dataset.id = image.id;
            item.dataset.index = index;
            
            item.innerHTML = `
                <img src="${image.thumbnail}" class="image-item-thumbnail" alt="${image.filename}">
                <span>${image.filename}</span>
                <span class="badge animation-badge ms-auto">${image.animation}</span>
            `;
            
            item.addEventListener('click', () => {
                currentPreviewIndex = parseInt(item.dataset.index);
                updatePreview();
                updateImageList(); // Update active state
            });
            
            imageList.appendChild(item);
        });

        // Update UI state
        updateUIState();
    }

    function updatePreview() {
        if (images.length === 0 || currentPreviewIndex < 0 || currentPreviewIndex >= images.length) {
            previewArea.innerHTML = `
                <div class="no-images">
                    <i class="bi bi-images display-1 text-muted"></i>
                    <p class="text-muted">No images loaded</p>
                </div>
            `;
            previewControls.classList.add('d-none');
            imageCounter.textContent = '0/0';
            return;
        }

        const image = images[currentPreviewIndex];
        previewArea.innerHTML = `<img src="${image.thumbnail}" alt="${image.filename}">`;
        previewControls.classList.remove('d-none');
        imageCounter.textContent = `${currentPreviewIndex + 1}/${images.length}`;

        // Update animation selection to match the current image
        animationTypeSelect.value = image.animation;
    }

    function updateUIState() {
        const hasImages = images.length > 0;
        const hasSelectedImage = currentPreviewIndex >= 0 && currentPreviewIndex < images.length;
        
        // Update button states
        createGifBtn.disabled = !hasImages || isCreatingGif;
        removeSelectedBtn.disabled = !hasSelectedImage;
        applyToSelectedBtn.disabled = !hasSelectedImage;
        applyToAllBtn.disabled = !hasImages;
        prevImageBtn.disabled = !hasImages || images.length <= 1;
        nextImageBtn.disabled = !hasImages || images.length <= 1;
    }

    function showPreviousImage() {
        if (images.length === 0) return;
        
        currentPreviewIndex = (currentPreviewIndex - 1 + images.length) % images.length;
        updatePreview();
        updateImageList();
    }

    function showNextImage() {
        if (images.length === 0) return;
        
        currentPreviewIndex = (currentPreviewIndex + 1) % images.length;
        updatePreview();
        updateImageList();
    }

    function removeSelectedImage() {
        if (images.length === 0 || currentPreviewIndex < 0 || currentPreviewIndex >= images.length) {
            return;
        }

        const imageId = images[currentPreviewIndex].id;
        
        fetch('/api/remove-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                image_id: imageId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error);
                return;
            }
            
            // Remove from our array
            images.splice(currentPreviewIndex, 1);
            
            // Update preview index
            if (images.length > 0) {
                currentPreviewIndex = Math.min(currentPreviewIndex, images.length - 1);
            } else {
                currentPreviewIndex = -1;
            }
            
            // Update UI
            updatePreview();
            updateImageList();
            showToast('Success', 'Image removed');
        })
        .catch(error => {
            showToast('Error', 'Failed to remove image: ' + error.message);
        });
    }

    function applyAnimationToSelected() {
        if (images.length === 0 || currentPreviewIndex < 0 || currentPreviewIndex >= images.length) {
            showToast('Error', 'No image selected');
            return;
        }

        const imageId = images[currentPreviewIndex].id;
        const animationType = animationTypeSelect.value;
        
        fetch('/api/set-animation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                image_id: imageId,
                animation_type: animationType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error);
                return;
            }
            
            // Update our array
            images[currentPreviewIndex].animation = animationType;
            
            // Update UI
            updateImageList();
            showToast('Success', `Applied '${animationType}' animation to selected image`);
        })
        .catch(error => {
            showToast('Error', 'Failed to apply animation: ' + error.message);
        });
    }

    function applyAnimationToAll() {
        if (images.length === 0) {
            showToast('Error', 'No images loaded');
            return;
        }

        const animationType = animationTypeSelect.value;
        
        fetch('/api/set-all-animations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                animation_type: animationType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error);
                return;
            }
            
            // Update our array
            images.forEach(image => {
                image.animation = animationType;
            });
            
            // Update UI
            updateImageList();
            showToast('Success', `Applied '${animationType}' animation to all images`);
        })
        .catch(error => {
            showToast('Error', 'Failed to apply animation to all: ' + error.message);
        });
    }

    function createGif() {
        if (images.length === 0) {
            showToast('Error', 'No images to create GIF');
            return;
        }

        // Get settings
        const duration = parseInt(frameDurationInput.value);
        const loop = parseInt(loopCountInput.value);
        const transitionFrames = parseInt(transitionFramesInput.value);
        
        // Validate input
        if (isNaN(duration) || duration <= 0) {
            showToast('Error', 'Duration must be greater than 0');
            return;
        }
        
        if (isNaN(loop) || loop < 0) {
            showToast('Error', 'Loop count must be 0 or greater');
            return;
        }
        
        if (isNaN(transitionFrames) || transitionFrames < 0) {
            showToast('Error', 'Transition frames must be 0 or greater');
            return;
        }
        
        isCreatingGif = true;
        createGifBtn.disabled = true;
        createGifBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
        
        showLoading(true);
        
        fetch('/api/create-gif', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                duration,
                loop,
                transition_frames: transitionFrames
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            isCreatingGif = false;
            createGifBtn.disabled = false;
            createGifBtn.innerHTML = 'Create GIF';
            
            if (data.error) {
                showToast('Error', data.error);
                return;
            }
            
            // Show the result
            resultGif.innerHTML = `<img src="${data.gif_url}" alt="Created GIF">`;
            downloadLink.href = data.gif_url;
            downloadLink.download = data.filename;
            resultCard.classList.remove('d-none');
            
            // Scroll to result
            resultCard.scrollIntoView({ behavior: 'smooth' });
            
            showToast('Success', 'GIF created successfully');
        })
        .catch(error => {
            showLoading(false);
            isCreatingGif = false;
            createGifBtn.disabled = false;
            createGifBtn.innerHTML = 'Create GIF';
            showToast('Error', 'Failed to create GIF: ' + error.message);
        });
    }

    function showLoading(show) {
        // Remove existing loading overlay if any
        const existingOverlay = document.querySelector('.loading-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        if (show) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            document.body.appendChild(overlay);
        }
    }

    function showToast(title, message) {
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        bsToast.show();
    }
}); 