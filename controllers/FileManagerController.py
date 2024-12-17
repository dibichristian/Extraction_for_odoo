import os
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

class FileManagerController:

    def generate_unique_filename(self, base_path, extension=None, extract=None):
        """Génère un nom de fichier unique pour éviter les conflits."""
        timestamps = datetime.now().strftime('%d_%m_%Y_%H%M%S')
        timestamp = datetime.now().strftime('%d_%m_%Y')
        if extension:
            if extract:
                name = f"{base_path}_{extract}_{timestamps}.{extension}"
            else:
                name = f"{base_path}_{timestamps}.{extension}"
            return name
        else:
            name = f"{base_path}_{timestamp}"
            if not os.path.exists(name):
                os.makedirs(name, exist_ok=True)
            return name

    def list_files(self, path=""):
        """Liste tous les fichiers et dossiers dans le répertoire des téléchargements."""
        try:
            download_folder = current_app.config['DOWNLOAD_FOLDER']
            full_path = os.path.abspath(os.path.join(download_folder, path))

            if not full_path.startswith(download_folder) or not os.path.exists(full_path):
                return {"error": f"Path {path} not found."}, 404

            items = os.listdir(full_path)
            files = []
            directories = []

            for item in items:
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    directories.append(item)
                elif os.path.isfile(item_path):
                    file_size = os.path.getsize(item_path)
                    last_modified_time = os.path.getmtime(item_path)
                    last_modified_date = datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
                    extention = os.path.splitext(item_path)
                    files.append({'name': item, 'size': file_size, 'last_modified': last_modified_date, 'extension': extention[1]})

            return {"directories": directories, "files": files, "current_path": path}
        except Exception as e:
            print(f"Erreur lors de la liste des fichiers : {e}")
            return {"error": "Une erreur s'est produite lors de l'accès au chemin."}, 500

    def upload_file(self, file):
        """
        Gère le téléchargement de fichiers.
        """
        try:
            if not file or file.filename == '':
                raise ValueError("Aucun fichier fourni ou le fichier est vide.")

            upload_folder = current_app.config['UPLOAD_FOLDER']

            file_name, file_extension = os.path.splitext(file.filename)
            if file_extension.lower() not in ['.csv', '.xlsx']:
                raise ValueError("Seuls les fichiers .csv et .xlsx sont autorisés.")

            filename = self.generate_unique_filename(file_name, file_extension)
            save_path = os.path.join(upload_folder, filename)

            # Sauvegarder le fichier
            file.save(save_path)
            return save_path
        except Exception as e:
            print(f"Erreur lors de l'upload du fichier : {e}")
            return None

    def download_file(self, filename):
        """
        Gère le téléchargement de fichiers.
        """
        # filename = secure_filename(filename)
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        return send_from_directory(download_folder, filename)

    def delete_file(self, filename):
        """
        Gère la suppression de fichiers.
        """
        # filename = secure_filename(filename)
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        file_path = os.path.join(download_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"File {filename} deleted.", 200
        return f"File {filename} not found.", 404

