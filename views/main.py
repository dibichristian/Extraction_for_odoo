from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from controllers.FileManagerController import FileManagerController
from controllers.FileConfigController import FileConfigController

main_blueprint = Blueprint('main', __name__)
file_manager = FileManagerController()
file_config = FileConfigController()

@main_blueprint.route('/')
def home():
    return render_template('index.html', page="Accueil")

@main_blueprint.route('/traiment', methods=['POST','GET'])
def form():
    if request.method == 'GET':
        return render_template('form.html', page="Nouvel import")
    
    elif request.method == 'POST':
        request_dict = {key: value for key, value in request.form.items()}

        file_path = request_dict['uploaded_file']
        
        if not file_path:
            return render_template('form.html', page="Nouvel import", erreur='Aucun fichier trouvé.')
        
        

        file_path = file_config.cleaning_data(request_dict)
        resultat = file_config.transition(file_path, request_dict['extract'])
        
        if resultat['type'] == 'Erreur':
            return render_template('form.html', page="Nouvel import", erreur=resultat['Resultat'])
        else:
            return browse_directory(message=resultat['Resultat'])

        
@main_blueprint.route('/traiment/check', methods=['POST'])
def check_form():
    file = request.files.get('file')
    if not file:
        return render_template('form.html', page="Nouvel import", erreur='Aucun fichier trouve.')
    file = file_manager.upload_file(file)
    extract = request.form.get('extract')
    resultat = file_config.get_headers(file)
    odoo_resultat = file_config.get_fiedls_odoo(extract)
    return render_template('form.html', page="Nouvel import", check=resultat, odoo_check=odoo_resultat, file=file, extract=extract)

@main_blueprint.route('/browse')
@main_blueprint.route('/browse/<path:path>')
def browse_directory(path="", message=None):
    """
    Render the home page with the list of files and directories.
    """
    result = file_manager.list_files(path)
    directories = result["directories"]
    files = result["files"]
    current_path = result["current_path"]
    page = 'Fichies d\'import'
    return render_template(
        'browse.html',
        page=page,
        directories=directories,
        files=files,
        current_path=current_path,
        enumerate=enumerate,
        message=message
    )


@main_blueprint.route('/download/<path:filename>')
def download_file(filename):
    
    # Forward the download request to the controller.
    
    return file_manager.download_file(filename)

@main_blueprint.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    
    # Forward the delete request to the controller.
    
    return file_manager.delete_file(filename)

@main_blueprint.route('/get_headers', methods=['POST'])
def get_headers_route():
    data = request.get_json()
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({"error": "Le chemin du fichier est requis."}), 400

    headers = file_config.get_headers(file_path)
    if isinstance(headers, str):  # Si une erreur est retournée
        return jsonify({"error": headers}), 400

    return jsonify({"columns": headers})


@main_blueprint.route('/get_fields_odoo', methods=['POST'])
def get_fields_odoo_route():
    """
    Retourne les colonnes et mappages pour une opération spécifique (Client ou Fournisseur).
    """
    move = request.json.get('move')
    if not move:
        return jsonify({"error": "Le type (move) est requis"}), 400

    data = file_config.get_fiedls_odoo(move)
    return jsonify(data)
