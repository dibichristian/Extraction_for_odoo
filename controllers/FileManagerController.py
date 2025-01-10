import csv
import os
from flask import current_app, send_from_directory
from openpyxl import Workbook
from werkzeug.utils import secure_filename
from datetime import datetime
from controllers.ToolController import ToolController

tool = ToolController()

class FileManagerController:

    def generate_unique_filename(self, base_name, extension=None, extract=None):
        """
        Génère un nom de fichier unique pour éviter les conflits.
        """
        timestamps = datetime.now().strftime('%d_%m_%Y_%H%M')
        timestamp = datetime.now().strftime('%d_%m_%Y')
        if extract:
            filename = f"{base_name}_{extract}_{timestamps}"
        else:
            filename = f"{base_name}_{timestamp}"

        if extension:
            filename += f".{extension.lstrip('.')}"
        
        return secure_filename(filename)

    def list_files(self, path=""):
        """
        Liste les fichiers et répertoires dans le dossier de téléchargement.
        """
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
                    file_extension = os.path.splitext(item_path)[1]
                    files.append({
                        'name': item,
                        'size': file_size,
                        'last_modified': last_modified_date,
                        'extension': file_extension,
                    })

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
                return tool.response_function(0, "Aucun fichier fourni ou le fichier est vide.", 401)

            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            file_name, file_extension = os.path.splitext(file.filename)
            if file_extension.lower() not in ['.csv', '.xlsx']:
                return tool.response_function(0, "Seuls les fichiers .csv et .xlsx sont autorisés.", 401)

            # Générer un nom unique et sauvegarder
            filename = self.generate_unique_filename(file_name, file_extension)
            save_path = os.path.join(upload_folder, filename)

            file.save(save_path)
            return tool.response_function(1, "Fichier téléchargé avec succès.", save_path)
        except Exception as e:
            print(f"Erreur lors de l'upload du fichier : {e}")
            return tool.response_function(0, str(e), 500)

    def download_file(self, filename):
        """
        Gère le téléchargement de fichiers.
        """
        try:
            download_folder = current_app.config['DOWNLOAD_FOLDER']
            return send_from_directory(download_folder, filename, as_attachment=True)
        except Exception as e:
            print(f"Erreur lors du téléchargement du fichier : {e}")
            return {"error": "Le fichier n'existe pas ou une erreur s'est produite."}, 404

    def delete_file(self, filename):
        """
        Gère la suppression de fichiers.
        """
        try:
            filename = secure_filename(filename)
            download_folder = current_app.config['DOWNLOAD_FOLDER']
            file_path = os.path.join(download_folder, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                return {"message": f"Fichier {filename} supprimé."}, 200
            return {"error": f"Fichier {filename} non trouvé."}, 404
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier : {e}")
            return {"error": "Une erreur s'est produite lors de la suppression."}, 500

    def file_exists(self, filename):
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        
        filename = os.path.join(download_folder, filename)
        print(os.path.exists(filename))
        if os.path.exists(filename):
            return tool.response_function(1, 0,'Fichier existant')
        else:
            return tool.response_function(0, 'Fichier inexistant', 404)
        
    def subdivide_csv_sheet(self, input_file, interval=5000, required_columns=["partner_id/id"]):
        """
        Divise un fichier CSV en sous-intervalles et génère un fichier XLSX 
        avec plusieurs feuilles représentant chaque sous-intervalle.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        file_output = input_file.replace('.csv', '.xlsx')
        files = input_file
        input_file = os.path.join(download_folder, input_file)
        try:
            # Charger le fichier CSV
            with open(input_file, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                data = list(reader)
            
            nombre_de_lignes_sans_entete = len(data) - 1

            if nombre_de_lignes_sans_entete < interval:
                return self.download_file(files)

            header = data[0]  # La première ligne est l'en-tête
            print(f"En-têtes détectées : {header}")
            required_column_indices = [header.index(col_name) for col_name in required_columns]
            
            # Créer un nouveau fichier XLSX
            workbook = Workbook()
            del workbook["Sheet"]  # Supprimer la feuille par défaut

            current_row = 1  # Commence après l'en-tête
            sheet_counter = 1

            # Parcourir les lignes en blocs définis par l'intervalle
            while current_row < len(data):
                end_row = min(current_row + interval, len(data))
                
                # Réduire l'intervalle tant que les cellules des colonnes définies sont vides
                while end_row > current_row:
                    if all(data[end_row - 1][col_index] is not None and data[end_row - 1][col_index].strip() != '' for col_index in required_column_indices):
                        end_row -= 1
                        break
                    end_row -= 1

                # Si end_row est inférieur à current_row, cela signifie qu'il n'a pas trouvé de ligne non vide
                if end_row <= current_row:
                    end_row = current_row + interval

                # Ajouter une nouvelle feuille pour chaque intervalle
                sheet_name = f"Part_{sheet_counter}"
                worksheet = workbook.create_sheet(title=sheet_name)

                # Ajouter l'en-tête principal
                worksheet.append(header)

                # Copier les données de la plage sélectionnée
                for row in data[current_row:end_row-1]:
                    worksheet.append(row)

                # Copier la ligne de référence pour le prochain intervalle, si nécessaire
                if end_row < len(data):
                    next_row_data = data[end_row-1]
                    worksheet.append(next_row_data)

                # Mettre à jour les compteurs pour le prochain intervalle
                current_row = end_row
                sheet_counter += 1

            output_file = input_file.replace('.csv', '.xlsx')       # Sauvegarder le fichier XLSX final
            workbook.save(output_file)
            print(f"Fichier généré : {output_file}")
            print(file_output)
            return self.download_file(file_output)
        except ValueError as e:
            print(f"Erreur de validation : {e}")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
