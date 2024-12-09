import os
from flask import current_app, send_from_directory
import datetime

class FileManagerController:
    def list_files(self, path=""):
        """
        List all files and directories in the downloads directory.
        Allow navigation through subdirectories.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        
        # Construire le chemin complet à partir du chemin par défaut
        full_path = os.path.abspath(os.path.join(download_folder, path))

        # Vérifier que le chemin se trouve toujours dans OUTPUT_FOLDER
        if not full_path.startswith(download_folder) or not os.path.exists(full_path):
            return f"File {path} not found.", 404

        items = os.listdir(full_path)
        files = []
        directories = []

        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            elif os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                last_modified_time = os.path.getmtime(item_path)
                last_modified_date = datetime.datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
                files.append({'name': item, 'size': file_size, 'last_modified': last_modified_date})

        return {"directories": directories, "files": files, "current_path": path}

    def upload_file(self, file):
        """
        Handle file upload.
        """
        upload_folder = current_app.config['UPLOAD_FOLDER']
        save_path = os.path.join(upload_folder, file.filename)
        file.save(save_path)
        return save_path

    def download_file(self, filename):
        """
        Handle file download.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        return send_from_directory(download_folder, filename)

    def delete_file(self, filename):
        """
        Handle file deletion.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        file_path = os.path.join(download_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"File {filename} deleted.", 200
        return f"File {filename} not found.", 404
