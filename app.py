from flask import Flask
import os
from dotenv import load_dotenv
from controllers.AppController import AppController
from views.main import main_blueprint
from controllers.helpers import upload_asset

# Load environment variables
load_dotenv(override=True)

def create_app():
    app = Flask(__name__)
    BASE_DIR = os.getcwd()

    # Configure dossier directories
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'uploads')
    app.config['DOWNLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'downloads')
    app.config['CONFIG'] = os.path.join(BASE_DIR, 'public', 'config')
    app.config['ODOO'] = os.path.join(BASE_DIR, 'app', 'odoo')

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CONFIG'], exist_ok=True)

    odoo_folder = app.config['ODOO']
    upload_asset(odoo_folder)

    # Register blueprints
    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        app_controller = AppController()
        app_controller.initialize_directories()
    app.run(host="0.0.0.0", port=5000, debug=True)

