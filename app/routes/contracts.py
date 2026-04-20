# app/routes/contracts.py
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models.contract import Contract, Milestone
from app.models.document import Document
from app.models.notification import Notification
from app.forms.contract import ContractForm, MilestoneForm
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc
from decorators import handle_integrity_exceptions

contracts = Blueprint('contracts', __name__, url_prefix='/contracts')


def update_expired_contracts():
    """
    Actualiza el status de los contratos a 'vencido' si:
    - La fecha actual es mayor a Contract.end_date
    - El status actual es 'activo'

    Returns:
        int: Número de contratos actualizados
    """
    try:
        today = datetime.now().date()

        # Buscar contratos activos que han vencido
        expired_contracts = Contract.query.filter(
            and_(
                Contract.end_date < today,
                Contract.status == 'activo'
            )
        ).all()

        # Contar cuántos contratos se van a actualizar
        updated_count = len(expired_contracts)

        if updated_count > 0:
            # Actualizar el status de todos los contratos vencidos
            Contract.query.filter(
                and_(
                    Contract.end_date < today,
                    Contract.status == 'activo'
                )
            ).update({'status': 'vencido'})

            # Confirmar los cambios en la base de datos
            db.session.commit()

            # Log opcional - solo si current_app está disponible
            try:
                current_app.logger.info(f"Se actualizaron {updated_count} contratos a status 'vencido'")
            except:
                print(f"Se actualizaron {updated_count} contratos a status 'vencido'")

        return updated_count

    except Exception as e:
        # Revertir cambios en caso de error
        db.session.rollback()
        # Log de error - usar print como fallback si current_app no está disponible
        try:
            current_app.logger.error(f"Error al actualizar contratos vencidos: {str(e)}")
        except:
            print(f"Error al actualizar contratos vencidos: {str(e)}")
        raise e

@contracts.route('/')
@login_required
def index():
    # Actualizar contratos vencidos antes de mostrar la lista
    try:
        updated_contracts = update_expired_contracts()
        if updated_contracts > 0:
            flash(f'Se actualizaron {updated_contracts} contratos vencidos', 'info')
    except Exception as e:
        flash('Error al actualizar contratos vencidos', 'error')

    # ── Parámetros de filtro ──────────────────────────────────────────────────
    status          = request.args.get('status',          '').strip()
    counterparty    = request.args.get('counterparty',    '').strip()
    contract_number = request.args.get('contract_number', '').strip()
    title           = request.args.get('title',           '').strip()
    start_date_str  = request.args.get('start_date',      '').strip()

    # ── Parámetros de ordenamiento ────────────────────────────────────────────
    # El template envía ?sort=<campo>&dir=asc|desc
    valid_sort_columns = ['counterparty', 'contract_number', 'title',
                          'start_date', 'end_date', 'value', 'status']
    sort = request.args.get('sort', 'counterparty')
    if sort not in valid_sort_columns:
        sort = 'counterparty'
    direction = request.args.get('dir', 'asc')

    # ── Paginación ────────────────────────────────────────────────────────────
    page     = request.args.get('page', 1, type=int)
    per_page = 10

    # ── Consulta base: solo contratos del usuario actual ──────────────────────
    query = Contract.query.filter_by(responsible_id=current_user.id)

    # Filtro por estado
    if status:
        query = query.filter(Contract.status == status)

    # Filtro por cliente/contraparte (búsqueda parcial, insensible a mayúsculas)
    if counterparty:
        query = query.filter(Contract.counterparty.ilike(f'%{counterparty}%'))

    # Filtro por número de contrato (búsqueda parcial)
    if contract_number:
        query = query.filter(Contract.contract_number.ilike(f'%{contract_number}%'))

    # Filtro por título (búsqueda parcial)
    if title:
        query = query.filter(Contract.title.ilike(f'%{title}%'))

    # Filtro por fecha de inicio (coincidencia exacta de día)
    if start_date_str:
        try:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Contract.start_date == start_date_obj)
        except ValueError:
            flash('Formato de fecha de inicio inválido.', 'warning')

    # ── Ordenamiento ──────────────────────────────────────────────────────────
    column = getattr(Contract, sort)
    query = query.order_by(desc(column) if direction == 'desc' else asc(column))

    # ── Totales para tarjetas de estadísticas ─────────────────────────────────
    total_contracts  = query.count()
    total_milestones = Milestone.query.count()

    # ── Paginación ────────────────────────────────────────────────────────────
    try:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    except Exception:
        pagination = query.paginate(page=1, per_page=per_page, error_out=False)
        flash('Error en la paginación, mostrando primera página.', 'warning')

    contracts_list = pagination.items

    # ── Contratos próximos a vencer (60 días) ─────────────────────────────────
    try:
        sixty_days_from_now = datetime.now().date() + timedelta(days=60)
        expiring_soon = Contract.query.filter(
            and_(
                Contract.end_date <= sixty_days_from_now,
                Contract.end_date >= datetime.now().date(),
                Contract.status == 'activo',
                Contract.responsible_id == current_user.id
            )
        ).order_by(Contract.end_date).limit(5).all()
    except Exception:
        expiring_soon = []

    return render_template('contracts/index.html',
                           contracts=contracts_list,
                           pagination=pagination,
                           expiring_soon=expiring_soon,
                           total_contracts=total_contracts,
                           total_milestones=total_milestones)

# Función adicional para ejecutar como tarea programada (opcional)
def scheduled_update_expired_contracts():
    """
    Versión de la función para ejecutar como tarea programada.
    Puede ser llamada desde un cron job, Celery, APScheduler, etc.
    """
    with current_app.app_context():
        try:
            updated_count = update_expired_contracts()
            print(f"Tarea programada: {updated_count} contratos actualizados a 'vencido'")
            return updated_count
        except Exception as e:
            print(f"Error en tarea programada: {str(e)}")
            return 0

# Si necesitas una ruta/endpoint para ejecutar manualmente la actualización:
@contracts.route('/update-expired-contracts')
def update_expired_contracts_endpoint():
    """
    Endpoint para ejecutar manualmente la actualización de contratos vencidos
    """
    try:
        updated_count = update_expired_contracts()
        if updated_count > 0:
            message = f"Se actualizaron {updated_count} contratos a status 'vencido'"
            return {"status": "success", "message": message, "updated_count": updated_count}
        else:
            return {"status": "success", "message": "No hay contratos para actualizar", "updated_count": 0}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}, 500

@contracts.route('/new', methods=['GET', 'POST'])
@handle_integrity_exceptions
@login_required
def new_contract():
    form = ContractForm()
    if form.validate_on_submit():
        contract = Contract(
            title=form.title.data,
            description=form.description.data,
            contract_number=form.contract_number.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data if not form.indefinite_contract.data else None,
            value=form.value.data,
            facturacion=form.facturacion.data,
            facturado=form.facturado.data,
            counterparty=form.counterparty.data,
            status=form.status.data,
            responsible_id=current_user.id,

        )
        db.session.add(contract)
        db.session.commit()
        flash('Contrato creado exitosamente.')
        return redirect(url_for('contracts.view_contract', id=contract.id))

    return render_template('contracts/new.html', title='Nuevo Contrato', form=form)

@contracts.route('/<int:id>/view')
@login_required
def view_contract(id):
    contract = Contract.query.get_or_404(id)
    today = datetime.now().date()
    return render_template('contracts/view.html', contract=contract, today=today)

@contracts.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contract(id):
    contract = Contract.query.get_or_404(id)
    form = ContractForm(obj=contract)

    if form.validate_on_submit():
        contract.title = form.title.data
        contract.description = form.description.data
        contract.contract_number = form.contract_number.data
        contract.start_date = form.start_date.data
        contract.end_date = form.end_date.data if not form.indefinite_contract.data else None
        contract.value = form.value.data
        contract.facturacion = form.facturacion.data
        contract.facturado = form.facturado.data
        contract.counterparty = form.counterparty.data
        contract.status = form.status.data

        db.session.commit()
        flash('Contrato actualizado exitosamente.')
        return redirect(url_for('contracts.view_contract', id=contract.id))

    return render_template('contracts/edit.html', title='Editar Contrato', form=form, contract=contract)


@contracts.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_contract(id):
    """
    Elimina un contrato específico.
    Solo acepta método POST para mayor seguridad.
    """
    try:
        contract = Contract.query.get_or_404(id)

        # Guardar información del contrato para el mensaje de confirmación
        contract_title = contract.title
        contract_number = contract.contract_number

        # Opcional: Verificar permisos (descomenta si necesitas esta lógica)
        if contract.responsible_id != current_user.id and not current_user.role == 'admin':
            flash('No tienes permisos para eliminar este contrato.', 'error')
            return redirect(url_for('contracts.view_contract', id=id))

        # Eliminar documentos asociados primero (si existen)
        Document.query.filter_by(contract_id=id).delete()

        # Eliminar hitos asociados (si existen)
        Milestone.query.filter_by(contract_id=id).delete()

        # Eliminar el contrato de la base de datos
        db.session.delete(contract)
        db.session.commit()

        flash(f'✓ Contrato "{contract_title}" (#{contract_number}) eliminado exitosamente.', 'success')
        return redirect(url_for('contracts.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'✗ Error al eliminar el contrato: {str(e)}', 'danger')
        return redirect(url_for('contracts.index'))

# En tu ruta que renderiza la lista de contratos
@contracts.route('/contracts')
def list_contracts():
    # contracts = Contract.query.all()
    contracts = Contract.query.filter_by(user_id=current_user.id)

    # Agregar contador de documentos a cada contrato
    contracts_with_doc_count = []
    for contract in contracts:
        contract.doc_count = Document.query.filter_by(contract_id=contract.id).count()
        contracts_with_doc_count.append(contract)

    return render_template('contracts/index.html', contracts=contracts_with_doc_count)


@contracts.route('/<int:id>/confirm-delete')
@login_required
def confirm_delete_contract(id):
    """
    Muestra una página de confirmación antes de eliminar el contrato.
    Esta es una alternativa más segura que permite al usuario confirmar la eliminación.
    """
    contract = Contract.query.get_or_404(id)

    # Verificar permisos (opcional)
    if hasattr(contract, 'responsible_id') and contract.responsible_id != current_user.id:
        if not current_user.is_admin:
            flash('No tienes permisos para eliminar este contrato.', 'error')
            return redirect(url_for('contracts.view_contract', id=id))

    return render_template('contracts/confirm_delete.html', contract=contract)

# Función auxiliar para limpiar filtros
def clean_filters(**kwargs):
    """Remueve filtros vacíos de los argumentos"""
    return {k: v for k, v in kwargs.items() if v}

@contracts.route('/<int:id>/milestone/new', methods=['GET', 'POST'])
@login_required
def new_milestone(id):
    contract = Contract.query.get_or_404(id)
    form = MilestoneForm()

    if form.validate_on_submit():
        milestone = Milestone(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            contract_id=contract.id
        )
        db.session.add(milestone)
        db.session.commit()

        # Crear notificación
        notification = Notification(
            title=f"Nuevo hito para contrato {contract.contract_number}",
            message=f"Se ha creado un nuevo hito: {milestone.title} con fecha {milestone.due_date}",
            user_id=contract.responsible_id,
            contract_id=contract.id
        )
        db.session.add(notification)
        db.session.commit()

        flash('Hito creado exitosamente.')
        return redirect(url_for('contracts.view_contract', id=contract.id))

    return render_template('contracts/milestone_form.html',
                           title='Nuevo Hito',
                           form=form,
                           contract=contract)

@contracts.route('/<int:id>/milestone/view')
@login_required
def view_milestone(id):
    milestone = Milestone.query.get_or_404(id)
    total_milestones = Milestone.query.count()
    return render_template('milestones/index.html', total_milestones=total_milestones, contract=contract)

@contracts.route('/<int:contract_id>/milestone/<int:milestone_id>/complete')
@login_required
def complete_milestone(contract_id, milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)

    if milestone.contract_id != contract_id:
        abort(404)

    milestone.completed = True
    milestone.completed_date = datetime.utcnow().date()
    db.session.commit()

    flash('Hito marcado como completado.')
    return redirect(url_for('contracts.view_contract', id=contract_id))

@contracts.route('/<int:contract_id>/milestone/<int:milestone_id>/delete', methods=['POST'])
@login_required
def delete_milestone(contract_id, milestone_id):
    """
    Gestiona la eliminación de un hito existente.
    Se utiliza el método POST por seguridad para evitar la eliminación accidental.
    """
    # Busca el hito por su ID; si no lo encuentra, devuelve un error 404.
    milestone = Milestone.query.get_or_404(milestone_id)

    # Medida de seguridad importante: verifica que el hito pertenezca al contrato
    # especificado en la URL para evitar la manipulación de IDs.
    if milestone.contract_id != contract_id:
        abort(403)  # Devuelve un error 'Forbidden' (Prohibido).

    # Elimina el objeto 'milestone' de la sesión de la base de datos.
    db.session.delete(milestone)
    # Confirma los cambios en la base de datos.
    db.session.commit()

    flash('El hito ha sido eliminado exitosamente.', 'success')
    # Redirige al usuario de vuelta a la página de detalles del contrato.
    return redirect(url_for('contracts.view_contract', id=contract_id))

@contracts.route('/<int:contract_id>/milestone/<int:milestone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_milestone(contract_id, milestone_id):
    """
    Gestiona la edición de un hito existente.
    """
    # Busca el hito por su ID; si no lo encuentra, devuelve un error 404.
    milestone = Milestone.query.get_or_404(milestone_id)

    # Busca el contrato asociado para validación y para pasarlo a la plantilla.
    contract = Contract.query.get_or_404(contract_id)

    # Medida de seguridad importante: verifica que el hito pertenezca al contrato
    # especificado en la URL. Esto evita que se puedan editar hitos de otros contratos
    # manipulando los IDs.
    if milestone.contract_id != contract.id:
        abort(403)  # Devuelve un error 'Forbidden' (Prohibido).

    # Al cargar la página (petición GET), se puebla el formulario con los datos
    # del objeto 'milestone' que se recuperó de la base de datos.
    # WTForms asocia los campos del formulario con los atributos del objeto.
    form = MilestoneForm(obj=milestone)

    # Si el formulario se envía (petición POST) y pasa las validaciones.
    if form.validate_on_submit():
        # Actualiza los datos del objeto 'milestone' con la información del formulario.
        milestone.title = form.title.data
        milestone.description = form.description.data
        milestone.due_date = form.due_date.data

        # Guarda los cambios en la base de datos.
        db.session.commit()

        flash('El hito ha sido actualizado exitosamente.', 'success')
        # Redirige al usuario de vuelta a la página de detalles del contrato.
        return redirect(url_for('contracts.view_contract', id=contract.id))

    # Si es una petición GET (la primera vez que se carga la página) o si el
    # formulario no es válido, se renderiza la plantilla del formulario.
    # El formulario ya contendrá los datos del hito para ser editados.
    return render_template('contracts/milestone_form.html',
                           title='Editar Hito',
                           form=form,
                           contract=contract)