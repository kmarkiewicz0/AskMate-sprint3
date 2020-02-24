from flask import Flask, render_template, request, redirect, url_for
from flask import session, escape
import util, database_manager, hashing_utility, session_controller
import os
from datetime import datetime, timedelta

app = Flask(__name__)

###################### SESSION SETTINGS ######################
app.secret_key = b'\xa0\xd7\xe2\x8er\xd6\xd2\xd8\x8b\xce\xb3T'
app.permanent_session_lifetime = timedelta(minutes=10)
###############################################################


@app.route('/')
def index():

    last_five_questions = database_manager.get_last_five()

    if 'username' in session:

        username = session['username']
        userID = database_manager.getUserIDbyUsername(username)
        ###### SESSION REFRESH #######
        session_controller.session_refresh(session)
        ##############################


        return render_template('index.html', questions=last_five_questions,
                               page_title='AskMate', username=username, userID=userID)

    return render_template('index.html', questions = last_five_questions,
                           page_title = 'AskMate')

@app.route('/list')
def list():

    session_controller.session_refresh(session)
    question_file = database_manager.import_questions_for_list()
    titles = ['ID','Submission time','Title',]
    sort = request.args.get('sort')
    search = request.args.get('search')

    if sort:
    # If sort has a value
        sorted_question_file = util.sort(sort)


        return render_template('list.html', titles=titles, questions=sorted_question_file,
                               page_title = 'AskMate - List of questions')

    if search:

        search_result = util.search_results(question_file,search)

        return render_template('list.html', titles=titles,questions=search_result,
                               page_title = 'AskMate - List of questions')

    return render_template('list.html',titles=titles, questions=question_file,
                           page_title = 'AskMate - List of questions')

@app.route('/add_question', methods=['GET','POST'])
def add():

    userID = session_controller.session_refresh(session)

    if userID:

        if request.method == "POST":

            title = request.form['title']
            message = request.form['message']
            id = database_manager.highest_id()
            view = 0
            vote = 0
            image = None
            timestamp = datetime.now().replace(microsecond=0)

            values = (id,timestamp,view,vote,title,message,image,userID)
            database_manager.add_question(values)

            return redirect (url_for('question',id=id))

        return render_template('add_question.html', page_title = 'AskMate - Add question')

    return redirect('/login')

@app.route('/question/<id>', methods=['GET','POST'])
def question(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/list')

    userID = session_controller.session_refresh(session)
    question = database_manager.show_question(id)
    answers = database_manager.show_answers(id)
    page_title = 'Question ' + str(id)

    if question:

        if userID:

            questionOwner = database_manager.getQuestionOwner(id)

            if userID == questionOwner:

                database_manager.view_counter(question_id=id)

                return render_template('question.html', id=id,question=question,answers=answers,
                                       page_title=page_title, questionAccess=True, logged=True,
                                       userID=userID)

            database_manager.view_counter(question_id=id)

            return render_template('question.html', id=id,question=question, answers=answers,
                               page_title=page_title, logged=True, userID=userID)

        database_manager.view_counter(question_id=id)

        return render_template('question.html', id=id, question=question, answers=answers,
                               page_title=page_title)

    return redirect(url_for('index'))

@app.route('/question/<id>/new-answer', methods=['GET','POST'])
def add_answer(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/list')

    if database_manager.is_id_in_database(id):

        userID = session_controller.session_refresh(session)

        if userID:

            if request.method == 'POST':

                answer_id = database_manager.highest_answer_id()
                timestamp = datetime.now().replace(microsecond=0)
                vote_number = 0
                question_id = id
                message = request.form['message']
                image = None

                values = (answer_id,timestamp,vote_number,question_id,message,image,userID)
                database_manager.add_answer(values)


                return redirect(url_for('question', id=question_id))

            return render_template('new_answer.html', id=id)

        else:
            return redirect(url_for('login'))

    return redirect(url_for('index'))

@app.route('/answer/<id>', methods=['GET','POST'])
def answer(id):

    page_title = 'Answer ' + str(id)
    index = {'ANSWER_ID':0,'TIMESTAMP':1,'VOTE':2,'QUESTION_ID':3,'MESSAGE':4,'IMAGE':5,'USER_ID':6}

    try:
        id = int(id)
    except ValueError:
        return redirect('/')

    answer = database_manager.show_answer_by_id(id)

    if answer:

        userID = session_controller.session_refresh(session)

        if userID:

            answerOwner = database_manager.getAnswerOwner(id)

            if userID == answerOwner:

                return render_template('answer.html', id=id, answer=answer, page_title=page_title,
                                        index=index,logged=True,answerAccess=True)

            return render_template('answer.html',id=id,answer=answer,page_title=page_title,
                                    index=index,logged=True)


        return render_template('answer.html',id=id, answer=answer, page_title=page_title, index=index)

    return redirect('/list')

@app.route('/question/<id>/delete', methods=['GET','POST'])
def delete_question(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/list')

    if database_manager.is_id_in_database(id):

        userID = session_controller.session_refresh(session)
        questionOwner = database_manager.getQuestionOwner(id)

        if userID == questionOwner:

            if request.method == 'POST':

                database_manager.delete_record_from_question(id)

                return redirect('/list')

            return render_template('delete_question.html', id=id)

    return redirect(url_for('list'))

@app.route('/question/<id>/vote', methods=['GET','POST'])
def vote(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/list')

    if database_manager.is_id_in_database(id=id):

        userID = session_controller.session_refresh(session)

        if userID:

            if request.method == 'POST':

                if request.form['button'] == 'up':

                    database_manager.vote_up(question_id=id)
                    return redirect (url_for('question',id=id))

                elif request.form['button'] == 'down':

                    database_manager.vote_down(question_id=id)
                    return redirect(url_for('question',id=id))

            return render_template('vote.html', id=id)

    return redirect('/')

@app.route('/answer/<id>/vote', methods=['GET','POST'])
def vote_answer(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/')

    answer = database_manager.show_answer_by_id(id)
    page_title = 'Vote Answer ' + str(id)
    userID = session_controller.session_refresh(session)

    if answer:
        if userID:
            if request.method == 'POST':
                if request.form['button'] == 'up':
                    database_manager.answer_vote_up(id)
                    return redirect(url_for('answer', id=id))
                else:
                    database_manager.answer_vote_down(id)
                    return redirect(url_for('answer', id=id))

            return render_template('vote_answer.html', id=id, page_title=page_title)

    return redirect('/')

@app.route('/answer/<id>/delete', methods=['GET','POST'])
def delete_answer(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/')

    answer = database_manager.show_answer_by_id(id)

    if answer:

        userID = session_controller.session_refresh(session)
        answerOwner = database_manager.getAnswerOwner(id)

        if userID == answerOwner:

            if request.method == 'POST':
                database_manager.delete_answer(id)
                return redirect('/list')

            return render_template('delete_answer.html', id=id)

    return redirect('/')

@app.route('/answer/<id>/edit', methods=['GET','POST'])
def edit_answer(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/')

    answer = database_manager.show_answer_by_id(id)

    if answer:

        answer=answer[0]

        if request.method == 'POST':
            if request.form['message']:
                database_manager.edit_answer(id,request.form['message'])
                return redirect(url_for('answer', id=id))

        return render_template('edit_answer.html', id=id, answer=answer)

    return redirect('/')

@app.route('/registration', methods=['GET','POST'])
def register():

    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':

        email = request.form['email']
        username = request.form['username']
        user_id = database_manager.highest_user_id()
        password = hashing_utility.hash_password(request.form['password'])

        if not database_manager.is_user_in_db(username,email):

            values = (user_id,email,username,password)
            database_manager.add_user(values)

            return redirect(url_for('index'))

        else:

            return render_template('registration.html', page_title = 'AskMate - Register', exist='Username or email already exist, try again')

    return render_template('registration.html', page_title = 'AskMate - Register')

@app.route('/login', methods=['GET','POST'])
def login():

    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':

        username = request.form['username']

        if database_manager.is_user_in_db(username,username):

            password = request.form['password']
            hashedPassword = database_manager.grab_password_from_db(username)

            if hashing_utility.verify_password(password,hashedPassword):

                session.permanent = True
                session['username'] = username

                return redirect(url_for('index'))

        return render_template('login.html', error='Wrong username or password')

    return render_template('login.html', page_title = 'AskMate - Login')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/users_list', methods=['GET','POST'])
def users_list():

    usersList = database_manager.getUsersList()
    titles = ['ID','Email', 'Username']

    return render_template('users_list.html', page_title = 'AskMate - Users List', usersList = usersList,
                           titles = titles)

@app.route('/user/<id>', methods=['GET','POST'])
def user(id):

    try:
        id = int(id)
    except ValueError:
        return redirect('/')

    USERNAME_INDEX = 2
    userData = database_manager.getUserById(id)
    userName = userData[USERNAME_INDEX]
    userQuestions = database_manager.getUserQuestions(id)
    userAnswers = database_manager.getUserAnswers(id)
    page_title = 'AskMate - User ' + str(id)
    questionTitles = ['ID','Title','Message','Submission Time','Views','Rating']
    answerTitles = ['ID','Message','Submission Time','Rating']


    if userData:

        return render_template('user.html', userName=userName, userQuestions=userQuestions,
                               page_title = page_title, questionTitles=questionTitles,
                               userAnswers=userAnswers,answerTitles=answerTitles)

    return redirect('/')

if __name__ == "__main__":
    app.run(
        debug=False, # Allow verbose error reports
        port=5000 # Set custom port
    )