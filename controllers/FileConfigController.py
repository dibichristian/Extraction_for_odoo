import os
import pandas as pd
from datetime import datetime
from flask import current_app, send_from_directory
from controllers.FileManagerController import FileManagerController

file_manager = FileManagerController()

class FileConfigController:
    
    def generate_unique_filename(self, base_path, extension=None, extract=None):
        """Génère un nom de fichier unique pour éviter les conflits."""
        if extension != None :
            timestamp = datetime.now().strftime('%d_%m_%Y_%H%M%S')
            name = f"{base_path}_{extract}_{timestamp}.{extension}"
        else :
            timestamp = datetime.now().strftime('%d_%m_%Y')
            name = f"{base_path}_{timestamp}"
            if not os.path.exists(name):
                os.makedirs(name, exist_ok=True)
        return name
    
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
        # Ajouter un "-" après chaque 2 caractères dans la colonne "Date", si elle existe
        if "Date" in df.columns:
            df["Date"] = df["Date"].astype(str).apply(lambda x: '-'.join([x[i:i+2] for i in range(0, len(x), 2)]))

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
        Ajoute les résultats de la comparaison entre deux DataFrames.
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
        return df

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
                            additional_data = pd.read_csv(comparison_file)
                        elif comparison_file.endswith('.xlsx'):
                            additional_data = pd.read_excel(comparison_file)
                        else:
                            print(f"Fichier de comparaison non pris en charge : {comparison_file}")
                            error = f"Fichier de comparaison non pris en charge : {comparison_file}"
                            additional_data = None

                        if additional_data is not None:
                            df = self.add_comparison_results(df, additional_data, column2, column1, column3, result_column)
                
                # Marquer les doublons
                df = self.mark_duplicates(df, column_name="Référence", duplicate_col_name="Doublon")

                # Supprimer les données dans les colonnes spécifiées si "Doublon" est "OUI"
                df = self.delete_data_based_on_column(df, check_column="Doublon", target_value="OUI", columns_to_clear=entete)

                # Réorganiser les colonnes selon l'ordre souhaité
                df = self.order_columns(df, column_order)

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
        
            upload_folder = current_app.config['UPLOAD_FOLDER']
            download_folder = current_app.config['DOWNLOAD_FOLDER']
            file_configs = self.get_congif(file, upload_folder, extract)
            path_name = self.generate_unique_filename(os.path.join(download_folder, 'Import_du'))
            file_mane = self.generate_unique_filename('Import','csv', extract=extract)
            result = f"{path_name}/{file_mane}"
            output_path = os.path.join(download_folder, result)
            column = self.get_fiedls_odoo(extract)
            entete = column['Entete']
            column_mapping = column['Mapping']
            column_order = column['Column']
            procees = self.process_import_files(file_configs, output_path, column_order, entete, column_mapping, path_name, file_mane)
            return procees
    
    def get_headers(self, file_path):
        """
        Retourne les entêtes (noms des colonnes) d'un fichier .xlsx ou .csv.
        
        :param file_path: Chemin du fichier (xlsx ou csv).
        :return: Liste des noms de colonnes ou un message d'erreur.
        """
        try:
            
            # Vérifier l'extension du fichier
            if file_path.endswith('.csv'):
                # Lire le fichier CSV
                df = pd.read_csv(file_path, nrows=0, sep=';')  # Charger uniquement les entêtes
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
                            "file": os.path.join(path, "res_partner.xlsx"),
                            "colonne1": "ref",
                            "colonne2": partner,
                            "colonne3": "id",
                            "resultat": partner
                        },
                        {
                            "file": os.path.join(path, "product_template.xlsx"),
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
        """
        try:
            # Récupération des colonnes à traiter pour le type de mouvement
            odoo_field_info = self.get_fiedls_odoo(data['extract'])
            columns_to_process = odoo_field_info['Column']

            # Lecture du fichier chargé
            df = pd.read_excel(data['uploaded_file'])  # Ajusté pour un fichier XLSX

            # Boucle pour renommer les colonnes spécifiées
            for column in columns_to_process:
                if column in data:  # Vérifie si une nouvelle colonne est spécifiée dans les données
                    self.rename_column(df, data[column], column)

            # Sauvegarder ou retourner le DataFrame nettoyé
            output_path = data['uploaded_file']
            df.to_excel(output_path, index=False)
            print(f"Fichier nettoyé sauvegardé sous : {output_path}")
            return df

        except Exception as e:
            print(f"Erreur lors du nettoyage des données : {e}")

    def rename_column(self, df, old_name, new_name):
        """
        Renomme une colonne dans un DataFrame en suivant les règles spécifiées.
        """
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
        else:
            print(f"Colonne '{old_name}' introuvable dans le fichier.")
        
        
        