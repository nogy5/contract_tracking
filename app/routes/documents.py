# app/routes/documents.py
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.document import Document
from app.models.contract import Contract
from app.forms.document import DocumentForm

documents = Blueprint('documents', __name__)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents.route('/contracts/<int:contract_id>/documents')
@login_required
def contract_documents(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    documents = Document.query.filter_by(contract_id=contract_id).all()

    return render_template('documents/index.html',
                           title='Documentos del Contrato',
                           contract=contract,
                           documents=documents)


@documents.route('/contracts/<int:contract_id>/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_document(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    form = DocumentForm()

    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No se seleccionó ningún archivo.')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            # Generar un nombre de archivo único usando UUID
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Crear registro en la base de datos
            document = Document(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                description=form.description.data,
                contract_id=contract.id,
                uploaded_by=current_user.id
            )

            db.session.add(document)
            db.session.commit()

            flash('Documento subido exitosamente.')
            return redirect(url_for('documents.contract_documents', contract_id=contract.id))
        else:
            flash('Tipo de archivo no permitido.')

    return render_template('documents/upload.html',
                           title='Subir Documento',
                           form=form,
                           contract=contract)


@documents.route('/documents/<int:id>/download')
@login_required
def download_document(id):
    document = Document.query.get_or_404(id)

    # Obtener solo el nombre del archivo del path completo
    filename = os.path.basename(document.file_path)
    directory = os.path.dirname(document.file_path)

    return send_from_directory(
        directory,
        filename,
        as_attachment=True,
        download_name=document.original_filename
    )


@documents.route('/documents/<int:id>/delete')
@login_required
def delete_document(id):
    document = Document.query.get_or_404(id)
    contract_id = document.contract_id

    # Eliminar el archivo físico
    try:
        os.remove(document.file_path)
    except Exception as e:
        flash(f'Error al eliminar el archivo: {str(e)}')

    # Eliminar el registro de la base de datos
    db.session.delete(document)
    db.session.commit()

    flash('Documento eliminado exitosamente.')
    return redirect(url_for('documents.contract_documents', contract_id=contract_id))