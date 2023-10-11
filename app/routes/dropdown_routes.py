from flask import Flask, render_template, flash, redirect, url_for, request
from app.forms.register_form import RegistrationForm
from app.forms.login_form import LoginForm
from app import app, db, login
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

@app.route("/settings", methods=["GET", "POST"])
def settings():
    return render_template("settings.html", title="Settings")