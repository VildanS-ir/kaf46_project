from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, mail
from app.models import User, Task, Team, TeamMember, Comment
from datetime import datetime

auth = Blueprint('auth', __name__)
tasks = Blueprint('tasks', __name__)
teams = Blueprint('teams', __name__)

# Регистрация и вход
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('tasks.dashboard'))
    
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid credentials!')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        return redirect(url_for('tasks.dashboard'))
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Задачи
@tasks.route('/dashboard')
@login_required
def dashboard():
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    team_tasks = Task.query.filter(Task.team_id.isnot(None)).all()
    return render_template('tasks/dashboard.html', tasks=user_tasks, team_tasks=team_tasks)

@tasks.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d')
        priority = request.form.get('priority')
        
        task = Task(
            title=title,
            description=description,
            deadline=deadline,
            priority=priority,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        
        flash('Task created!')
        return redirect(url_for('tasks.dashboard'))
    
    return render_template('tasks/create.html')

# Команды
@teams.route('/teams')
@login_required
def team_list():
    teams = Team.query.all()
    return render_template('teams/list.html', teams=teams)

@teams.route('/team/<int:team_id>')
@login_required
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    return render_template('teams/detail.html', team=team)