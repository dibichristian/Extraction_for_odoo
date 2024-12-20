import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def upload_asset(odoo_folder):
    BASE_DIR = os.getcwd()
    git_repo_url = GIT_REPO_URL = "https://github.com/tfrancoi/odoo_csv_import.git"
    # Étape 1 : Créer le dossier s'il n'existe pas
    if not os.path.exists(os.path.join(odoo_folder, 'odoo_export_thread.py')):
        print("Création du dossier ODOO...")

        # Étape 2 : Cloner le projet depuis le dépôt distant
        print("Clonage du dépôt distant...")
        clone_command = ["git", "clone", git_repo_url, odoo_folder]
        try:
            result = subprocess.run(clone_command, check=True)
            print("Dépôt cloné avec succès !")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors du clonage du dépôt : {e}")
            return

        # Étape 3 : Installer les dépendances via requirements.txt
        requirements_path = os.path.join(BASE_DIR, 'static', 'requirements.txt')
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
