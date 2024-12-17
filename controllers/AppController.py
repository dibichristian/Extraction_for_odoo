from flask import current_app, send_from_directory
from datetime import datetime
from tqdm import tqdm
import openpyxl
import csv
import subprocess
import os
import time
import logging
import shutil

class AppController:

    def export_odoo_data(self, modele, colonne, fichier, domain='[]'):

        file_odoo_app = current_app.config['ODOO']
        file_config = current_app.config['CONFIG']

        # Commande de base pour l'export
        base_command = [
            "python", "odoo_export_thread.py",
            "-c", self.connect_file_create(),
            f"--file={fichier}",
            f"--model={modele}",
            "--worker=2",
            "--size=200",
            f"--domain={domain}",
            f'--field={colonne}',
            '--sep=;',
            "--encoding=utf-8-sig"
        ]
        
        # Répertoire d'exécution
        execution_directory = os.path.join(file_odoo_app, 'odoo_csv_import')
        # Exécution de la commande
        try:
            result = subprocess.run(base_command, shell=True, cwd=execution_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)

            # Vérification des erreurs dans stderr
            if result.stderr.decode('utf-8', errors='replace'):
                error = f"Erreurs lors de l'exportation : {result.stderr.decode('utf-8', errors='replace')}"
                print(error)
                return {'Status': 'Erreur', 'Message': error}
            else:
                print(f"Exportation terminée. Fichier créé : {fichier}")
                succes = f"Exportation terminée. Fichier créé : {fichier}"
                print(succes)
                return {'Status': 'Succes', 'Message': succes}
        
        except subprocess.TimeoutExpired:
            print("L'exportation a dépassé le délai imparti.")
            error = "L'exportation a dépassé le délai imparti."
            return {'Status': 'Erreur', 'Message': error}
            

    def connect_file_create(self, host='simam-recette-16885367.dev.odoo.com', base='simam-recette-16885367', login='admin', password='admin', port=443, uid=2):
        """
        Crée un fichier de configuration pour la connexion à Odoo.
        """
        if not current_app:
            raise RuntimeError("Cette méthode doit être appelée dans le contexte d'une application Flask.")

        file_odoo_app = current_app.config['CONFIG']
        connect_file = os.path.join(file_odoo_app, 'connection.conf')
        print(connect_file)

        file_content = f"""[Connection]
hostname = {host}
database = {base}
login = {login}
password = {password}
protocol = jsonrpcs
port = {port}
uid = {uid}
"""
        try : 
            with open(connect_file, "w", encoding="utf-8") as file:
                file.write(file_content)
        except Exception as e:
            raise ValueError(f"Erreur lors de la  : {e}")

        return connect_file

        