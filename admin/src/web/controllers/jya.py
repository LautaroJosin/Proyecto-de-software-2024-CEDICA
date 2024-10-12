from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, Request, request, url_for

from src.core.people.member_rider import Member
from src.core import adressing, disabilities, people, professions
from src.web.forms.person_document_form import PersonDocumentForm as DocumentForm
from src.web.forms.person_link_form import PersonLinkForm as LinkForm
from src.web.forms.rider_form import RiderForm
from src.web.handlers.autenticacion import login_required


bp = Blueprint("jya", __name__, url_prefix="/jya")


@bp.get("/")
@login_required
def index() -> str:
    """Listado de j/a del equipo usando filtros, ordenación y paginación"""
    page = request.args.get("page", 1, type=int)
    per_page = 25

    # Obtener los filtros de búsqueda y ordenación
    filters = {
        "name": request.args.get("name"),
        "last_name": request.args.get("last_name"),
        "dni": request.args.get("dni"),
        "members": request.args.getlist("members", type=int),
    }
    
    sort_by = request.args.get("sort_by", "name")
    sort_direction = request.args.get("sort_direction", "asc")

    riders, total_pages = people.list_riders(
        filters, page, per_page, sort_by, sort_direction
    )
    return render_template(
        "jya/index.html",
        riders=riders,
        members=people.list_professionals(),
        filters=filters,
        page=page,
        total_pages=total_pages,
        sort_by=sort_by,
        sort_direction=sort_direction,
        current_year=datetime.now().year,
    )


@bp.get("/<int:id>")
@login_required
def show(id: int) -> str:
    """Recibe el id de un j/a y muestra su información y documentos asociados"""
    filters = {
        "document_name": request.args.get("document_name"),
        "document_type": request.args.get("document_type"),
        "person_id": id,
    }
    sort_by = request.args.get("sort_by", "document_name")
    sort_direction = request.args.get("sort_direction", "asc")
    rider = people.get_rider_by_field("id", id)
    documents = people.list_filtered_documents(id, filters, sort_by, sort_direction) 
    return render_template("jya/show.html", rider=rider, documents=documents, filters=filters, sort_by=sort_by, sort_direction=sort_direction, current_year=datetime.now().year,)


def _get_validator(localities: list, rider_id=None) -> RiderForm:
    """Recibe la lista de profesiones, trabajos, localidades y el id del j/a y retorna el validador del formulario"""
    form = RiderForm(rider_id=rider_id)
    form.locality_id.choices = [(locality.id, locality.name) for locality in localities]
    return form


def _validate_request(
    req: Request,
    localities: list,
    rider_id=None,
) -> tuple:
    """Recibe la request, la lista de profesiones, trabajos, provincias y localidades y valida que el formulario sea correcto"""
    form = _get_validator(localities, rider_id)
    form.process(req.form)
    if not form.validate():
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        flash(f"Error en el formulario -> {'; '.join(error_messages)}", "danger")
        return form, False

    return form, True


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create() -> str:
    """Muestra el formulario para crear un nuevo j/a y lo guarda en la BD"""
    rider = {}
    disability_types_list = disabilities.list_disability_types()
    disabilities_list = disabilities.list_disability_diagnosis()
    localities_list = adressing.list_localities()
    provinces_list = adressing.list_provinces()
    member_list = Member.query.all()

    # Si se envia el formulario
    if request.method == "POST":
        form, valid = _validate_request(request)
        if valid:
            rider = people.rider_new(**form.data)
            flash(
                f"{rider.name} {rider.last_name} ha sido creado exitosamente",
                "success",
            )
            return redirect(url_for("jya.show", id=rider.id))
        else:
            rider = form.data

    return render_template(
        "jya/create.html",
        rider=rider,
        disability_types=disability_types_list,
        disabilities=disabilities_list,
        localities=localities_list,
        provinces=provinces_list,
        members=member_list,
    )


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def update(id: int) -> str:
    """Recibe el id de un j/a y muestra el formulario para editarlo, al mismo tiempo que lo actualiza en la BD"""
    rider = people.get_rider_by_field("id", id)

    # Si se envia el formulario
    if request.method == "POST":
        form, valid = _validate_request(
            request, rider_id=rider.id
        )
        if valid:
            rider = people.rider_update(id, **form.data)
            flash(
                f"{rider.name} {rider.last_name} ha sido actualizado exitosamente",
                "success",
            )
            return redirect(url_for("jya.show", id=id))
        else:
            rider = people.Rider(**form.data)
            rider.id = id

    return render_template(
        "jya/update.html",
        rider=rider,
    )


@bp.post("/<int:id>/delete")
@login_required
def destroy(id: int) -> str:
    """Recibe el id de un j/a y lo elimina fisicamente de la BD"""
    rider = people.get_rider_by_field("id", id)

    documents = people.list_documents(rider.id)
    for document in documents:
        people.delete_document(document["id"])

    if rider.tutor_1:
        people.tutor_delete(rider.tutor_1.id)
    if rider.tutor_2:
        people.tutor_delete(rider.tutor_2.id)
    if rider.school:
        for school in rider.school:
            professions.school_delete(school.id)
    if rider.job_proposal:
        for job_proposal in rider.job_proposal:
            professions.job_proposal_delete(job_proposal.id)

    rider = people.rider_delete(id)
    flash(f"{rider.name} {rider.last_name} ha sido eliminado", "success")

    return redirect(url_for("jya.index"))


@bp.route("/<int:id>/add_document", methods=["GET", "POST"])
@login_required
def add_document(id: int) -> str:
    """Recibe el id de un j/a y agrega un documento a su lista de documentos"""
    form = DocumentForm()
    if form.validate_on_submit():
        document = form.document.data
        type = form.document_type.data
        people.rider_add_document(id, document, type)
        flash("Documento agregado exitosamente", "success")
        return redirect(url_for("jya.show", id=id))
    elif form.errors:
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        flash(f"Error en el formulario: {error_messages}", "danger")

    return render_template("jya/add_document.html", rider_id=id, form=form)


@bp.route("/<int:id>/add_link", methods=["GET", "POST"])
@login_required
def add_link(id: int) -> str:
    """Recibe el id de un j/a y agrega un enlace a su lista de documentos"""
    form = LinkForm()
    if form.validate_on_submit():
        name = form.document_name.data
        path = form.document_path.data
        type = form.document_type.data
        people.document_new(id, path, name, type, link=True)
        flash("Enlace cargado exitosamente", "success")
        return redirect(url_for("jya.show", id=id))
    elif form.errors:
        error_messages = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
        flash(f"Error en el formulario: {error_messages}", "danger")

    return render_template("jya/add_link.html", rider_id=id, form=form)


@bp.post("/<int:id>/delete_document/<int:document_id>")
@login_required
def destroy_document(id: int, document_id: int) -> str:
    """Recibe el id de un j/a y el id de un documento y lo elimina de la BD"""
    document = people.delete_document(document_id)
    flash(f"Documento {document.document_name} eliminado exitosamente", "success")
    return redirect(url_for("jya.show", id=id))
