"""
CS-GY 6083 - Project Part II
Flask Application Factory

This module initializes the Flask application with all configurations,
blueprints, and extensions.
"""

from flask import Flask
from .config import Config


def create_app(config_class=Config):
    """
    Application factory pattern for Flask.
    Creates and configures the Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable Jinja2 auto-escaping for XSS protection
    # This is enabled by default for .html, .htm, .xml, .xhtml templates
    app.jinja_env.autoescape = True
    
    # Register blueprints
    from .auth import auth_bp
    from .routes_customer import customer_bp
    from .routes_employee import employee_bp
    from .routes_analytics import analytics_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(employee_bp, url_prefix='/admin')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    return app
