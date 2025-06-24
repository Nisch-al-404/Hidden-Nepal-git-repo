from app import create_app
app = create_app()

app.config['SECRET_KEY'] = 'your_secret_key_here'



if __name__ == '__main__':
    app.run(debug=True)
