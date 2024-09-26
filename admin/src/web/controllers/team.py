from flask import render_template, Blueprint, request, redirect, url_for

from src.core import people, adressing, professions


bp = Blueprint("team", __name__, url_prefix ="/team") 

@bp.get("/")
def index():
    """Listado de miembros del equipo"""
    members = people.list_members()
    return render_template('team/index.html', members=members)

@bp.get("/<int:id>")
def show(id: int):
    """Detalle de un miembro del equipo"""
    member = people.get_member_by_id(id)
    return render_template('team/show.html', member=member)

def _check_data(form_data: dict):
    """Valida los datos del formulario"""
    form_data['active'] = form_data.get('active', 'false').lower() == 'true'
    if form_data.get('end_date') == '':
        form_data['end_date'] = None
    return form_data

@bp.route("/nuevo" , methods=['GET', 'POST'])
def create():
    """Formulario para crear un nuevo miembro del equipo"""
    profession_list = professions.list_professions()
    jobs = professions.list_jobs()
    localities = adressing.list_localities()
    if request.method == "POST":
        # Aquí debes procesar los datos del formulario
        form_data = _check_data(request.form.to_dict())
        member = people.member_new(**form_data)
        return redirect(url_for('team.show', id=member.id))
    return render_template('team/create.html', professions=profession_list, jobs=jobs, localities=localities)

@bp.post("/<int:id>/editar")
def update(id: int):
    """Formulario para editar un miembro del equipo"""
    member = people.get_member_by_id(id)
    profession_list = professions.list_professions()
    jobs = professions.list_jobs()
    localities = adressing.list_localities()
    return render_template('team/update.html', member=member, professions=profession_list, jobs=jobs, localities=localities)

@bp.post("/<int:id>")
def save(id: int):
    """Actualizar un miembro del equipo"""
    member = people.member_update(id, **request.form)
    return redirect(url_for('team.show', id=member.id))

@bp.post("/<int:id>/eliminar")
def destroy(id: int):
    """Eliminar un miembro del equipo"""
    member = people.member_delete(id)
    return redirect(url_for('team.index'))
