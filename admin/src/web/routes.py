from flask import render_template

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.core.user_role_permission.operations.user_operations import (
    find_user,
    get_roles_from_user,
    get_user_by_email,
    user_new,
)


def register(app):
    @app.route("/", endpoint="home")
    def home(): 
        return render_template("home.html")
    
    @app.route("/redauth")
    def red_auth():
        redirect_uri = url_for('auth', _external=True)
        print(redirect_uri)  # https://127.0.0.1:5000/login/callback
        return app.oauth.google.authorize_redirect(redirect_uri)
    
    @app.route("/redlogin")
    def red_login():
        redirect_uri = url_for('login_google', _external=True)
        print(redirect_uri)  
        return app.oauth.google.authorize_redirect(redirect_uri)

    
    
    @app.route('/login/callback')
    def auth():
        "Se registra parcialmente al usuario mediante google, y se le avisa que queda a la espera de validacion"
        token = app.oauth.google.authorize_access_token()
        userinfo = token['userinfo'] 
        
        email = userinfo['email']
        first_name = userinfo['given_name']
        last_name = userinfo['family_name']
        google_id = userinfo['sub']  # id de Google
        
        user = get_user_by_email(email)
        
        if user is None:
            user = user_new(
                alias=first_name,
                #lastname=last_name, no existe en el modelo
                google_id=google_id,
                email=email,
                password="default_password",
                confirmed=False,
            )        
        else:
            flash("Ya existe un usuario con ese email","error")
            return redirect(url_for("auth.login"))

        flash("Tu registro esta a la espera de la confirmación de un Administrador","info")
        return redirect(url_for("auth.login"))

        
    @app.route('/logingoogle/callback')
    def login_google():
        # Obtener el token de Google
        token = app.oauth.google.authorize_access_token()
        userinfo = token['userinfo']  # Información del usuario obtenida de Google
        email = userinfo['email']
        google_id = userinfo['sub']  # El ID único de Google para el usuario

        user = get_user_by_email(email)
        if user:
            if user.google_id:
                # si esta registrado con google
                #verifico que el admin lo haya verificado
                if user.confirmed == True:
                    session["user"] = user.email
                    flash("La sesión se inició correctamente!", "success")
                    return render_template("home.html")
                else:
                    flash('Su cuenta esta a la espera de verificacion por un Administrador','info')
                    return redirect(url_for('auth.login')) 
            else:
                # tiene cuenta tradicional
                flash("Este correo ya está registrado, pero no está vinculado a Google. Inicie sesión con su contraseña.", "warning")
                return redirect(url_for('auth.login')) 
        else:
            flash('No existe un usuario asociado a la cuenta de Google correspondiente','error')
            return render_template('auth/login.html')
