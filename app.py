from app import create_app
from app.contributor import contributor_bp
app = create_app()

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.register_blueprint(contributor_bp, url_prefix='/contributor')


if __name__ == '__main__':
    app.run(debug=True)
