from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
# Set the secret key to a random value
app.secret_key = "SECRET KEY"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Quizblitz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)


#Models
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable = False)
    name = db.Column(db.String(50), nullable = False)
    password = db.Column(db.String(100), nullable = False)
    qualification = db.Column(db.String(80), nullable = False)
    dob = db.Column(db.Date, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password,name,qualification= None, dob = None, is_admin=False):
        self.username = username
        self.is_admin = is_admin
        self.name = name
        self.qualification = qualification
        self.dob = dob
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique = True)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject')
    quiz = db.relationship('Quiz', back_populates = 'subject')
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    questions_count = db.Column(db.Integer,nullable = False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    questions = db.relationship('Question', back_populates="chapter")

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    quiz_name = db.Column(db.String(50), nullable = True)
    duration = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    subject = db.relationship('Subject',back_populates = "quiz")
    questions = db.relationship('Question', back_populates ='quiz')
    chapter = db.relationship('Chapter', backref = "quizzes")

    def __init__(self, quiz_name, duration, chapter_id, score=0, subject_id= None):
        self.score = score
        self.quiz_name = quiz_name
        self.duration = duration
        self.chapter_id = chapter_id
        self.subject_id = subject_id

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    question = db.Column(db.Text,nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    correct = db.Column(db.Integer, nullable=False)

    quiz = db.relationship('Quiz', back_populates = "questions")
    chapter = db.relationship('Chapter',back_populates = "questions")
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'),nullable=True)

class Scores(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable = False)
    total = db.Column(db.Integer, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable = False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable = True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable = True)

    subject = db.relationship('Subject',backref = 'scores')
    user = db.relationship('User', backref='scores')
    quiz = db.relationship('Quiz', backref='scores')
    chapter = db.relationship('Chapter', backref = 'scores')

    def __init__(self, score, total, user_id, quiz_id, subject_id, chapter_id):
        self.score = score
        self.total = total
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.subject_id = subject_id
        self.chapter_id = chapter_id

with app.app_context():
    db.create_all()

    # Check if an admin user already exists
    admin = User.query.filter_by(is_admin=True).first()

    admin_user = User(
        username="quizmaster@gmail.com",
        name="Quiz Master",  # Add a valid name here
        password=generate_password_hash("admin123"),
        qualification="Admin",
        dob=datetime.strptime("2000-01-01", '%Y-%m-%d').date(),
        is_admin=True
    )
    db.session.add(admin_user)
    db.session.commit()

@app.route("/")
def home():
    return render_template("home.html")

#REGISTERATION
@app.route("/register", methods = ['GET','POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        qualification = request.form.get('qualification')
        dob = request.form.get('dob')
        dob = datetime.strptime(dob, '%Y-%m-%d').date()

        exists = User.query.filter_by(username=username).first()
        if exists:
            flash("User already exists, Login!")
            return redirect(url_for('login_page'))

       # if not username or not password or not qualification or not dob:
        #    return redirect(url_for('register_page'))

        hashed_password = generate_password_hash(password)

        new_user = User(username = username, password = hashed_password, name = name ,qualification = qualification, dob = dob)
        db.session.add(new_user)
        db.session.commit()
        flash("Registeration successful!, Login please!","success")
        return redirect(url_for('login_page'))
    return render_template("registerpage.html")

@app.route("/login")
def login_page():
    return render_template("loginpage.html")
@app.route("/login", methods = ['GET','POST'])
def login_post():
    session.pop('_flashes', None)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        this_user = User.query.filter_by(username=username).first()

        if not this_user:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login_page'))

        #if not this_user or not this_user.check_password(password):
         #   flash("Invalid username or password")
          #  return redirect(url_for('login_page'))

        session['username'] = this_user.username
        session['user_id'] = this_user.id
        session['is_admin'] = this_user.is_admin

        #login successful
        if this_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template("loginpage.html")


#admin dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    subjects = Subject.query.all()

    return render_template('admin_dashboard.html', subjects=subjects)

#adding subject
@app.route("/add/subject", methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        Data = Subject(name = name, description = description)
        db.session.add(Data)
        db.session.commit()
        flash("Subject created successfully","success")
        return redirect(url_for('admin_dashboard'))
    return render_template('New Subject.html')


@app.route("/edit/subject/<int:subject_id>", methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        subject.name = request.form["name"]
        subject.description = request.form["description"]
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_subject.html', subject=subject)


@app.route("/delete/subject/<int:subject_id>", methods = ['GET','POST'])
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if subject:
        chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        for chapter in chapters:
            db.session.delete(chapter)
        db.session.delete(subject)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

#adding chapter
@app.route("/add/chapter", methods=['GET', 'POST'])
def add_chapter():
    if request.method == 'POST':
        name = request.form['name']
        questions_count = int(request.form['noofquestions'])
        subject_id = request.form['subject_id']
        Data = Chapter(name = name, questions_count = questions_count, subject_id = subject_id)
        db.session.add(Data)
        db.session.commit()
        flash("Chapter created successfully")
        return redirect(url_for('admin_dashboard'))
    subject = Subject.query.all()
    return render_template('add_chapter.html', subjects = subject)

@app.route("/edit/chapter/<int:chapter_id>", methods = ['GET','POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if request.method == 'POST':
        name = request.form['name']
        questions_count = int(request.form['noofquestions'])
        subject_id = request.form['subject_id']

        chapter.name = name
        chapter.questions_count = questions_count
        chapter.subject_id = subject_id

        db.session.commit()
        flash("Chapter edited")
        return redirect(url_for('admin_dashboard'))
    subject = Subject.query.all()
    return render_template('edit_chapter.html', subjects = subject, chapter = chapter)

@app.route("/delete/chapter/<int:chapter_id>", methods = ['GET','POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


#quiz_header
@app.route("/admin/quiz")
def Aquiz():
    quizzes = Quiz.query.all()
    return render_template("Aquiz.html", quizzes = quizzes)


@app.route("/create/quiz", methods = ['GET','POST'])
def create_quiz():
    chapters = Chapter.query.all()
    if request.method == "POST":
        quiz_name = request.form.get('quiz_name')
        duration = int(request.form.get('duration'))
        chapter_id = int(request.form.get('chapter_id'))
        chapter = Chapter.query.get(chapter_id)
        subject_id = chapter.subject.id

        quiz = Quiz(quiz_name = quiz_name, duration = duration, chapter_id = chapter_id,subject_id = subject_id)
        db.session.add(quiz)
        db.session.commit()

        flash("successfull")
        return redirect(url_for('Aquiz'))

    return render_template("create_quiz.html", chapters = chapters)

@app.route("/edit/quiz/<int:quiz_id>", methods = ['GET','POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    chapters = Chapter.query.all()
    if request.method == "POST":
        quiz.quiz_name = request.form.get('quiz_name')
        quiz.duration = int(request.form.get('duration'))
        quiz.chapter_id = int(request.form.get('chapter_id'))
        chapter = Chapter.query.get(quiz.chapter_id)

        quiz.subject_id = chapter.subject.id
        db.session.commit()
        return redirect(url_for('Aquiz'))
    return render_template("edit_quiz.html", quiz =quiz, chapters = chapters)

@app.route("/delete/quiz/<int:quiz_id>", methods = ['GET','POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    Scores.query.filter_by(quiz_id = quiz_id).delete()
    Question.query.filter_by(quiz_id = quiz_id).delete()
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('Aquiz'))




@app.route("/make/question" , methods = ['GET','POST'])
def make_question():
    quiz_id = request.args.get('quiz_id')

    if request.method == "POST":
        title = request.form.get('title')
        question = request.form['statement']
        option1 = request.form['1']
        option2 = request.form['2']
        option3 = request.form['3']
        option4 = request.form['4']
        correct = int(request.form['correct'])
        quiz_id = int(request.form['quiz_id'])

        question = Question(title = title,question=question, option1 =option1, option2 =option2,option3 =option3, option4 =option4, correct = correct, quiz_id = quiz_id)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('Aquiz'))
    quizzes = Quiz.query.filter_by()
    return render_template("new_question.html",quizzes = quizzes, quiz_id = quiz_id)



@app.route("/edit/question/<int:question_id>", methods = ['GET','POST'])
def edit_question(question_id):
    question = Question.query.get(question_id)
    if request.method == "POST":
        title = request.form['title']
        statement = request.form['statement']
        option1 = request.form['1']
        option2 = request.form['2']
        option3 = request.form['3']
        option4 = request.form['4']
        correct = int(request.form['correct'])

        question.title = title
        question.statement = statement
        question.option1 = option1
        question.option2 = option2
        question.option3 = option3
        question.option4 = option4
        question.correct = correct
        db.session.commit()
        flash("Question updated successfully")
        return redirect(url_for('Aquiz'))
    return render_template("edit_question.html", question = question)

@app.route("/delete/question/<int:question_id>", methods = ['GET','POST'])
def delete_question(question_id):
    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('Aquiz'))

@app.route("/admin/summary")
def Asummary():
    users = User.query.filter_by(is_admin=0).all()
    username= []
    quiz_attempts = []

    for user in users:
        attempts = Scores.query.filter_by(user_id=user.id).count()
        username.append(user.username)
        quiz_attempts.append(attempts)

    return render_template("Asummay.html", username = username, quiz_attempts = quiz_attempts)
@app.route("/admin/search/all", methods = ['GET','POST'])
def admin_search():
    search_query = request.form['search_query']

    #search for quiz
    quizzes = Quiz.query.filter(Quiz.quiz_name.contains(search_query)).all()

    #search for users
    users = User.query.filter(
        or_(
            User.username.ilike(f"%{search_query}%"),
            User.name.ilike(f"%{search_query}%"),
            User.qualification.ilike(f"%{search_query}%")
        )
    ).all()

    #search for subjects
    subjects = Subject.query.filter(Subject.name.contains(search_query)).all()

    return render_template("search.html",quizzes = quizzes,users = users,subjects = subjects)






#user dashboard
@app.route("/user/dashboard", methods = ['GET'])
def user_dashboard():
    username = session.get("username")
    user = User.query.filter_by(username = username).first()
    #user = User.query.get(session['user_id'])
    quizzes = Quiz.query.all()
    chapters = Chapter.query.all()

    attempted_quizzes_ids = session.get(f"attempted_quizzes_{user.id}",[])

    available_quizzes = [quiz for quiz in quizzes if quiz.id not in attempted_quizzes_ids]
    attempted_quiz_data = [quiz for quiz in quizzes if quiz.id in attempted_quizzes_ids]
    user_scores = Scores.query.filter(Scores.user_id == user.id, Scores.quiz_id.in_(attempted_quizzes_ids)).all()

    return render_template("user_dashboard.html", quizzes =available_quizzes, user = user,chapters = chapters, attempted_quiz = attempted_quiz_data, user_scores = user_scores)



@app.route("/view/quiz/<int:quiz_id>", methods = ['GET','POST'])
def view_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(quiz.subject_id)
    print(f"Subject:{subject}")
    return render_template("view_quiz_details.html", quiz = quiz,chapter = chapter,subject = subject)

@app.route("/start/quiz/<int:quiz_id>")
def start_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id = quiz.id).all()
    return render_template("start_quiz.html",quiz = quiz,questions = questions)




@app.route("/submit/quiz/<int:quiz_id>", methods = ['GET','POST'])
def submit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id = quiz_id).all()
    score = 0

    for question in questions:
        selected = request.form.get(f"q{question.id}")
        if selected:
            if int(selected) == question.correct:
                score += 1

    subject_id = quiz.subject_id
    chapter_id = quiz.chapter_id

    user_id = session['user_id']
    attempted_quizzes = session.get(f'attempted_quizzes_{user_id}',[])
    if quiz_id not in attempted_quizzes:
        attempted_quizzes.append(quiz_id)
        session[f"attempted_quizzes_{user_id}"] =attempted_quizzes

    new_score = Scores(user_id = session['user_id'],quiz_id = quiz_id,score=score, total = len(questions), subject_id = subject_id, chapter_id = chapter_id)
    db.session.add(new_score)
    db.session.commit()


    return redirect(url_for('user_scores',quiz_id = quiz_id))
    #return render_template("Uscores.html",quiz = quiz, score = score,total = len(questions))

@app.route("/user/profile", methods = ['GET','POST'])
def user_profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.username = request.form['username']
        user.name = request.form['name']
        user.qualification = request.form['qualification']
        user.dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d").date()
        db.session.commit()
        flash("Your Profile has been updated")
        return redirect("user_dashboard")

    return render_template("user_profile.html", user = user)

@app.route("/user/scores/<int:quiz_id>")
def user_scores(quiz_id):
    score = session.get(f'quiz_{quiz_id}_score',0)
    quiz = Quiz.query.get(quiz_id)
    user_scores = Scores.query.filter_by(user_id=session['user_id']).all()
    return render_template("Uscores.html", user_scores = user_scores, score = score,quiz = quiz)



"""@app.route("/user/search", methods = ['GET','POST'])
def search_by_chapter():
    if request.method == 'POST':
        chapter = request.form['chapter_name']
        chapter = Chapter.query.filter_by(name=chapter).first()
        user_id = session['user_id']
        if chapter:
            scores = Scores.query.filter_by(chapter_id=chapter.id, user_id = session['user_id']).all()
        else:
            scores =  []
        return render_template("user_search.html",scores = scores)

    return redirect(url_for("user_dashboard"))"""

@app.route("/user/summary")
def user_summary():
    chapter_quiz_count = db.session.query(Chapter.name, db.func.count(Quiz.id)).join(Quiz).group_by(Chapter.id).all()
    labels = [chapter[0] for chapter in chapter_quiz_count]
    quiz_counts = [chapter[1] for chapter in chapter_quiz_count]

    total_quizzes_count = db.session.query(db.func.count(Quiz.id)).scalar()
    user_id = session['user_id']
    attempted_quizzes = session.get(f'attempted_quizzes_{user_id}',[])
    attempted_quizzes_count = len(attempted_quizzes)
    return render_template("Usummary.html",labels=labels,quiz_counts=quiz_counts, total_quizzes_count=total_quizzes_count, attempted_quizzes_count=attempted_quizzes_count)



if __name__ == '__main__':
    app.run(debug=True)