from flask import (
    Flask, Blueprint, request, render_template, redirect, 
    url_for, jsonify, abort
)
from controllers.FileManagerController import FileManagerController
from controllers.FileConfigController import FileConfigController

main_blueprint = Blueprint('main', __name__)
file_manager = FileManagerController()
file_config = FileConfigController()

# Fonction pour gérer les erreurs
def template_error(message, error):
    return f"{message} \n {error}"

@main_blueprint.route('/')
@main_blueprint.route('/home')
def home():
    return render_template('index.html', page="Accueil")

@main_blueprint.route('/processing', methods=['POST', 'GET'])
def form():
    if request.method == 'GET':
        return render_template('form.html', page="Nouvel import")
    
    # Traitement des requêtes POST
    request_dict = {key: value for key, value in request.form.items()}
    file_path = request_dict.get('uploaded_file')

    if not file_path:
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur="Aucun fichier trouvé."
        )
    
    file_path_result = file_config.cleaning_data(request_dict)
    if file_path_result['Type'] == 'Error':
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur=template_error(file_path_result['Message'], file_path_result['Response'])
        )
    
    resultat = file_config.transition(file_path_result['Response'], request_dict.get('extract'))
    if resultat['Type'] == 'Error':
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur=template_error(resultat['Message'], resultat['Response'])
        )
    
    return browse_directory(message=f"Fichier d’importation : \n {resultat['Response']}")

@main_blueprint.route('/processing/check', methods=['POST'])
def check_form():
    file = request.files.get('file')
    if not file:
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur="Aucun fichier trouvé."
        )
    uploaded_file = file_manager.upload_file(file)
    extract = request.form.get('extract')
    sep = request.form.get('separator')
    odoo_resultat = file_config.get_fiedls_odoo(extract)

    if uploaded_file['Type'] == 'Error':
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur=template_error(uploaded_file['Message'], uploaded_file['Response'])
        )
    else:
        resultat = file_config.get_headers(uploaded_file['Response'], sep) if sep else file_config.get_headers(uploaded_file['Response'])

    if resultat['Type'] == 'Error':
        return render_template(
            'form.html', 
            page="Nouvel import", 
            erreur=template_error(resultat['Message'], resultat['Response'])
        )
    else:
        return render_template(
            'form.html', 
            page="Nouvel import", 
            check=resultat['Response'], 
            odoo_check=odoo_resultat, 
            file=uploaded_file['Response'], 
            extract=extract, 
            sep=sep
        )

@main_blueprint.route('/browse')
@main_blueprint.route('/browse/<path:path>')
def browse_directory(path="", message=None):
    result = file_manager.list_files(path)
    directories = result.get("directories", [])
    files = result.get("files", [])
    current_path = result.get("current_path", "")

    return render_template(
        'browse.html',
        page="Fichiers d'import",
        directories=directories,
        files=files,
        current_path=current_path,
        enumerate=enumerate,
        message=message
    )

@main_blueprint.route('/download/<path:filename>')
def download_file(filename):
    if file_manager.file_exists(filename)['Type'] == 'Error':
        abort(404, description="Fichier introuvable.")
    return file_manager.download_file(filename)

@main_blueprint.route('/download_import/<path:filename>')
def download_file_import(filename):
    if file_manager.file_exists(filename)['Type'] == 'Error':
        abort(404, description="Fichier introuvable.")
    return file_manager.subdivide_csv_sheet(filename)

@main_blueprint.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    print(filename)
    if file_manager.file_exists(filename)['Type'] == 'Error':
        abort(404, description="Fichier introuvable.")
    return file_manager.delete_file(filename)

@main_blueprint.route('/get_headers', methods=['POST'])
def get_headers_route():
    data = request.get_json()
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({"error": "Le chemin du fichier est requis."}), 400

    headers = file_config.get_headers(file_path)
    if isinstance(headers, str):
        return jsonify({"error": headers}), 400

    return jsonify({"columns": headers})

@main_blueprint.route('/get_fields_odoo', methods=['POST'])
def get_fields_odoo_route():
    move = request.json.get('move')
    if not move:
        return jsonify({"error": "Le type (move) est requis"}), 400

    return jsonify(file_config.get_fiedls_odoo(move))

@main_blueprint.route('/admin@admin', methods=['POST', 'GET'])
def admin_action():
    if request.method == 'GET':
        return render_template('admin.html')

# Gestion des erreurs globales
@main_blueprint.app_errorhandler(400)
def bad_request(error):
    return render_template("400.html", message=error.description), 400

@main_blueprint.app_errorhandler(404)
def not_found(error):
    return render_template("404.html", message=error.description), 404

@main_blueprint.app_errorhandler(500)
def internal_server_error(error):
    return render_template("500.html", message="Erreur interne du serveur."), 500
