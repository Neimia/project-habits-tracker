from flask import Flask, render_template, redirect, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.user import RegisterForm, LoginForm
from forms.habit import AddHabitForm, CheckHabitForm, ImportHabitsForm
from data.users import User
from data.habits import Habit, HabitCheck
from data import db_session
import datetime
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='регистрация', form=form,
                                   message="пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.username == form.username.data).first():
            return render_template('register.html', title='регистрация', form=form,
                                   message="пользователь уже существует")
        user = User(
            username=form.username.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/habits")
        return render_template('login.html', message="неверный логин или пароль", form=form)
    return render_template('login.html', title='авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/habits')
@login_required
def habits_list():
    db_sess = db_session.create_session()
    habits = db_sess.query(Habit).filter(Habit.user_id == current_user.id).all()

    habits_data = []
    for habit in habits:
        checks_count = db_sess.query(HabitCheck).filter(HabitCheck.habit_id == habit.id).count()
        week_ago = datetime.datetime.now().date() - datetime.timedelta(days=7)
        week_checks = db_sess.query(HabitCheck).filter(
            HabitCheck.habit_id == habit.id,
            HabitCheck.check_date >= week_ago
        ).count()

        habits_data.append({
            'habit': habit,
            'checks_count': checks_count,
            'week_checks': week_checks
        })

    return render_template('habits_list.html', habits_data=habits_data)


@app.route('/habits/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    form = AddHabitForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        habit = Habit(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db_sess.add(habit)
        db_sess.commit()
        return redirect('/habits')
    return render_template('add_habit.html', form=form)


@app.route('/habits/<int:habit_id>')
@login_required
def habit_detail(habit_id):
    db_sess = db_session.create_session()
    habit = db_sess.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()
    if not habit:
        return redirect('/habits')

    checks = db_sess.query(HabitCheck).filter(HabitCheck.habit_id == habit_id).order_by(
        HabitCheck.check_date.desc()).all()
    total_checks = len(checks)

    calendar_data = {}
    for i in range(30):
        date = datetime.datetime.now().date() - datetime.timedelta(days=i)
        checked = db_sess.query(HabitCheck).filter(
            HabitCheck.habit_id == habit_id,
            HabitCheck.check_date == date
        ).first() is not None
        calendar_data[date] = checked

    return render_template('habit_detail.html', habit=habit, checks=checks,
                           total_checks=total_checks, calendar_data=calendar_data)


@app.route('/habits/<int:habit_id>/check', methods=['GET', 'POST'])
@login_required
def check_habit(habit_id):
    db_sess = db_session.create_session()
    habit = db_sess.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()
    if not habit:
        return redirect('/habits')

    form = CheckHabitForm()
    if form.validate_on_submit():
        existing = db_sess.query(HabitCheck).filter(
            HabitCheck.habit_id == habit_id,
            HabitCheck.check_date == form.check_date.data
        ).first()

        if existing:
            return render_template('check_habit.html', form=form, habit=habit,
                                   message="отметка за эту дату уже существует")

        check = HabitCheck(
            habit_id=habit_id,
            check_date=form.check_date.data
        )
        db_sess.add(check)
        db_sess.commit()
        return redirect(f'/habits/{habit_id}')

    form.check_date.data = datetime.datetime.now().date()
    return render_template('check_habit.html', form=form, habit=habit)


@app.route('/habits/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    db_sess = db_session.create_session()
    habit = db_sess.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()
    if habit:
        db_sess.delete(habit)
        db_sess.commit()
    return redirect('/habits')


@app.route('/api/habits', methods=['GET'])
@login_required
def api_get_habits():
    db_sess = db_session.create_session()
    habits = db_sess.query(Habit).filter(Habit.user_id == current_user.id).all()

    return jsonify({
        'habits': [{
            'id': h.id,
            'name': h.name,
            'description': h.description,
            'created_date': h.created_date.isoformat(),
            'checks_count': len(h.checks)
        } for h in habits]
    })


@app.route('/api/habits/<int:habit_id>/check', methods=['POST'])
@login_required
def api_check_habit(habit_id):
    data = request.get_json()
    check_date_str = data.get('date', datetime.datetime.now().date().isoformat())

    try:
        check_date = datetime.datetime.strptime(check_date_str, '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'неверный формат даты'}), 400

    db_sess = db_session.create_session()
    habit = db_sess.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()

    if not habit:
        return jsonify({'error': 'привычка не найдена'}), 404

    existing = db_sess.query(HabitCheck).filter(
        HabitCheck.habit_id == habit_id,
        HabitCheck.check_date == check_date
    ).first()

    if existing:
        return jsonify({'error': 'уже отмечено'}), 400

    check = HabitCheck(habit_id=habit_id, check_date=check_date)
    db_sess.add(check)
    db_sess.commit()

    return jsonify({'message': f'отмечено {habit.name} за {check_date}'})


@app.route('/api/habits/<int:habit_id>/stats', methods=['GET'])
@login_required
def api_habit_stats(habit_id):
    db_sess = db_session.create_session()
    habit = db_sess.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()

    if not habit:
        return jsonify({'error': 'привычка не найдена'}), 404

    total_checks = len(habit.checks)
    checks_dates = [c.check_date for c in habit.checks]

    streak = 0
    current_streak = 0
    today = datetime.datetime.now().date()

    for i in range(30):
        date = today - datetime.timedelta(days=i)
        if date in checks_dates:
            current_streak += 1
        else:
            if current_streak > streak:
                streak = current_streak
            current_streak = 0

    return jsonify({
        'id': habit.id,
        'name': habit.name,
        'description': habit.description,
        'total_checks': total_checks,
        'current_streak': streak
    })


@app.route('/habits/import', methods=['GET', 'POST'])
@login_required
def import_habits():
    form = ImportHabitsForm()
    errors = []
    message = None

    if form.validate_on_submit():
        file = form.db_file.data
        filename = secure_filename(file.filename)

        if not filename.endswith('.db'):
            errors.append('файл должен иметь расширение .db')
            return render_template('import_habits.html', form=form, errors=errors)

        temp_path = os.path.join('uploads', f'temp_{current_user.id}_{filename}')
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)

        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
            if not cursor.fetchone():
                errors.append('в файле нет таблицы с привычками')
                conn.close()
                os.remove(temp_path)
                return render_template('import_habits.html', form=form, errors=errors)

            cursor.execute("SELECT name, description FROM habits")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                errors.append('таблица с привычками пуста')
                os.remove(temp_path)
                return render_template('import_habits.html', form=form, errors=errors)

            db_sess = db_session.create_session()
            imported_count = 0
            skipped_count = 0

            for row in rows:
                name = row[0]
                description = row[1] if len(row) > 1 and row[1] else ''

                existing = db_sess.query(Habit).filter(
                    Habit.user_id == current_user.id,
                    Habit.name == name
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                habit = Habit(
                    name=name,
                    description=description,
                    user_id=current_user.id
                )
                db_sess.add(habit)
                imported_count += 1

            db_sess.commit()
            message = f'импортировано: {imported_count}, пропущено (уже есть): {skipped_count}'

        except Exception as e:
            errors.append(f'ошибка при чтении файла: {str(e)}')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if message:
            return render_template('import_habits.html', form=form, message=message)

    return render_template('import_habits.html', form=form, errors=errors)


def main():
    db_session.global_init("db/habits.db")
    app.run(debug=True)


if __name__ == '__main__':
    main()
