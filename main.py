from  flask import Flask, render_template, request, redirect, flash, session, send_file
import engine_class
from flask_session import Session
from os import urandom
import traceback
import io


'''config = {
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}'''

app = Flask(__name__)


app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

api_hash = "YOUR API ID"
api_id = "YOUR API HASH"

class config_value:
    def __init__(self, _client=None, _phoneNumber="", _sessionCode=None):
        self.client = _client
        self.phoneNumber = _phoneNumber
        self.sessionCode = _sessionCode
    
    def config_values(self, _client, _phoneNumber, _sessionCode):
        self.client = _client
        self.phoneNumber = _phoneNumber
        self.sessionCode = _sessionCode
    
    def config_files(self, data):
        self.files = data

config = config_value()


def _config_connection():
    sessionValue = session.get("name")
    
    if not sessionValue or "#" not in sessionValue:
        return "/"
    else:
        phoneNumber, sessionCode = sessionValue.split("#")[0], sessionValue.split("#")[1]
        
    try:
        if not config.client or not config.client.is_user_connected():
            client = engine_class.Telegram(phoneNumber, sessionCode, api_id, api_hash)
            config.config_values(client, phoneNumber, sessionCode)
    except ConnectionError:
        print("connection error")
        return None
    except Exception:
        print(traceback.print_exc())
        return "/cloud/logout"
    return None

    
@app.route("/", methods=('GET', 'POST'))
def login():

    sessionCode = session.get("name")

    if not sessionCode:
        sessionCode = str(urandom(10).hex())
        session["name"] = sessionCode
    elif "#" in sessionCode:
        return redirect("/cloud")

    phoneValid = False
    if request.method == 'POST':

        config.phoneNumber = request.form['phoneNumber']

        if not config.phoneNumber:
            flash('Phone Number is required!')
        else:
            try:
                if int(config.phoneNumber) and config.phoneNumber.startswith('+') and len(config.phoneNumber) > 11:
                    
                    client = engine_class.Telegram(phoneNumber=config.phoneNumber, sessionCode=sessionCode, api_id=api_id, api_hash=api_hash)
                    otp_response = client.send_code()
                    if otp_response == "true":
                        phoneValid = True
                    else:
                        flash(otp_response)
                else:
                    if len(config.phoneNumber) == 10:
                        config.phoneNumber = "+91" + config.phoneNumber
                        
                        client = engine_class.Telegram(phoneNumber=config.phoneNumber, sessionCode=sessionCode, api_id=api_id, api_hash=api_hash)
                        otp_response = client.send_code()
                        if otp_response == "true":
                            phoneValid = True
                        else:
                            flash(otp_response)
                    else:
                        flash("Phone Number is Invalid!") 
            except Exception as e:
                print(traceback.print_exc())
                flash(str(e))

    if not phoneValid:
        return render_template("login.html", phoneNumber=config.phoneNumber)
    else:
        config.config_values(client, config.phoneNumber, sessionCode)
        return render_template("verify_otp.html", cnCode=config.phoneNumber[:-10], unHiddenDigits=config.phoneNumber[-3:], otp="")

@app.route("/authorize", methods=(["POST"]))
def otp_verify():
    response = False
    if request.method == "POST":
        inputOtp = request.form['inputOtp']
        response = config.client.validiate_code(inputOtp)
        if response == "true":
            session['name'] = config.phoneNumber + "#" + config.sessionCode
        else:
            flash(response)
    if response == "true":
        return redirect("/cloud")
    else:
        return render_template("verify_otp.html", cnCode=config.phoneNumber[:-10], unHiddenDigits=config.phoneNumber[-3:], otp=inputOtp)

#------ refresh route
@app.route("/refresh")
def refresh():
    config.phoneNumber = ""
    return redirect("/")


# --- Logout
@app.route("/cloud/logout", methods=(["GET", "POST"]))
def logout():
    if request.method == "POST" or request.method== "GET":
        if session.get("name"):
            config.client.log_out()
            session["name"] = config.sessionCode
            flash("You were logged out of session!")
  
    return redirect("/")


# ------ about page
@app.route("/about")
def about():
    return render_template("about.html")


# ------cloud
@app.route("/cloud")
def cloud():
    conn = _config_connection()
    if conn:
        return redirect(conn)
    
    try:
        files = config.client.get_saved_files()
    except:
        return redirect("/cloud/logout")
    config.config_files(files)

    return render_template("cloud_page.html", files_data=files)

@app.route("/account/logout")
def get_logout():
    session["name"] = config.sessionCode
    flash("You were logged out of session!")
    return redirect("/")

@app.route("/cloud/delete", methods=(["POST"]))
def delete_file():
    conn = _config_connection()
    if conn:
        return redirect(conn)
    
    file_id = request.form['file_id']
    response = config.client.delete_file(file_id)
    if response != "true":
        flash(response)
    return redirect("/cloud")

@app.route("/cloud/upload", methods=(['POST']))
def upload_file():
    conn = _config_connection()
    if conn:
        return redirect(conn)

    file = request.files['file']
    file.name = file.filename
    config.client.upload_file(file)
    
    return redirect("/cloud")

@app.route("/cloud/download", methods=(['POST']))
def download_file():
    conn = _config_connection()
    if conn:
        return redirect(conn)

    id, filename = request.form["file_data"].split("no11i")[0], request.form["file_data"].split("no11i")[1]

    return send_file(io.BytesIO(config.client.downloadFile(config.files[id][-1])), as_attachment=True, download_name=filename)


if __name__=="__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)