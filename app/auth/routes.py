import mysql.connector
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from app.models import get_db, User



@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_panel'))
        return redirect(url_for('contributor.contributor_dashboard'))

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn=None
        cursor=None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user is None:
                flash("User does not exist", "danger")
                return render_template("auth/login.html")

            if user:
                if user and check_password_hash(user['password_hash'], password):
                    user_obj = User(user['id'],user['username'], user['email'], user['role'])
                    login_user(user_obj)
                    flash("🎉 Logged in successfully!", "success")

                    if user['role'] == 'admin':
                        return redirect(url_for('admin.admin_panel'))

                    return redirect(url_for('contributor.contributor_dashboard'))
                else:
                    flash("❌ Invalid email or password", "danger")

        except Exception as e:
            print("Login error:", e)
            flash("⚠️ Something went wrong during login", "danger")

        finally:
            if conn:
                conn.close()
                cursor.close()
    return render_template("auth/login.html")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username:str = request.form['username']
        email:str = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)
        conn=None
        cursor=None

        try:
            conn = get_db()
            cursor = conn.cursor()
            print("Entered:", password)
            print("Entered:", email)

            cursor.execute("""
                           INSERT INTO users  (username, email, password_hash, role, can_contribute)
                           VALUES (%s, %s, %s, 'contributor', TRUE)
                           """, (username, email, hashed_password))
            conn.commit()
            flash("🎉 Registered successfully!", "success")
            return redirect(url_for('auth.login'))

        except mysql.connector.IntegrityError:
            flash("⚠️ Email already exists!", "danger")
        except mysql.connector.Error:
            flash("💥 Database error ", "danger")
        except KeyError:
            flash("🧩 Missing form data ", "danger")
        except Exception:
            flash(f"⚠️ Unexpected error occurred", "danger")



        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    return render_template("auth/register.html")

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login'))