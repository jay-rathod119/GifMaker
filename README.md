# GIF Maker Web Application

A web-based application for creating GIFs from images with various transition animations.

## Features

- Upload images from your device
- Import images from URLs
- Apply different transition animations between images
- Customize GIF settings (duration, loop count, transition frames)
- Preview images before creating the GIF
- Download the created GIF

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd gif-maker
```

2. Create a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:
```
pip install -r requirements.txt
```

## Running Locally

Start the application with:
```
python app.py
```

The application will be available at http://127.0.0.1:5000/

## Deploying to Production

### Using Gunicorn (Linux/Mac)

1. Install Gunicorn:
```
pip install gunicorn
```

2. Run the application:
```
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using Waitress (Windows)

1. Install Waitress:
```
pip install waitress
```

2. Create a file named `wsgi.py` with the following content:
```python
from waitress import serve
from app import app

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8000)
```

3. Run the application:
```
python wsgi.py
```

### Deploying to a Cloud Provider

This application can be deployed to various cloud providers:

#### Heroku

1. Create a `Procfile` with the following content:
```
web: gunicorn app:app
```

2. Deploy to Heroku:
```
heroku create
git push heroku main
```

#### AWS Elastic Beanstalk

1. Create a file named `.ebextensions/python.config`:
```
option_settings:
  "aws:elasticbeanstalk:container:python":
    WSGIPath: app:app
```

2. Deploy using the EB CLI:
```
eb init
eb create
```

## Directory Structure

- `app.py` - The main Flask application
- `templates/` - HTML templates
- `uploads/` - Temporary storage for uploaded images
- `output/` - Storage for generated GIFs

## Usage

1. Upload images using either the URL input or the file upload option
2. Navigate through images using the Previous/Next buttons
3. Apply animations to individual images or all images at once
4. Set the GIF parameters (duration, loop count, transition frames)
5. Click "Create GIF" to generate your GIF
6. Download the generated GIF using the provided link

## License

MIT 