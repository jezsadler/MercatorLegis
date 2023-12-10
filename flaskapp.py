from urllib.error import HTTPError
from flask import Flask, render_template,request,redirect, url_for,flash
from flask_mail import Mail, Message
from skills_layout import generate_gang_quickref
from contact import ContactForm
app = Flask(__name__)
app.secret_key = 'zenith'

mail = Mail()
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'contactymerge@gmail.com'
app.config["MAIL_PASSWORD"] = 'mnbk rwhl mdnl mrzz'
mail.init_app(app)

@app.route("/",methods = ['GET','POST'])
def selector():
    if request.method == 'POST':
        gangpath = request.form['gangpath']
        orientation = request.form['orientation']
        if 'hideunrecognized' in request.form and request.form['hideunrecognized'] == 'on':
            hideunknown = True
        else:
            hideunknown = False
        if 'hideooc' in request.form and request.form['hideooc'] == 'on':
            hideooc = True
        else:
            hideooc = False
        return redirect(url_for("qr_sheet",gangpath=gangpath, orientation=orientation, 
                                hideunknown=hideunknown, hideooc=hideooc))
    return render_template("srqr_selector.html")

@app.route('/contact',methods=['GET','POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('srqr_contact.html', form=form)
        else:
            msg = Message("SRQR Feedback: " + form.subject.data, 
                          sender='contactymerge@gmail.com', 
                          recipients=['jez.sadler@gmail.com'])
            msg.body = """ 
            From: %s <%s> 
            %s """ % (form.name.data, form.email.data, form.message.data)
            mail.send(msg)
            return 'Form posted.'
    elif request.method == 'GET':
        return render_template('srqr_contact.html', form=form)

@app.route("/quickref_sheet.html",methods = ['GET','POST'])
def qr_sheet():
    try:
        gang_name,gang_type,gang_skills,wyrd,specials, \
            weapon_traits,wargear,actions,unknown_rules,ignore_gang \
                = generate_gang_quickref(request.args['gangpath'])
    except (HTTPError, IndexError):
        flash("Could not find a gang with the URL or ID you entered. Please try again.")
        return redirect("/")

    return render_template("srqr_template.html",
                           orient=request.args['orientation'],
                           hide_unknown=request.args['hideunknown'],
                           hide_ooc=request.args['hideooc'],
                           gang_name=gang_name,
                           gang_type=gang_type,
                           gang_skills=gang_skills,
                           wyrd_powers=wyrd,
                           gang_specials=specials,
                           weapon_traits=weapon_traits,
                           wargear=wargear,
                           actions=actions,
                           unknown_rules=unknown_rules,
                           ignore_gang=ignore_gang)