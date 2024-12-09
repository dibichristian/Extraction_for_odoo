import os
from flask import Flask
from dotenv import load_dotenv
from views.main import main_blueprint

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    BASE_DIR = os.getcwd()

    # Configure uploads and downloads directories
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'uploads')
    app.config['DOWNLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'downloads')
    app.config['TEMP'] = os.path.join(BASE_DIR, 'public', 'temp')
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
