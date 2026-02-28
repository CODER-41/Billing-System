from flask import Flask, jsonify
from flask_cors import CORS
from .extensions import db, jwt, bcrypt, migrate, limiter
from .config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

    from .routes.auth import bp as auth_bp
    from .routes.users import bp as users_bp
    from .routes.employees import bp as employees_bp
    from .routes.payroll import bp as payroll_bp
    from .routes.transfers import bp as transfers_bp
    from .routes.reports import bp as reports_bp
    from .routes.webhooks import bp as webhooks_bp

    app.register_blueprint(auth_bp,      url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp,     url_prefix='/api/v1/users')
    app.register_blueprint(employees_bp, url_prefix='/api/v1/employees')
    app.register_blueprint(payroll_bp,   url_prefix='/api/v1/payroll')
    app.register_blueprint(transfers_bp, url_prefix='/api/v1/transfers')
    app.register_blueprint(reports_bp,   url_prefix='/api/v1/reports')
    app.register_blueprint(webhooks_bp,  url_prefix='/api/v1/webhooks')

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'status': 'error', 'message': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'status': 'error', 'message': 'Resource not found'}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({'status': 'error', 'message': 'Too many requests'}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    @app.route('/api/v1/health')
    def health():
        return jsonify({'status': 'success', 'message': 'Payroll API is running!'}), 200

    return app
