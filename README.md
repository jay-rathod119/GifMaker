# GIF Maker

A Python application that allows you to fetch images from URLs or select local images to create animated GIFs with custom transitions.

## Vercel Deployment

This project can be deployed on Vercel as a serverless application. Due to the limitations of serverless environments, the version deployed on Vercel offers limited functionality compared to the full desktop version.

### Deployment Issues

If you encounter the error `500: INTERNAL_SERVER_ERROR Code: FUNCTION_INVOCATION_FAILED`, this is likely because:

1. Serverless functions can't write to the filesystem persistently
2. The app originally used local file storage for images and GIFs
3. Memory limitations in serverless environments

### How to Fix

The repository now includes a Vercel-compatible version in the `api/` directory. This version:

- Stores images in memory using base64 encoding
- Provides a simplified interface
- Removes features that are incompatible with serverless environments

To deploy on Vercel:

1. Push the code to GitHub
2. Connect your Vercel account to GitHub
3. Select the repository
4. Configure as follows:
   - Framework: Other
   - Root Directory: ./
   - Build Command: (leave default)
   - Output Directory: (leave default)

## Local Development

For local development with full functionality:

```bash
pip install -r requirements.txt
python app.py
```

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