from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    Request,
    request,
    url_for
)

from src.core import adressing, people, professions
from web.forms.member_form import MemberForm
from web.forms.person_document_form import PersonDocumentForm as DocumentForm
from src.web.handlers.autenticacion import login_required


bp = Blueprint("team", __name__, url_prefix ="/team") 

@bp.get("/")
@login_required
def index() -> str:
    """Listado de miembros del equipo usando filtros, ordenación y paginación"""
    page = request.args.get('page', 1, type=int)
    per_page = 25

    # Obtener los filtros de búsqueda y ordenación
    filters = {
        'name': request.args.get('name'),
        'last_name': request.args.get('last_name'),
        'dni': request.args.get('dni'),
        'email': request.args.get('email'),
        'profession_id': request.args.get('profession_id')
    }
    sort_by = request.args.get('sort_by', 'name')
    sort_direction = request.args.get('sort_direction', 'asc')

    members, total_pages = people.list_members(filters, page, per_page, sort_by, sort_direction)
    return render_template(
        'team/index.html', 
        members=members, 
        page=page, 
        total_pages=total_pages, 
        professions=professions.list_professions(),
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction
    )

@bp.get("/<int:id>")
def show(id: int)->str:
    """Recibe el id de un miembro del equipo y muestra su información"""
    member = people.get_member_by_field('id', id)
    documents = people.list_documents(id)
    return render_template('team/show.html', member=member, documents=documents)

def _get_data_from_db():
    """Obtiene la lista de profesiones, trabajos, provincias y localidades de la BD"""
    profession_list = professions.list_professions()
    jobs = professions.list_jobs()
    provinces = adressing.list_provinces()
    localities = adressing.list_localities()
    return profession_list, jobs, provinces, localities

def _get_validator(profession_list:list, jobs:list, localities:list, member_id=None)->MemberForm:
    """Recibe la lista de profesiones, trabajos, localidades y el id del miembro y retorna el validador del formulario"""
    form = MemberForm(member_id=member_id)
    form.profession_id.choices = [(profession.id, profession.name) for profession in profession_list]
    form.job_id.choices = [(job.id, job.name) for job in jobs]
    form.locality_id.choices = [(locality.id, locality.name) for locality in localities]
    return form

def _validate_request(req:Request, profession_list:list, jobs:list, provinces:list, localities: list, member_id=None)->tuple:
    """Recibe la request, la lista de profesiones, trabajos, provincias y localidades y valida que el formulario sea correcto"""
    form = _get_validator(profession_list, jobs, localities, member_id)
    form.process(req.form)
    if not form.validate():
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        flash(f"Error en el formulario -> {'; '.join(error_messages)}", "danger")
        return form, False
    
    return form, True

@bp.route("/new" , methods=['GET', 'POST'])
def create()->str:
    """Muestra el formulario para crear un nuevo miembro del equipo y lo guarda en la BD"""
    member = {}
    profession_list, jobs, provinces, localities = _get_data_from_db()
    
    # Si se envia el formulario
    if request.method == "POST":
        form, valid = _validate_request(request, profession_list, jobs, provinces, localities)
        if valid:
            member = people.member_new(**form.data)
            flash(f"El miembro {member.name} {member.last_name} ha sido creado exitosamente", "success")
            return redirect(url_for('team.show', id=member.id))
        else:
            member = form.data

    return render_template('team/create.html', member=member, professions=profession_list, jobs=jobs, provinces=provinces)

@bp.route("/<int:id>/edit", methods=['GET', 'POST'])
def update(id: int)->str:
    """Recibe el id de un miembro del equipo y muestra el formulario para editarlo, al mismo tiempo que lo actualiza en la BD"""
    member = people.get_member_by_field('id', id)
    profession_list, jobs, provinces, localities = _get_data_from_db()
    
    # Si se envia el formulario
    if request.method == "POST":
        form, valid = _validate_request(request, profession_list, jobs, provinces, localities, member_id=member.id)
        if valid:
            member = people.member_update(id, **form.data)
            flash(f"El miembro {member.name} {member.last_name} ha sido actualizado exitosamente", "success")
            print(member)
            return redirect(url_for('team.show', id=id))
        else:
            member = people.Member(**form.data)
    
    return render_template('team/update.html', member=member, professions=profession_list, jobs=jobs, provinces=provinces)

@bp.post("/<int:id>/delete")
def destroy(id: int)->str:
    """Recibe el id de un miembro del equipo y lo elimina fisicamente de la BD"""
    documents = people.list_documents(id)
    for document in documents:
        people.delete_document(document['id'])
    member = people.member_delete(id)
    flash(f"El miembro {member.name} {member.last_name} ha sido eliminado", "success")
    return redirect(url_for('team.index'))

@bp.route("/<int:id>/add_document", methods=['GET', 'POST'])
def add_document(id: int)->str:
    """Recibe el id de un miembro del equipo y agrega un documento a su lista de documentos"""
    form = DocumentForm()
    if form.validate_on_submit():
        document = form.document.data
        people.member_add_document(id, document)
        flash("Documento agregado exitosamente", "success")
        return redirect(url_for('team.show', id=id))
    else:
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        flash(f"Error en el formulario: {error_messages}", "danger")

    return render_template('team/add_document.html', member_id=id, form=form)

@bp.post("/<int:id>/delete_document/<int:document_id>")
def destroy_document(id: int, document_id: int)->str:
    """Recibe el id de un miembro del equipo y el id de un documento y lo elimina de la BD"""
    document = people.delete_document(document_id)
    flash(f"Documento {document.document_name} eliminado exitosamente", "success")
    return redirect(url_for('team.show', id=id))