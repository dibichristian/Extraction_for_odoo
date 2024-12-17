import os
import subprocess
from flask import Flask
from dotenv import load_dotenv
from views.main import main_blueprint

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    BASE_DIR = os.getcwd()
    # URL du dépôt distant
    GIT_REPO_URL = "https://github.com/tfrancoi/odoo_csv_import.git"

    # Configure uploads and downloads directories
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'uploads')
    app.config['DOWNLOAD_FOLDER'] = os.path.join(BASE_DIR, 'public', 'downloads')
    app.config['TEMP'] = os.path.join(BASE_DIR, 'public', 'temp')
    app.config['CONFIG'] = os.path.join(BASE_DIR, 'public', 'config')
    app.config['ODOO'] = os.path.join(BASE_DIR, 'app', 'odoo')

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CONFIG'], exist_ok=True)
    os.makedirs(app.config['TEMP'], exist_ok=True)

    odoo_folder = app.config['ODOO']
    
    # Étape 1 : Créer le dossier s'il n'existe pas
    if not os.path.exists(odoo_folder):
        print("Création du dossier ODOO...")
        os.makedirs(odoo_folder)

        # Étape 2 : Cloner le projet depuis le dépôt distant
        print("Clonage du dépôt distant...")
        clone_command = ["git", "clone", GIT_REPO_URL, odoo_folder]
        try:
            subprocess.run(clone_command, check=True)
            print("Dépôt cloné avec succès !")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors du clonage du dépôt : {e}")
            return

        # Étape 3 : Installer les dépendances via requirements.txt
        requirements_path = os.path.join(os.path.join(BASE_DIR, 'static'), 'requirements.txt')
        if os.path.exists(requirements_path):
            print("Installation des dépendances...")
            install_command = ["pip", "install", "-r", requirements_path]
            try:
                subprocess.run(install_command, check=True)
                print("Dépendances installées avec succès !")
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de l'installation des dépendances : {e}")
        else:
            print("Fichier requirements.txt introuvable dans le dépôt cloné.")

    # Register blueprints
    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000,debug=True)
