# wall 
from flask import Flask, render_template, redirect, request, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
app = Flask(__name__)
app.secret_key = "spaghetti"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
mysql = connectToMySQL('simple_wall')
bcrypt = Bcrypt(app)

# begin routes
@app.route('/')
def main():
    # print('this is session',session)
    return render_template('index.html')

@app.route('/process', methods=['POST','GET'])
def processUser():
    session.clear()
    # print(request.form)
    error= False
    session['email'] = request.form['email']
    # print("this is the session email",session['email'])
    # print("these emails already exist",email_exist)

    if request.form['reg'] == "new_user":
        session['name'] = request.form['first']
        email_exist = mysql.query_db('select email from users;')

        # print("these emails already exist",email_exist)

        if len(request.form['first']) < 1:
            error = True
            flash("First Name CANNOT be empty")

        if len(request.form['last']) < 1:
            error = True
            flash("Last Name CANNOT be empty")

        if len(request.form['email']) < 1:
            error = True
            flash("Email CANNOT be empty!")

        elif not EMAIL_REGEX.match(request.form['email']):
            error = True
            flash("Invalid email!")

        for i in email_exist:
            if request.form['email'] == i['email']:
                error = True
                flash("The email address you chose is already in use by another user. Please choose another email address.")

        if request.form['pass1'] != request.form['pass2']:
            error = True
            flash('Your passwords do not match. Please fix them')

        if len(request.form['pass1']) < 1:
            error = True
            flash('Password must be AT LEAST 6 characters')

        if error == True:
            return redirect('/')

        pw_hash = bcrypt.generate_password_hash(request.form['pass1'])  
        # print(pw_hash)

        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s);"
        data = {
             'first_name': request.form['first'],
             'last_name':  request.form['last'],
             'email': request.form['email'],
             'password': pw_hash
           }
        mysql.query_db(query, data)

    if request.form['reg'] == "login":
        if not EMAIL_REGEX.match(request.form['email']):
            error = True
            flash("Invalid Login email!")
            return redirect('/')
            
        # session['email'] = request.form['email']

        query = "select * from users where email =%(email)s;"
        data = {
            'email': request.form['email']
        }
        getback = mysql.query_db(query,data)
        # print("GET BACK!",getback)

        if len(getback) == 0:
            error = True
            flash("User name not found")
            return redirect('/')

        email = request.form['email']
        password = request.form['password']

        session['name']=getback[0]['first_name']
        session['userid']=getback[0]['id_users']
        # print(session['name'])
        # print(getback[0]['password'])
        db_email = getback[0]['email']
        # print(db_email)
        db_password = getback[0]['password']
        # print(db_password)

        if email != getback[0]['email']:
            error = True
            flash("Username not found")

        if not bcrypt.check_password_hash(db_password,password):
            error= True
            flash("Email and password do not match. Invalid Login Credentials")

        if len(request.form['email']) < 1:
            error = True
            flash("Email and/or Password CANNOT be empty!")

        if len(request.form['password']) < 1:
            error = True
            flash("Email and/or Password CANNOT be empty!")

        if error == True:
            return redirect('/')

    return redirect('/welcome')

@app.route('/welcome')
def welcome():
    query = "select * from users where email =%(email)s;"
    data = {
        'email': session['email']
    }
    getback = mysql.query_db(query,data)
    session['userid']=getback[0]['id_users']

    ppl = session['name']
    return render_template('success.html', x=ppl)

@app.route('/welcome/wall/', methods=['GET'])
def wall():
    queryMsg = "select * from messages where id_users = %(ID)s"
    dataMsg = {
        'ID': session['userid']
    }
    inbox = mysql.query_db(queryMsg,dataMsg)
    # print('INBOX',inbox)

    queryUsers = "select * from users where email != %(email)s;"
    dataUsers = {
        'email': session['email']
    }
    AllUsersNotYou = mysql.query_db(queryUsers,dataUsers)
    # print("!!!",AllUsersNotYou)

    queryMcount = "select count(id_messages)n from messages where id_users = %(ID)s"
    dataMcount = {
        'ID': session['userid']
    }
    msgCount = mysql.query_db(queryMcount,dataMcount)
    print(msgCount)


    if msgCount[0]['n'] == 1:
        noun = "Message"
    else:
        noun = "Messages"


    qrySendCount = "select count(id_users)n from messages where id_users = %(ID)s"
    dataSendCount = {
        'ID': session['userid']
    }
    outbox = mysql.query_db(qrySendCount,dataSendCount)


    return render_template('wall.html', users=AllUsersNotYou, inbox=inbox, name=session['name'], msgCount=msgCount[0]['n'], noun=noun, outbox=outbox[0]['n'])

@app.route('/send', methods=['POST'])
def sendMsg():
    # print("HEYHEYHEY",request.form['msg_to'])

    query = "INSERT INTO messages (message, created_at, id_users) VALUES (%(message)s, NOW(), %(id_users)s);"
    data = {
        'message': request.form['kite'],
        'id_users': request.form['msg_to']
    }
    mysql.query_db(query, data)

    return redirect('welcome/wall')

@app.route('/delete', methods=['POST'])
def deleteMsg():
    queryMsg = "select * from messages where id_users = %(ID)s"
    dataMsg = {
        'ID': session['userid']
    }
    inbox = mysql.query_db(queryMsg,dataMsg)
    # print('INBOX',inbox)
    # print("MESSAGE TO BE DELETED",request.form['delete'])

    queryDel = "delete from messages where id_messages = %(msgid)s"
    dataDel = {
        'msgid': request.form['delete']
    }
    mysql.query_db(queryDel,dataDel)

    return redirect('welcome/wall')

@app.route('/reset', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')
# end routes
app.run(debug=True)