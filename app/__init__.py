from flask import Flask
from .config.settings import Config
from .extensions import db, migrate, jwt, cors
from .routes import register_routes
import logging 
from flask import jsonify
from flasgger import Swagger

def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

     # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # include all endpoints
                "model_filter": lambda tag: True,  # include all models
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",  # where Swagger UI will be available
    }

    template = {
        "swagger": "2.0",
        "info": {
            "title": "Your Project API",
            "description": "Auto-generated API documentation using Flasgger",
            "version": "1.0.0",

            "securityDefinitions": {
    "Bearer": {
        "type": "apiKey",
        "name": "Authorization",
        "in": "header",
        "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
    }
}

        },
        "basePath": "/",  # base path for your API
        "schemes": ["http", "https"],
    }

    Swagger(app, config=swagger_config, template=template)

    # register routes/blueprints
    register_routes(app)

    # simple root for quick health-check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

        # global JWT expired handler (example)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"msg": "token expired"}), 401
    
    return app
