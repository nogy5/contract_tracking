# app/routes/notifications.py
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc

notifications = Blueprint('notifications', __name__)


@notifications.route('/notifications')
@login_required
def index():
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    # Obtener parámetros de filtro con valores por defecto
    search = request.args.get('search', '').strip()
    title = request.args.get('title', '').strip()
    message = request.args.get('message', '').strip()
    created_at = request.args.get('created_at', '').strip()
    read = request.args.get('read', '').strip()

    # Parámetros de ordenamiento
    sort = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Contratos por página

    # Construir query base
    query = Notification.query

    # Aplicar filtros solo si tienen valores
    if search:
        query = query.filter(
            or_(
                Notification.title.ilike(f'%{search}%')
            )
        )

    if message:
        query = query.filter(Notification.message == message)

    if title:
        query = query.filter(Notification.title == title)

    if read:
        query = query.filter(Notification.read == read)

    if created_at:
        try:
            date_from_obj = datetime.strptime(created_at, '%Y-%m-%d').date()
            query = query.filter(Notification.created_at >= date_from_obj)
        except ValueError:
            flash('Formato de fecha "creado en" inválido', 'error')

    # Aplicar ordenamiento
    valid_sort_columns = ['title', 'message', 'created_at', 'read']
    if sort in valid_sort_columns:
        column = getattr(Notification, sort)
        if order == 'desc':
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        # Ordenamiento por defecto si el parámetro no es válido
        query = query.order_by(desc(Notification.created_at))

    # Ordenar tabla principal por nombre del título después de ordenar por Cliente
    if 'sort' not in request.args and 'order' not in request.args:
        sort = 'title'
        order = 'asc'

    # Ejecutar paginación
    try:
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    except Exception as e:
        # En caso de error en la paginación, mostrar primera página
        pagination = query.paginate(
            page=1,
            per_page=per_page,
            error_out=False
        )
        flash('Error en la paginación, mostrando primera página', 'warning')

    return render_template('notifications/index.html',
                           notifications=user_notifications,
                           pagination=pagination,
                           title=title
                           )


@notifications.route('/notifications/mark_read/<int:id>')
@login_required
def mark_read(id):
    notification = Notification.query.get_or_404(id)

    # Verificar que la notificación pertenece al usuario actual
    if notification.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 403

    notification.read = True
    db.session.commit()

    return jsonify({'status': 'success'})


@notifications.route('/notifications/mark_all_read')
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
    db.session.commit()

    return redirect(url_for('notifications.index'))


@notifications.route('/notifications/unread_count')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()

    return jsonify({'Hitos': count})
    # return redirect(url_for('notifications.index'))