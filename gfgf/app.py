from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'mysite/static/uploads'


db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.String(64), primary_key=True)  # Telegram ID
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20), nullable=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Почта
    username = db.Column(db.String(50), unique=True, nullable=False)  # Имя пользователя
    password = db.Column(db.String(128), nullable=False)  # Хешированный пароль
    profile_image = db.Column(db.String(200), nullable=True)  # Путь к изображению профиля

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # Внешний ключ на курс
    task_data = db.Column(db.JSON, nullable=False)  # Данные задания в формате JSON

    # Связь с курсом
    course = db.relationship('Course', backref='tasks', lazy=True)  # Здесь оставляем backref='tasks'


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey('user.id'), nullable=False)  # Связь с пользователем
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # Связь с курсом
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)  # Связь с конкретным заданием
    score = db.Column(db.Float, nullable=False)  # Оценка или баллы за задание
    completed_at = db.Column(db.DateTime, nullable=True)  # Дата выполнения задания
    feedback = db.Column(db.Text, nullable=True)  # Обратная связь от учителя, если необходимо

    # Связь с пользователем
    user = db.relationship('User', backref='results', lazy=True)

    # Связь с курсом
    course = db.relationship('Course', backref='results', lazy=True)

    # Связь с заданием
    task = db.relationship('Task', backref='results', lazy=True)


# Routes
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        existing_user = User.query.filter_by(id=telegram_id).first()
        if existing_user:
            return jsonify({'message': 'User already registered'}), 200
    return render_template('index.html')

@app.route('/')
def main():
    teacher_id = session.get('teacher_id')
    if teacher_id:
        teacher = Teacher.query.get(teacher_id)
        if teacher:
            # Если учитель вошел в систему, передаем в шаблон информацию о нем
            return render_template('main.html', logged_in=True)
    return render_template('main.html', logged_in=False)

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    try:
        # Проверяем, что данные переданы в формате JSON
        data = request.get_json()
        if not data or 'telegram_id' not in data:
            return 'Invalid request data', 400  # Если данных нет или отсутствует ключ telegram_id

        telegram_id = data['telegram_id']

        # Проверяем, есть ли пользователь в базе данных
        existing_user = User.query.filter_by(id=telegram_id).first()
        if existing_user:
            return jsonify({'message': 'User already registered'}), 200

    except Exception:
        if request.method == 'POST':
            telegram_id = request.form['telegram_id']
            existing_user = User.query.filter_by(id=telegram_id).first()
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            grade = request.form['grade']

            # Проверяем наличие пользователя в базе данных
            existing_user = User.query.filter_by(id=telegram_id).first()
            if existing_user:
                return jsonify({'message': 'User already registered'}), 200

            # Создаем нового пользователя, если его нет в базе данных
            new_user = User(id=telegram_id, first_name=first_name, last_name=last_name, grade=grade)
            db.session.add(new_user)
            db.session.commit()
            return 'Registration successful'

    return render_template('register_user.html')


from sqlalchemy.exc import IntegrityError

@app.route('/register_teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Хеширование пароля
        profile_image = request.files['profile_image']

        # Создание папки, если её нет
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Сохранение изображения профиля
        if profile_image and profile_image.filename:
            # Генерация уникального имени для файла
            filename = f"{uuid.uuid4().hex}_{profile_image.filename}"
            # Путь к файлу, который сохраняется в папке uploads
            image_path = os.path.join('uploads', filename)
            # Сохранение файла в папке static/uploads
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            image_path = None

        # Сохранение учителя в базе данных
        teacher = Teacher(email=email, username=username, password=password, profile_image=image_path)
        try:
            db.session.add(teacher)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "Пользователь с таким email или username уже существует", 400

        return redirect(url_for('login_teacher'))

    return render_template('register_teacher.html')


@app.route('/login_teacher', methods=['GET', 'POST'])
def login_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and check_password_hash(teacher.password, password):
            session['teacher_id'] = teacher.id
            return redirect(url_for('profile'))

        return 'Invalid credentials', 401

    return render_template('login_teacher.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('login_teacher'))

    teacher_id = session['teacher_id']
    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    applications = Application.query.join(Course).filter(Course.teacher_id == teacher_id).all()
    return render_template('teacher_dashboard.html', courses=courses, applications=applications)

@app.route('/create_course', methods=['POST'])
def create_course():
    if 'teacher_id' not in session:
        return redirect(url_for('login_teacher'))

    name = request.form['name']
    description = request.form['description']
    teacher_id = session['teacher_id']

    new_course = Course(name=name, description=description, teacher_id=teacher_id)
    db.session.add(new_course)
    db.session.commit()
    return 'Course created successfully'

@app.route('/apply_course', methods=['POST'])
def apply_course():
    user_id = request.form['user_id']
    course_id = request.form['course_id']

    if not User.query.get(user_id):
        return 'User not found', 404

    if not Course.query.get(course_id):
        return 'Course not found', 404

    application = Application(user_id=user_id, course_id=course_id)
    db.session.add(application)
    db.session.commit()
    return 'Application submitted'

@app.route('/approve_application', methods=['POST'])
def approve_application():
    application_id = request.form['application_id']
    application = Application.query.get(application_id)

    if application:
        application.status = 'Approved'
        db.session.commit()
        return 'Application approved'

    return 'Application not found', 404


# CODE:FROM:SOGINASA
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    teacher_id = session.get('teacher_id')
    if teacher_id:
        # Получаем курсы, созданные учителем
        courses = Course.query.filter_by(teacher_id=teacher_id).all()

        if request.method == 'POST':
            task_data = request.form.get('task_data')  # Данные задания
            course_id = request.form.get('course_id')  # ID выбранного курса

            # Создаем новый объект Task
            new_task = Task(course_id=course_id, task_data=task_data)

            # Добавляем задачу в сессию и сохраняем в базе данных
            db.session.add(new_task)
            db.session.commit()

            return redirect('/tasks')  # Перенаправляем на страницу с заданиями

        return render_template('tasks.html', courses=courses)

    return redirect('/login')  # Если учитель не авторизован

@app.route('/save_task', methods=['POST'])
def save_task():
    teacher_id = session.get('teacher_id')
    if teacher_id:
        # Получаем данные из тела запроса в формате JSON
        task_data = request.get_json()

        # Извлекаем данные из JSON
        questions = task_data.get('taskData', [])  # Получаем список вопросов
         # Получаем ID курса
        course_id = task_data.get('course_id')
        # Создаем новый объект Task
        new_task = Task(course_id=course_id, task_data=questions)

        # Добавляем задачу в сессию и сохраняем в базе данных
        db.session.add(new_task)
        db.session.commit()

        # Возвращаем ответ с сообщением
        return jsonify({'message': 'Задание сохранено'}), 200
    return jsonify({'message': 'Зарегестрируйтесь'}), 500

@app.route('/tabs')
def tabs():
    teacher_id = session.get('teacher_id')
    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    tasks = []
    for course in courses:
        this_tasks = Task.query.filter_by(course_id=course.id).all()
        for task in this_tasks:
            tasks.append(task)
    if not teacher_id:
        return redirect('/login_teacher', logged_in=False)
    return render_template('tab_chooise.html', logged_in=True, courses=courses, tasks=tasks)


@app.route('/tab/<task_id>', methods=['GET'])
def tab(task_id):
    # Получаем задание по его ID, если его нет - 404
    task = Task.query.get_or_404(task_id)
    return render_template('tabs.html', task=task)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile')
def profile():
    # Предполагается, что ID учителя хранится в сессии после входа в систему
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        return redirect('/login_teacher')  # Перенаправление на страницу входа, если учитель не авторизован

    # Получение данных учителя из базы
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return "Профиль не найден", 404

    return render_template('profile.html', teacher=teacher)

@app.route('/user_dashboard')
def user_dashboard():
    courses = Course.query.all()
    return render_template('dashboard.html', courses=courses)

@app.route('/prof_chang', methods=['GET', 'POST'])
def edit_profile():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        return redirect('/login_teacher')

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return "Учитель не найден", 404

    if request.method == 'POST':
        # Получение данных из формы
        new_username = request.form['username']
        new_email = request.form['email']
        profile_image = request.files.get('profile_image')

        # Проверка уникальности email и имени пользователя
        if new_email != teacher.email and Teacher.query.filter_by(email=new_email).first():
            return "Этот email уже используется", 400
        if new_username != teacher.username and Teacher.query.filter_by(username=new_username).first():
            return "Это имя пользователя уже занято", 400

        # Сохранение нового изображения профиля, если оно загружено
        if profile_image and profile_image.filename:
            # Удаление старого аватара, если он есть
            if teacher.profile_image:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], teacher.profile_image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Сохранение нового изображения
            filename = f"{uuid.uuid4().hex}_{secure_filename(profile_image.filename)}"
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.join('uploads', filename)
            teacher.profile_image = image_path

        # Обновление данных учителя
        teacher.username = new_username
        teacher.email = new_email

        # Сохранение изменений в базе данных
        db.session.commit()

        return redirect(url_for('profile'))

    return render_template('prof_chang.html', teacher=teacher)


@app.route('/applications')
def applications():
    return render_template('applications.html')



@app.route('/course/<int:course_id>')
def course_details(course_id):
    # Получаем курс по ID
    course = Course.query.get_or_404(course_id)
    # Получаем задания, связанные с курсом
    tasks = Task.query.filter_by(course_id=course_id).all()
    return render_template('course_details.html', course=course, tasks=tasks)

@app.route('/task/<int:task_id>')
def task_page(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return render_template('task.html', task_data=task.task_data)

def calculate_score():
    return 0 # пока что проблема в том что мы не сохраняем task_data

@app.route('/submit_task/<int:task_id>', methods=['POST'])
def submit_task(task_id):
    # Получаем все ответы с формы
    answers = {}
    for question_index in range(1, len(request.form) + 1):
        question_data = request.form.getlist(f'question_{question_index}')
        if question_data:  # Если ответ на вопрос есть
            answers[question_index] = question_data

    # Здесь вам нужно будет сохранить ответы в базу данных
    # Получаем информацию о пользователе и курсе
    task = Task.query.get(task_id)
    user_id = request.form.get('telegram_id')  # Предполагаем, что у вас есть текущий пользователь (сессия или JWT)
    course_id = task.course_id  # Получаем ID курса для данного задания

    # Записываем результаты
    for question_index, answer in answers.items():
        # Здесь вы можете хранить результат, используя модель Result
        result = Result(
            user_id=user_id,
            course_id=course_id,
            task_id=task_id,
            score=calculate_score(answer),  # Функция для подсчета баллов за ответ
            completed_at=datetime.utcnow(),
            feedback=None  # Можно добавить обратную связь, если нужно
        )
        db.session.add(result)

    db.session.commit()

    # Перенаправляем на страницу с результатами или подтверждением
    return redirect(url_for('task_submitted', task_id=task_id))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)

