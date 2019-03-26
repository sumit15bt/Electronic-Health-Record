#from data import Articles
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging,make_response
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import pandas as pa
from model import InputForm
from compute import compute
import random
import string
import urllib.parse
import urllib.request

from sklearn.neighbors import KNeighborsClassifier


app=Flask(__name__)
app._static_folder ='static/'


# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'EHR'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Articles=Articles()


@app.route('/', methods=['GET', 'POST'])
def index():
    # breast-cancer prediction
    formbreastcancer = InputForm(request.form)
    if request.method == 'POST' and formbreastcancer.validate():
        result = compute(formbreastcancer.a.data, formbreastcancer.b.data,formbreastcancer.c.data, formbreastcancer.d.data,formbreastcancer.e.data,formbreastcancer.z.data,formbreastcancer.g.data,formbreastcancer.h.data,formbreastcancer.i.data)
    else:
        result = None
    return render_template('index2.html', form=formbreastcancer, result=result)






# Register Form Class
class RegisterForm(Form):
    PractisionerNo = StringField('PractisionerNo', [validators.Length(min=5, max=20)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Doctor Registeration
@app.route('/register',methods=['GET','POST'])
def registrationform():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        PractisionerNo = form.PractisionerNo.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO Doctors(PractisionerNo, Username,Email,  Password) VALUES(%s, %s, %s, %s)", (PractisionerNo, username, email,  password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered', 'success')

        return redirect(url_for('login'))
    return render_template('Doctor_registration.html', form=form)


# Doctor login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Doctors WHERE Username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    # Show articles only from the user logged in
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Article Form Class
class PatienRecords(Form):
    AadharNo = StringField('Aadhar No', [validators.regexp(u'^(\d{12}|\d{16})$')])
    name = StringField('name', [validators.Length(min=1, max=100)])
    DoctorName = StringField('Doctor Name', [validators.Length(min=1, max=30)])
    DocPracNo = StringField('Doctor Practionar No', [validators.Length(min=1, max=20)])
    visitNo = StringField('visit No', [validators.Length(min=1, max=10)])
    suffering = StringField('Suffering from Disease', [validators.Length(min=1, max=100)])
    DiseaseDescription= TextAreaField('Disease Description' )
    medication= TextAreaField('Treatment & Medications')
    tests= TextAreaField('Tests',)
    results= TextAreaField('Results')

# Add Patient Records
@app.route('/add_record', methods=['GET', 'POST'])
@is_logged_in
def add_record():
    form = PatienRecords(request.form)

    if request.method == 'POST' and form.validate():
        AadharNo=form.AadharNo.data
        name=form.name.data
        DoctorName=form.DoctorName.data
        DocPracNo=form.DocPracNo.data
        visitNo=form.visitNo.data
        suffering=form.suffering.data
        DiseaseDescription=form.DiseaseDescription.data
        medication=form.medication.data
        tests=form.tests.data
        results=form.results.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        mysqlstatement="INSERT INTO `Report` (`sno`, `AadharNo`, `name`, `DoctorName`, `DocPracNo`, `visitNo`, `suffering`, `Disease Description`, `medication`, `tests`, `results`, `time`) VALUES (NULL, '"+AadharNo+"', '"+name+"', '"+DoctorName+"', '"+DocPracNo+"', '"+visitNo+"', '"+suffering+"', '"+DiseaseDescription+"', '"+medication+"', '"+tests+"', '"+results+"',CURRENT_TIMESTAMP);"
        cur.execute(mysqlstatement)

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Record Submitted', 'success')

        return redirect(url_for('record_search'))

    return render_template('add_records.html', form=form)





# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Edit Article
@app.route('/edit_record/<string:sno>', methods=['GET', 'POST'])
@is_logged_in
def edit_record(sno):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE sno = %s", [sno])

    report = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields

    form.AadharNo.data = report['AadharNo']
    form.name.data = report['name']
    form.DoctorName.data = report['DoctorName']
    form.DocPracNo.data = report['DocPracNo']
    form.visitNo.data = report['visitNo']
    form.suffering.data = report['suffering']
    form.DiseaseDescription.data = report['DiseaseDescription']
    form.medication.data = report['medication']
    form.tests.data = report['tests']
    form.results.data = report['results']



    if request.method == 'POST' and form.validate():


        suffering=form.suffering.data
        DiseaseDescription=form.DiseaseDescription.data
        medication=form.medication.data
        tests=form.tests.data
        results=form.results.data


        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)








# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

# articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    # Show all articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()




# full article view
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    # Show  article with particular id
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])

    article = cur.fetchone()
    return render_template("article.html",article=article)

#about
@app.route('/about')
def aboutProject():
    return render_template("about.html")


def rand_pass(size):
        # Takes random choices from
	# ascii_letters and digits
	generate_pass = ''.join([random.choice( string.ascii_uppercase +
		                            string.ascii_lowercase +
		                            string.digits)
		                            for n in range(size)])
	return generate_pass

@app.route('/record_search',methods=['GET', 'POST'])
@is_logged_in
def record_search():
    if request.method == 'POST':
        aadharNo=request.form['aadharsearch']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT mobileno FROM Patient where AadharNo="+aadharNo)
        mobileno = cur.fetchone()
        cur.close()

        if mobileno:
            otpgenerated = rand_pass(5)
            print(otpgenerated)
            authkey = "267368ANbjR9YCbb85c89f6b7" # Your authentication key.

            mobiles = str(mobileno['mobileno']) # Multiple mobiles numbers separated by comma.

            message = "Your OTP  is  {}".format(otpgenerated) # Your message to send.

            sender = "SMSIND" # Sender ID, While using route4 sender id should be 6 characters long.

            route = "4" # Define route

            # Prepare you post parameters
            values = {
            'authkey' : authkey,
            'mobiles' : mobiles,
            'message' : message,
            'sender' : sender,
            'route' : route
            }


            '''url = "http://api.msg91.com/api/sendhttp.php" # API URL

            postdata = urllib.parse.urlencode(values).encode('utf-8') # URL encoding the data here.

            req = urllib.request.Request(url, postdata)

            response = urllib.request.urlopen(req)

            output = response.read() # Get Response

            print(output) # Print Response'''



            return render_template("record_search.html",mobileNo=mobileno['mobileno'],aadharNo=aadharNo,otpgenerated=otpgenerated)
        else:
            flash('Some Error ,Enter correct Aadhar Number', 'danger')
            return render_template("record_search.html")
    return render_template("record_search.html")





@app.route('/records',methods=['GET', 'POST'])
@is_logged_in
def records():

    try:
        if request.method == 'POST':
            aadharNo=request.form['aadharNo']
            otpgenerated=request.form['otpgenerated']
            otpEntered=request.form['otpEntered']
            if otpEntered!=otpgenerated:
                flash('Some Error,OTP mismatched..!!', 'danger')
                return render_template("record_search.html")
            else:
                cur = mysql.connection.cursor()
                result = cur.execute("SELECT sno,AadharNo,name,DoctorName,DocPracNo,visitNo,suffering,medication,tests,results,time  FROM Report where AadharNo="+aadharNo)
                AllReports = cur.fetchall()
                cur.close()
                return render_template("records.html",AllReports=AllReports)
    except:
        flash('Some Error,OTP mismatched..!!', 'danger')
        return render_template("record_search.html")

'''import pdfkit
@app.route('/ReportPdf')
def ReportPdf():
    rendered=render_template('index2.html')
    css=['static/css/bootstrap/bootstrap.min.css']
    pdf=pdfkit.from_string(rendered,False,css=css)
    response=make_response(pdf)
    response.headers['Content-type']='application/pdf'
    response.headers['Content-Disposition']='attachment;filename=output.pdf'
    return response'''


@app.route('/cancer', methods=['GET', 'POST'])
def cancer():
    if request.method == 'POST':
        age=float(request.form['age'])
        gender=float(request.form['gender'])
        air=float(request.form['values'])
        alch=float(request.form['values1'])
        dust=float(request.form['values2'])
        occp=float(request.form['values3'])
        gene=float(request.form['values4'])
        ldesc=float(request.form['values5'])
        diet=float(request.form['values6'])
        obsty=float(request.form['values7'])
        smoke=float(request.form['values8'])
        psmoke=float(request.form['values9'])
        chest=float(request.form['values10'])
        cough=float(request.form['values11'])
        fatig=float(request.form['values12'])
        weight=float(request.form['values13'])
        breath=float(request.form['values14'])
        wheez=float(request.form['values15'])
        swallow=float(request.form['values16'])
        nails=float(request.form['values17'])
        cold=float(request.form['values18'])
        dcough=float(request.form['values19'])
        snore=float(request.form['values20'])
        data=pa.read_excel("cancer_patient_data_sets .xlsx").values

        train_data=data[0:998,1:24]
        train_target=data[0:998,24]


        clf2=KNeighborsClassifier(n_neighbors=3)
        trained2=clf2.fit(train_data,train_target)

        test=[age,gender,air,alch,dust,occp,gene,ldesc,diet,obsty,smoke,psmoke,chest,cough,fatig,weight,breath,wheez,swallow,nails,cold,dcough,snore]
        #test=[34,1,2,3,4,5,6,7,6,5,4,3,2,1,2,3,4,5,2,3,5,2,3]

        predicted=trained2.predict([test])
    
        return render_template("cancer.html",predicted=predicted)
    else:
        return render_template('cancer.html')


@app.route('/bcancer', methods=['GET', 'POST'])
def b_cancer():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        result = compute(form.a.data, form.b.data,form.c.data, form.d.data,form.e.data,form.z.data,form.g.data,form.h.data,form.i.data)
    else:
        result = None
    return render_template('BC_cancer.html', form=form, result=result)

@app.route('/preventivemeasures/')
def preventivemeasures():
    return render_template('preventivemeasures.html')


@app.route('/homealone')
def home():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    # Show all articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('home.html', articles=articles)
    else:
        about_msg = 'No Articles Found'
        return render_template('home.html', about_msg=about_msg)
    # Close connection
    cur.close()



if __name__ == "__main__":
    app.secret_key='sumit123secret'
    app.run(debug=True)
