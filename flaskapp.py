from flask import Flask, render_template,request,redirect, url_for,send_file
from skills_layout import generate_gang_quickref
app = Flask(__name__)
import os

@app.route("/",methods = ['GET','POST'])
def selector():
    if request.method == 'POST':
        gangpath = request.form['gangpath']
        return redirect(url_for("qr_sheet",gangpath=gangpath))
    return render_template("srqr_selector.html")

@app.route("/quickref_sheet.html",methods = ['GET','POST'])
def qr_sheet():
    gang_name,gang_type,gang_skills,wyrd,specials,weapon_traits,wargear,unknown_rules = generate_gang_quickref(request.args['gangpath'])
    return render_template("srqr_template.html",
                           gang_name=gang_name,
                           gang_type=gang_type,
                           gang_skills=gang_skills,
                           wyrd_powers=wyrd,
                           gang_specials=specials,
                           weapon_traits=weapon_traits,
                           wargear=wargear,
                           unknown_rules=unknown_rules)