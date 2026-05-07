from flask import (Blueprint, render_template, request, redirect,
                   url_for, session)
from .config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if (username == Config.ADMIN_USERNAME and
                password == Config.ADMIN_PASSWORD):
            session["logged_in"] = True
            session["user"] = username
            session["cashier_name"] = "Cashier #1"
            return redirect(url_for("main.index"))
        else:
            return render_template(
                "login.html",
                error="❌ Invalid credentials! Please try again.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
