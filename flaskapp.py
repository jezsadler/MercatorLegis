from urllib.error import HTTPError
from flask import Flask, render_template,request,redirect, url_for,flash
from flask_mail import Mail, Message
from skills_layout import generate_gang_quickref
from contact import ContactForm
app = Flask(__name__)
app.secret_key = 'zenith'

with open('static/email.config') as emailfile:
    mail_config = {s.split(',')[0]:s.split(',')[1].strip()
                   for s in emailfile.readlines()}
mail = Mail()
app.config["MAIL_SERVER"] = mail_config['mail_server']
app.config["MAIL_PORT"] = int(mail_config['mail_port'])
app.config["MAIL_USE_SSL"] = bool(mail_config['mail_use_ssl'])
app.config["MAIL_USERNAME"] = mail_config['mail_username']
app.config["MAIL_PASSWORD"] = mail_config['mail_password']
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
        if form.validate_on_submit():
            msg = Message("SRQR Feedback: " + form.subject.data, 
                          sender=form.email.data, 
                          recipients=[mail_config['mail_recipient']])
            msg.body = """ 
            From: %s <%s> 
            %s """ % (form.name.data, form.email.data, form.message.data)
            redirect('/')
            mail.send(msg)
            flash('Message sent.')
            return redirect('/')
    elif request.method == 'GET':
        return render_template('srqr_contact.html', form=form)

@app.route("/quickref_sheet.html",methods = ['GET','POST'])
def qr_sheet():
    try:
        gang_name,gang_type,gang_skills,wyrd,specials, \
            weapon_traits,wargear,actions,conditions,unknown_rules,ignore_gang \
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
                           conditions=conditions,
                           unknown_rules=unknown_rules,
                           ignore_gang=ignore_gang)