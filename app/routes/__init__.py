from flask import Blueprint

def register_routes(app):

    from app.routes.auth_routes import auth_bp
    # from app.routes.user_routes import user_bp
    from app.routes.task_routes import task_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(task_bp, url_prefix='/user/tasks')







    @app.route("/")
    def home():
        return "home"