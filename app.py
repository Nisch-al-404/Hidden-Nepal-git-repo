from app import create_app
app = create_app()

app.config['SECRET_KEY'] = 'your_secret_key_here'

from app.contributor.routes import contributor_bp
app.register_blueprint(contributor_bp, url_prefix='/contributor')


if __name__ == '__main__':
    app.run(debug=True)
