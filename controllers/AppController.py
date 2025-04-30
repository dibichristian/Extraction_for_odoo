import os
import logging
import subprocess
from flask import current_app
from controllers.ToolController import ToolController

tool = ToolController()


class AppController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def initialize_directories(self):
        """
        Initialise les dossiers nécessaires à l'application (à appeler dans un contexte Flask).
        """
        if not current_app:
            raise RuntimeError("Cette méthode doit être appelée dans le contexte d'une application Flask.")

        # Récupérer les configurations
        config_path = current_app.config.get('CONFIG', 'config')
        odoo_path = current_app.config.get('ODOO', 'odoo')

        # Créer les répertoires nécessaires
        os.makedirs(config_path, exist_ok=True)
        os.makedirs(odoo_path, exist_ok=True)

        self.logger.info(f"Répertoires initialisés : CONFIG={config_path}, ODOO={odoo_path}")

    def connect_file_create(self):
        """
        Crée un fichier de configuration pour la connexion à Odoo.
        """
        file_odoo_app = current_app.config['CONFIG']
        connect_file = os.path.join(file_odoo_app, 'connection.conf')

        if not os.path.exists(connect_file):
            try:
                print("ODDO_HOST =", os.getenv("ODOO_HOST"))
                file_content = f"""[Connection]
hostname = {os.getenv('ODOO_HOST')}
database = {os.getenv('ODOO_DATABASE')}
login = {os.getenv('ODOO_LOGIN')}
password = {os.getenv('ODOO_PASSWORD')}
protocol = jsonrpcs
port = {os.getenv('ODOO_PORT', 443)}
uid = {os.getenv('ODOO_UID', 2)}
"""
                with open(connect_file, "w", encoding="utf-8") as file:
                    file.write(file_content)
                logging.info(f"Fichier de configuration créé: {connect_file}")
            except Exception as e:
                logging.error(f"Erreur lors de la création du fichier de configuration: {e}")
                raise ValueError(f"Erreur lors de la création du fichier de configuration: {e}")

        return connect_file


    def export_odoo_data(self, modele, colonne, fichier, domain='[]'):
        """
        Exporter les données depuis Odoo vers un fichier CSV.
        """
        if not modele or not colonne or not fichier:
            return tool.response_function(0, "Paramètres invalides", "Modele, colonne ou fichier manquant.")

        if not os.path.exists(fichier):
            self.initialize_directories()
            
            # Commande de base pour l'exportation
            base_command = [
                "python", "odoo_export_thread.py",
                "-c", self.connect_file_create(),
                f"--file={fichier}",
                f"--model={modele}",
                "--worker=2",
                "--size=200",
                f"--domain={domain}",
                f"--field={colonne}",
                "--sep=;",
                "--encoding=utf-8-sig"
            ]

            execution_directory = current_app.config['ODOO']

            try:
                logging.info(f"Exécution de la commande: {' '.join(base_command)} dans {execution_directory}")
                result = subprocess.run(
                    base_command, cwd=execution_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600
                )

                if result.returncode != 0:
                    error_details = result.stderr.decode('utf-8', errors='replace')
                    logging.error(f"Erreur lors de l'exportation: {error_details}")
                    return tool.response_function(0, "Erreurs lors de l'exportation", error_details)
                else:
                    logging.info(f"Exportation terminée avec succès. Fichier créé: {fichier}")
                    return tool.response_function(1, "Exportation terminée. Fichier créé", fichier)

            except subprocess.TimeoutExpired:
                logging.error("L'exportation a dépassé le délai imparti.")
                return tool.response_function(0, "L'exportation a dépassé le délai imparti.", 0)

            except Exception as e:
                logging.exception("Une erreur imprévue est survenue.")
                return tool.response_function(0, "Erreur imprévue", e)

        else:
            logging.info(f"Fichier existant: {fichier}")
            return tool.response_function(1, "Fichier existant", fichier)
