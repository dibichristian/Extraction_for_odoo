import os
import csv
import zipfile
import pandas as pd
from datetime import datetime
from flask import current_app, send_from_directory
from controllers.FileManagerController import FileManagerController
from controllers.AppController import AppController

file_manager = FileManagerController()
data_odoo = AppController()

class FileConfigController:
    
    def drop_columns(self, df, columns_to_drop):
        """Supprime les colonnes spécifiques d'un DataFrame."""
        df.columns = df.columns.str.strip()  # Nettoie les noms de colonnes
        columns_to_drop = [col.strip() for col in columns_to_drop]  # Nettoie les noms à supprimer
        df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True)
        return df

    def order_columns(self, df, column_order):
        """
        Réorganise les colonnes d'un DataFrame selon un ordre spécifié
        et modifie la colonne "Date" en ajoutant un "-" après chaque 2 caractères.
        
        :param df: Le DataFrame à modifier.
        :param column_order: La liste des colonnes dans l'ordre souhaité.
        :return: Un DataFrame avec les colonnes réorganisées.
        """
        # Convertion de la Colonne Date au format date de Odoo
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], format="%d%m%y").dt.strftime("%Y-%m-%d")

        # Garder uniquement les colonnes spécifiées dans column_order
        new_order = [col for col in column_order if col in df.columns]
        
        # Retourner le DataFrame avec les colonnes dans le nouvel ordre
        return df[new_order]



    def delete_data_based_on_column(self, df, check_column, target_value, columns_to_clear):
        """Supprime les données des colonnes spécifiées si une valeur cible est trouvée dans une colonne donnée."""
        df.loc[df[check_column] == target_value, columns_to_clear] = None
        return df

    def keep_only_columns(self, df, columns_to_keep):
        """Conserve uniquement les colonnes spécifiées dans un DataFrame."""
        return df[[col for col in columns_to_keep if col in df.columns]]

    def mark_duplicates(self, df, column_name, duplicate_col_name="Doublon", yes_value="OUI", no_value="NON"):
        """Marque les doublons dans une colonne d'un DataFrame."""
        if duplicate_col_name in df.columns:
            df.drop(columns=[duplicate_col_name], inplace=True)
        df[duplicate_col_name] = df.duplicated(subset=[column_name], keep="first").apply(lambda x: yes_value if x else no_value)
        return df


    def add_comparison_results(self, df, additional_data, column2, column1, column3, result_column):
        """
        Ajoute les résultats de la comparaison entre deux DataFrames et retourne une liste des éléments non trouvés.
        """
        additional_data.columns = additional_data.columns.str.strip()
        df.columns = df.columns.str.strip()

        # Supprimer les espaces dans les valeurs des colonnes concernées
        additional_data[column1] = additional_data[column1].astype(str).str.strip()
        additional_data[column3] = additional_data[column3].astype(str).str.strip()
        df[column2] = df[column2].astype(str).str.strip()

        # Créer un dictionnaire de correspondance à partir de additional_data
        lookup_dict = dict(zip(additional_data[column1], additional_data[column3]))

        # Appliquer le dictionnaire de correspondance
        df[result_column] = df[column2].map(lookup_dict)

        # Identifier les éléments non trouvés
        missing_elements = df[df[result_column].isna()][column2].unique()

        # Retourner le DataFrame mis à jour et les éléments non trouvés
        return df, missing_elements


    def rename_columns(self, df, column_mapping):
        """
        Renomme les colonnes d'un DataFrame selon un dictionnaire de mappage.

        Args:
            df (pd.DataFrame): Le DataFrame à modifier.
            column_mapping (dict): Dictionnaire de mappage {ancien_nom: nouveau_nom}.

        Returns:
            pd.DataFrame: Le DataFrame avec les colonnes renommées.
        """
        df.rename(columns=column_mapping, inplace=True)
        return df

    def process_import_files(self, file_configs, output_path, column_order, entete, column_mapping, pathname, filename):
        """
        Traite un ou plusieurs fichiers Excel ou CSV, applique les transformations nécessaires,
        et exporte les résultats dans un seul fichier CSV.
        """
        all_dataframes = []  # Liste pour stocker tous les DataFrames à concaténer
        error = None
        success = None

        for config in file_configs:
            try:
                file_path = config.get("file")
                comparisons = config.get("comparaison", [])
                
                # Charger le fichier principal
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                else:
                    print(f"Format de fichier non pris en charge : {file_path}")
                    continue

                print(f"Traitement du fichier : {file_path}")

                # Comparaisons multiples
                for comparison in comparisons:
                    comparison_file = comparison.get("file")
                    column1 = comparison.get("colonne1")
                    column2 = comparison.get("colonne2")
                    column3 = comparison.get("colonne3")
                    result_column = comparison.get("resultat")

                    if comparison_file:
                        if comparison_file.endswith('.csv'):
                            additional_data = pd.read_csv(comparison_file, sep=';')
                        elif comparison_file.endswith('.xlsx'):
                            additional_data = pd.read_excel(comparison_file)
                        else:
                            print(f"Fichier de comparaison non pris en charge : {comparison_file}")
                            error = f"Fichier de comparaison non pris en charge : {comparison_file}"
                            additional_data = None

                        if additional_data is not None:
                            df, missing_elements = self.add_comparison_results(df, additional_data, column2, column1, column3, result_column)
                            if len(missing_elements) > 0:
                                return {
                                    "type": "Erreur",
                                    "Resultat": f"Les Produits suivants n'ont pas été trouvés, veuillez les mettre à jour dans Odoo :\n{missing_elements}",
                                }

                # Réorganiser les colonnes selon l'ordre souhaité
                df = self.order_columns(df, column_order)

                # Marquer les doublons
                df = self.mark_duplicates(df, column_name="Référence", duplicate_col_name="Doublon")

                # Supprimer les données dans les colonnes spécifiées si "Doublon" est "OUI"
                df = self.delete_data_based_on_column(df, check_column="Doublon", target_value="OUI", columns_to_clear=entete)

                # Renommer les colonnes selon le mappage fourni
                df = self.rename_columns(df, column_mapping)

                # Ajouter le DataFrame traité à la liste
                all_dataframes.append(df)

                print(f"Fichier traité avec succès : {file_path}")

            except Exception as e:
                print(f"Erreur lors du traitement du fichier {file_path} : {e}")
                error = f"Erreur lors du traitement du fichier {file_path} : {e}"

        # Concaténer tous les DataFrames en un seul
        if all_dataframes:
            final_df = pd.concat(all_dataframes, ignore_index=True)
            final_df.to_csv(output_path, index=False, sep=",", encoding="utf-8-sig")
            print(f"Traitement terminé avec succès : {output_path}")
            success = f"Traitement terminé avec succès : {filename}"
        else:
            print("Aucune donnée valide n'a été trouvée.")
            error = "Aucune donnée valide n'a été trouvée."
            
        if error != None:
            return { 'type' : 'Erreur', 'Resultat' : error}
        else:
            return { 'type' : 'Succes', 'Resultat' : success, 'Path': pathname}
    
    def transition(self, file, extract):
        verif = self.verif_move(file, extract)
        
        if verif['status'] == 'Succès':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            download_folder = current_app.config['DOWNLOAD_FOLDER']
            file_configs = self.get_congif(file, upload_folder, extract)
            path_name = file_manager.generate_unique_filename(os.path.join(download_folder, 'Import_du'))
            if extract == 'Fni':
                move = 'Fournisseur'
            elif extract == 'Clt':
                move = 'Client'
            else:
                move = 'Autres'
            file_mane = file_manager.generate_unique_filename('Import','csv', extract=move)
            result = f"{path_name}/{file_mane}"
            output_path = os.path.join(download_folder, result)
            column = self.get_fiedls_odoo(extract)
            entete = column['Entete']
            column_mapping = column['Mapping']
            column_order = column['Column']
            procees = self.process_import_files(file_configs, output_path, column_order, entete, column_mapping, path_name, file_mane)
            return procees
        else:
            return { 'type' : verif['status'], 'Resultat' : verif['message']}
    
    def get_headers(self, file_path, separator=None):
        """
        Retourne les entêtes (noms des colonnes) d'un fichier .xlsx ou .csv.
        
        :param file_path: Chemin du fichier (xlsx ou csv).
        :return: Liste des noms de colonnes ou un message d'erreur.
        """
        try:
            
            # Vérifier l'extension du fichier
            if file_path.endswith('.csv'):
                # Lire le fichier CSV
                df = pd.read_csv(file_path, nrows=0, sep=separator)  # Charger uniquement les entêtes
            elif file_path.endswith('.xlsx'):
                # Lire le fichier Excel
                df = pd.read_excel(file_path, nrows=0)  # Charger uniquement les entêtes
            else:
                return f"Format non pris en charge : {file_path}"
            
            # Retourner les noms des colonnes
            return list(df.columns)
        except Exception as e:
            return f"Erreur lors de la lecture du fichier : {str(e)}"
    
    def get_fiedls_odoo(self, move):
        if move == 'Clt':
            return {
                'Column'  : ["Référence", "Date", "Client", "Produit", "Description", "Prix unitaire", "Quantité", "Remise"],
                'Entete' : ["Référence", "Date", "Client"],
                'Mapping' : {
                    "Référence": "origine",
                    "Date": "date_order",
                    "Client": "partner_id/id",
                    "Produit": "order_line/product_id",
                    "Description": "order_line/name",
                    "Prix unitaire": "order_line/price_unit",
                    "Quantité": "order_line/quantity",
                    "Remise": "order_line/discount"
                }
            }
        elif move == 'Fni':
            return {
                'Column'  : ["Référence", "Date", "Fournisseur", "Produit", "Description", "Prix unitaire", "Quantité", "Remise"],
                'Entete' : ["Référence", "Date", "Fournisseur"],
                'Mapping' : {
                    "Référence": "origine_ref",
                    "Date": "date",
                    "Fournisseur": "partner_id/id",
                    "Produit": "invoice_line_ids/product_id",
                    "Description": "invoice_line_ids/name",
                    "Prix unitaire": "invoice_line_ids/price_unit",
                    "Quantité": "invoice_line_ids/quantity",
                    "Remise": "invoice_line_ids/discount"
                }
            }
            
    def get_congif(self, file, path, move):
        if move == 'Clt':  
            partner = "Client"
        else :
            partner = "Fournisseur"
        file_configs = [
                {
                    "file": file,
                    "comparaison": [
                        {
                            "file": self.get_entity_odoo("res_partner"),
                            "colonne1": "ref",
                            "colonne2": partner,
                            "colonne3": "id",
                            "resultat": partner
                        },
                        {
                            "file": self.get_entity_odoo("product_template"),
                            "colonne1": "default_code",
                            "colonne2": "Produit",
                            "colonne3": "display_name",
                            "resultat": "Produit"
                        }
                    ]
                }
            ]
        return file_configs

    def cleaning_data(self, data):
        """
        Nettoie et renomme les colonnes d'un fichier CSV/XLSX selon les noms dans 'Column'.
        La sortie est toujours un fichier CSV.
        """
        try:
            # Récupération des colonnes à traiter pour le type de mouvement
            odoo_field_info = self.get_fiedls_odoo(data['extract'])
            columns_to_process = odoo_field_info['Column']
            # Lecture du fichier chargé (CSV ou XLSX)
            input_file = data['uploaded_file']
            if input_file.endswith('.csv'):
                df = pd.read_csv(input_file, sep=data['sep'])
            elif input_file.endswith('.xlsx'):
                df = pd.read_excel(input_file, engine='openpyxl')
            else:
                raise ValueError(f"Format de fichier non pris en charge : {input_file}")

            # Boucle pour renommer les colonnes spécifiées
            for column in columns_to_process:
                if column in data:  # Vérifie si une nouvelle colonne est spécifiée dans les données
                    self.rename_column(df, data[column], column)

            # Déterminer le chemin de sortie pour le fichier CSV
            output_file = input_file.rsplit('.', 1)[0] + '_cleaned.csv'
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Fichier nettoyé sauvegardé sous : {output_file}")
            return output_file  # Retourne le chemin du fichier généré

        except Exception as e:
            print(f"Erreur lors du nettoyage des données : {e}")
            return None


    def rename_column(self, df, old_name, new_name):
        """
        Renomme une colonne dans un DataFrame en suivant les règles spécifiées.
        """
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
        else:
            print(f"Colonne '{old_name}' introuvable dans le fichier.")
    
    def verif_move(self, file, move):
        """
        Vérifie les données du fichier en fonction du type de mouvement (Client ou Fournisseur).
        """
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Chargement du fichier principal
        if file.endswith('.csv'):
            df = pd.read_csv(file, sep=",")
        elif file.endswith('.xlsx'):
            df = pd.read_excel(file, engine='openpyxl')
        else:
            raise ValueError(f"Format de fichier non pris en charge : {file}")

        print("Colonnes disponibles dans le DataFrame principal :", df.columns.tolist())

        # Chargement du fichier partenaire
        partner_file_path = self.get_entity_odoo("res_partner")
        if type(partner_file_path) != str:
            print("Erreur lors de l'export : res_partner")
            return {
                "status": "Erreur",
                "message": partner_file_path['message']
            }

        partner = pd.read_csv(partner_file_path, sep=";")

        # Configuration des colonnes selon le type de mouvement
        if move == 'Clt':  
            col2 = "Client"
            col3 = "customer_rank"
        else:
            col2 = "Fournisseur"
            col3 = "supplier_rank"

        # Vérification de l'existence des colonnes
        for col in [col2]:
            if col not in df.columns:
                raise KeyError(f"La colonne '{col}' est absente du fichier chargé.")

        # Ajout des résultats de la comparaison
        df, missing_elements = self.add_comparison_results(df, partner, col2, "ref", col3, 'Verif')

        # Convertir la colonne 'Verif' en numérique
        try:
            df['Verif'] = pd.to_numeric(df['Verif'], errors='coerce')  # Convertit en NaN les valeurs non numériques
        except Exception as e:
            raise ValueError(f"Erreur lors de la conversion de la colonne 'Verif' : {e}")

        # Filtrer uniquement les lignes avec des valeurs non nulles dans 'Verif'
        valid_rows = df[df['Verif'].notnull()]

        # Identifier les lignes invalides parmi les lignes non nulles : valeurs <= 0
        invalid_rows = valid_rows[valid_rows['Verif'] <= 0]

        # Si des lignes invalides existent, les retourner
        if not invalid_rows.empty:
            print("Lignes invalides détectées :", invalid_rows)
            return {
                "status": "Erreur",
                "message": f"Les données de votre colonne {col2} ne correspondent pas aux données {col2} de la base de données Odoo",
                "invalid_data": invalid_rows.to_dict(orient='records')  # Retourne les lignes invalides sous forme de dictionnaire
            }
        elif len(missing_elements) > 0:
            return {
                "status": "Erreur",
                "message": f"Les Clients suivants n'ont pas été trouvés, veuillez les mettre à jour dans Odoo :\n{missing_elements}",
            }

        # Si tout est valide
        return {
            "status": "Succès",
            "message": "Tous les enregistrements valides ont été vérifiés avec succès.",
            "data": valid_rows.to_dict(orient='records')  # Retourne uniquement les lignes valides sous forme de dictionnaire
        }

    def get_entity_odoo(self, entity):

        file_config = current_app.config['CONFIG']
        
        if entity == 'res_partner':
            file = os.path.join(file_config, file_manager.generate_unique_filename('res_partner', 'csv'))
            action = data_odoo.export_odoo_data(entity.replace("_", "."), 'id,ref,customer_rank,supplier_rank', file)
        elif entity == 'product_template':
            file = os.path.join(file_config, file_manager.generate_unique_filename('product_template', 'csv'))
            action = data_odoo.export_odoo_data(entity.replace("_", "."), 'id,display_name,default_code', file)
        
        if action['Status'] == 'Erreur':
            return {'Status': 'Erreur', 'Message': action['Message']}
        else:
            return file


    #Scinder pour import
    import openpyxl
    import csv

    def get_column_index(sheet, column_name):
        """Retourne l'index de la colonne basée sur le nom de la colonne."""
        for col in sheet.iter_cols(1, sheet.max_column):
            if col[0].value == column_name:
                return col[0].column
        raise ValueError(f"Colonne '{column_name}' non trouvée dans la feuille.")


    def subdivide_csv_sheet(self, input_file, output_file_prefix, interval, required_columns):
        """
        Divise un fichier CSV en plusieurs sous-fichiers selon un intervalle de lignes.

        :param input_file: Chemin du fichier CSV d'entrée.
        :param output_file_prefix: Préfixe pour les fichiers de sortie.
        :param interval: Intervalle de lignes pour chaque sous-fichier.
        :param required_columns: Colonnes requises pour vérifier les lignes vides.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        # Charger le fichier CSV
        with open(os.path.join(download_folder, input_file), mode='r', newline='', encoding='ISO-8859-1') as file:
            reader = csv.reader(file, delimiter=',')
            data = list(reader)

        header = data[0]  # La première ligne est l'en-tête
        required_column_indices = [header.index(col_name) for col_name in required_columns]

        # Variables pour suivre les lignes et les fichiers
        current_row = 1  # Commence après l'en-tête
        file_counter = 1
        output_files = []  # Liste pour stocker les fichiers créés

        # Parcourir les lignes en blocs définis par l'intervalle
        while current_row < len(data):
            end_row = min(current_row + interval, len(data))

            # Réduire l'intervalle tant que les cellules des colonnes définies sont vides
            while end_row > current_row:
                if all(data[end_row - 1][col_index] is not None and data[end_row - 1][col_index] != '' 
                       for col_index in required_column_indices):
                    end_row -= 1
                    break
                end_row -= 1

            # Si end_row est inférieur à current_row, cela signifie qu'il n'a pas trouvé de ligne non vide
            if end_row <= current_row:
                end_row = current_row + interval

            # Créer un nouveau fichier CSV pour chaque intervalle
            output_file = f"{output_file_prefix}_{file_counter}.csv"
            output_files.append(output_file)
            with open(os.path.join(download_folder, output_file), mode='w', newline='', encoding='utf-8') as new_file:
                writer = csv.writer(new_file, delimiter=',')

                # Ajouter l'en-tête principal
                writer.writerow(header)

                # Copier les données de la plage sélectionnée
                for row in data[current_row:end_row - 1]:
                    writer.writerow(row)

                # Copier la ligne de référence pour le prochain intervalle, si nécessaire
                if end_row < len(data):
                    next_row_data = data[end_row - 1]
                    writer.writerow(next_row_data)

            # Mettre à jour les compteurs pour le prochain intervalle
            current_row = end_row
            file_counter += 1
        file_download = f"{output_file_prefix}_combined.zip"
        # Appeler la fonction pour regrouper les fichiers en un fichier ZIP
        self.combine_csv_files(output_files, file_download)

        return file_manager.download_file(file_download)


    def for_import(self, input_file):
        """
        Vérifie si le fichier contient plus de lignes que l'intervalle.
        - Si oui : subdivise le fichier CSV.
        - Sinon : lance le téléchargement du fichier.

        :param input_file: Le chemin du fichier CSV à traiter.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        output_file = input_file.replace('.csv', '')  # Correction de "remplace" -> "replace"
        interval = 5000
        required_columns = ["partner_id/id"]

        # Lire le fichier CSV pour compter les lignes
        try:
            df = pd.read_csv(os.path.join(download_folder, input_file))
            total_rows = len(df)

            # Vérifier si le nombre de lignes dépasse l'intervalle
            if total_rows > interval:
                print(f"Le fichier contient {total_rows} lignes, ce qui dépasse l'intervalle de {interval}.")
                return self.subdivide_csv_sheet(input_file, output_file, interval, required_columns)
            else:
                print(f"Le fichier contient seulement {total_rows} lignes. Téléchargement en cours...")
                return file_manager.download_file(input_file)
        except Exception as e:
            return f"Erreur lors de la lecture du fichier : {e}"

    def combine_csv_files(self, file_list, zip_filename):
        """
        Combine une liste de fichiers CSV dans une archive ZIP.

        :param file_list: Liste des fichiers CSV à regrouper.
        :param zip_filename: Nom du fichier ZIP de sortie.
        """
        download_folder = current_app.config['DOWNLOAD_FOLDER']

        print(f"Création du fichier ZIP : {zip_filename}")
        with zipfile.ZipFile(os.path.join(download_folder, zip_filename), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in file_list:
                zipf.write(os.path.join(download_folder, file), os.path.basename(os.path.join(download_folder, file)))
                print(f"Ajout du fichier : {file}")

        # Optionnel : Supprimer les fichiers individuels après les avoir regroupés
        for file in file_list:
            os.remove(os.path.join(download_folder, file))
            print(f"Suppression du fichier temporaire : {file}")

        print(f"Le fichier ZIP {zip_filename} est prêt pour le téléchargement.")