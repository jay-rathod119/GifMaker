# GIF Maker

A Python application that allows you to fetch images from URLs or select local images to create animated GIFs with custom transitions.

## Features

- Modern, user-friendly interface using CustomTkinter
- Fetch images directly from URLs
- Browse and select local image files
- Preview images before creating GIFs
- Customize GIF settings (duration, loop count)
- **Apply various transition animations between frames:**
  - None (simple frame change)
  - Instant (no transition)
  - Fade in
  - Slide up
  - Slide down
  - Slide right
  - Slide left
  - Grow
  - Shrink
- Customize the number of transition frames
- Create animated GIFs from selected images
- Resize and normalize images automatically

## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- CustomTkinter
- Requests

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install Pillow customtkinter requests
```

## Usage

1. Run the application:

```bash
python gif_maker_app.py
```

2. Add images using one of the following methods:
   - Enter an image URL and click "Fetch Image"
   - Click "Browse Files" to select local images

3. Apply animations to your images:
   - Select an animation type from the dropdown menu
   - Click "Apply to Selected Image" to apply to the current image
   - Click "Apply to All Images" to apply the same animation to all images

4. Configure GIF settings:
   - Frame Duration (milliseconds)
   - Loop Count (0 for infinite loop)
   - Transition Frames (how many frames to use for transitions)

5. Click "Create GIF" to generate and save your animated GIF

## Project Structure

```
gif_maker/
├── gif_maker_app.py  # Main application file
├── images/           # Directory for storing fetched images
├── output/           # Directory for saving created GIFs
└── README.md         # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.