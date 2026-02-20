from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func,or_
from datetime import datetime, timedelta
from flask import Response
import csv
from io import StringIO
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def send_email(to_email, subject, body, html=False):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        # Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print("Error sending email:", e)

def send_email_change_verification(to_email, verification_link):

    subject = "Verify Your New Email Address"

    body = f"""
Hello,

Click the link below to confirm your new email address:

{verification_link}

This link expires in 10 minutes.

If you did not request this change, ignore this email.
"""

    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls(context=context)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        server.quit()
        print("Email verification sent!")

    except Exception as e:
        print("Error sending email:", e)

def send_reset_email(to_email, reset_url):

    subject = "Password Reset Request"

    body = f"""
Hello,

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request this, ignore this email.
"""

    # Create message
    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    # Secure connection
    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls(context=context)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        server.quit()

        flash("Reset email sent successfully!")

    except Exception as e:
        flash(f"Error sending email: {e}")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        return f(*args, **kwargs)

    return decorated_function

UPLOAD_FOLDER = "static/uploads"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
serializer = URLSafeTimedSerializer(app.secret_key)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# ===============================
# MODELS
# ===============================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)   # ✅ NEW
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="citizen")
    is_verified = db.Column(db.Boolean, default=False)
    complaints = db.relationship("Complaint", backref="user", lazy=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    category = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Pending")
    address = db.Column(db.String(300), nullable=False)
    latitude = db.Column(db.String(200),nullable=True)
    longitude = db.Column(db.String(200),nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_resolved = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    feedback = db.Column(db.String(50))
with app.app_context():
    db.create_all()
# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    session.clear()
    return render_template("index.html")


# ===============================
# REGISTER
# ===============================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        phone = request.form.get("phone")
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return redirect(url_for("home", alert="Email already exists"))

        hashed_password = generate_password_hash(password)
        user = User(
            name=name,
            email=email,
            phone=phone,
            password=hashed_password,
            is_verified=True
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("home",alert="Email registered successfully."))

    return render_template("register.html")

# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role
            session["name"] = user.name
            session["email"] = user.email
            session["phone"] = user.phone
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("home",alert="Invalid credentials!"))
    return redirect(url_for("home"))


# ===============================
# ADMIN LOGIN
# ===============================
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=email).first()

        if admin and check_password_hash(admin.password, password):

            session["admin_id"] = admin.id
            session["is_admin"] = True

            flash("Welcome Admin!", "success")
            return redirect(url_for("admin_dashboard"))

        else:
            return redirect(url_for("home",alert="Invalid credentials"))
    return redirect(url_for("home"))



# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))



# ===============================
# CITIZEN DASHBOARD
# ===============================
@app.route("/export-csv")
def export_csv():

    if "user_id" not in session:
        return redirect(url_for("login"))

    complaints = Complaint.query.filter_by(user_id=session["user_id"]).all()

    output = StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        "ID",
        "Title",
        "Category",
        "Address",
        "Status",
        "Date Created",
        "Latitude",
        "Longitude"
    ])

    # CSV Rows
    for c in complaints:
        writer.writerow([
            c.id,
            c.title,
            c.category,
            c.address,
            c.status,
            c.date_created,
            c.latitude,
            c.longitude
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=complaints.csv"}
    )

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session or session["role"] != "citizen":
        return redirect(url_for("home"))

    complaints = Complaint.query.filter_by(user_id=session["user_id"]).all()
    resolved_count = Complaint.query.filter_by(user_id=session["user_id"],status="Resolved").count()
    pending_count = Complaint.query.filter_by(user_id=session["user_id"],status="Pending").count()
    in_progress_count = Complaint.query.filter_by(user_id=session["user_id"],status="In Progress").count()
    return render_template("dashboard.html",complaints=complaints[:3],total_complaints=len(complaints),pending=pending_count,
                           in_progress = in_progress_count,resolved=resolved_count)


# ===============================
# REPORT PAGE
# ===============================
@app.route("/report")
def report():
    return render_template("report.html")


# ===============================
# SUBMIT COMPLAINT
# ===============================
@app.route("/submit-complaint", methods=["POST"])
def submit_complaint():
    if "user_id" not in session:
        return redirect(url_for("home"))

    title = request.form["title"]
    description = request.form["description"]
    location = request.form["address"]
    file = request.files["image"]
    category = request.form["category"]
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    new_complaint = Complaint(
               title=title,
               description=description,
               address=location,
               image=filename,
               user_id=session["user_id"],
               category=category,
               latitude = latitude,
               longitude = longitude
               )

    db.session.add(new_complaint)
    db.session.commit()

    flash("Complaint submitted successfully!", "success")
    return redirect(url_for("dashboard"))

# ===============================
# FEEDBACK
# ===============================
@app.route("/complaint/feedback/<int:id>", methods=["POST"])
def complaint_feedback(id):

    data = request.get_json()
    feedback = data.get("feedback")

    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({"success": False})

    complaint.feedback = feedback  # add this column in model
    db.session.commit()
    complaint_resolved_date = None
    if feedback == "satisfied":
        complaint_resolved_date = complaint.date_resolved.strftime("%d %b %Y")

    return jsonify({
        "success": True,
        "resolved_date": complaint_resolved_date
    })



# ===============================
# MY COMPLAIN PAGE
# ===============================
@app.route("/my_complain")
def my_complain():
    if "user_id" not in session or session["role"] != "citizen":
        return redirect(url_for("home"))

    status = request.args.get("status", "")

    query = Complaint.query.filter_by(user_id=session["user_id"])

    if status:
        query = query.filter(Complaint.status.ilike(status))

    complaints = query.order_by(
        Complaint.date_created.desc()
    ).all()
    return render_template("my_complaints.html",complaints=complaints,selected_status=status)

# ===============================
# ANALYTIC PAGE
# ===============================
@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("home"))

    # Status count
    status_data = db.session.query(
        Complaint.status,
        func.count(Complaint.id)
    ).group_by(Complaint.status).all()

    # Category count
    category_data = db.session.query(
        Complaint.category,  # replace with category column if you have one
        func.count(Complaint.id)
    ).group_by(Complaint.category).all()

    # Weekly complaints (last 7 days)
    last_week = datetime.utcnow() - timedelta(days=7)

    weekly_data = db.session.query(
        func.date(Complaint.date_created),
        func.count(Complaint.id)
    ).filter(
        Complaint.date_created >= last_week
    ).group_by(
        func.date(Complaint.date_created)
    ).all()

    return render_template(
        "analytics.html",
        status_data=status_data,
        category_data=category_data,
        weekly_data=weekly_data
    )

# ===============================
# PROFILE PAGE
# ===============================
@app.route("/profile")
def profile():
    if "user_id" not in session or session["role"] != "citizen":
        return redirect(url_for("home"))
    complaints = Complaint.query.filter_by(user_id=session["user_id"]).all()
    return render_template("profile.html",complaints=len(complaints))

@app.route("/update-profile", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    user.name = request.form.get("name")
    user.phone = request.form.get("phone")

    db.session.commit()

    # Update session values
    session["name"] = user.name
    session["phone"] = user.phone

    flash("Profile updated successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form["email"]

        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt="password-reset")

            reset_url = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            send_reset_email(email, reset_url)

        flash("If this email exists, a reset link has been sent.")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600  # 1 hour expiry
        )
    except:
        flash("Invalid or expired token.")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password updated successfully.")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/change-password", methods=["POST"])
def change_password():

    user = User.query.get(session["user_id"])

    current = request.form.get("current_password")
    new = request.form.get("new_password")

    if not check_password_hash(user.password, current):
        flash("Current password is incorrect", "danger")
        return redirect(url_for("dashboard"))

    user.password = generate_password_hash(new)
    db.session.commit()

    flash("Password updated successfully!", "success")
    return redirect(url_for("dashboard"))

# ===============================
# DELETE ACCOUNT
# ===============================
@app.route("/delete-account")
def delete_account():

    user = User.query.get(session["user_id"])

    # Delete user complaints first
    Complaint.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

    session.clear()

    flash("Account deleted successfully", "success")
    return redirect(url_for("home"))


# ===============================
# UPDATE EMAIL
# ===============================
@app.route("/request-email-change", methods=["POST"])
def request_email_change():

    new_email = request.form.get("email")

    token = serializer.dumps(new_email, salt="email-change")

    verification_link = url_for("verify_email", token=token, _external=True)

    send_email_change_verification(new_email, verification_link)

    flash("Verification link sent to your email.", "info")

    return redirect(url_for("dashboard"))

@app.route("/verify-email/<token>")
def verify_email(token):

    try:
        new_email = serializer.loads(token, salt="email-change", max_age=600)
    except:
        flash("Invalid or expired token", "danger")
        return redirect(url_for("dashboard"))

    user = User.query.get(session["user_id"])
    user.email = new_email
    db.session.commit()

    session["email"] = new_email

    flash("Email updated successfully!", "success")
    return redirect(url_for("dashboard"))

# ===============================
# ADMIN DASHBOARD
# ===============================
@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    total_complaints = Complaint.query.count()
    resolved_count = Complaint.query.filter_by(status="Resolved").count()
    pending_count = Complaint.query.filter_by(status="Pending").count()
    progress = Complaint.query.filter_by(status="In Progress").count()
    user_count = User.query.filter_by(role="citizen").count()

    # ===== Monthly Trends =====
    monthly_data = db.session.query(
        func.strftime("%Y-%m", Complaint.date_created),
        func.count(Complaint.id)
    ).group_by(
        func.strftime("%Y-%m", Complaint.date_created)
    ).all()

    months = []
    counts = []

    for month, count in monthly_data:
        months.append(month)
        counts.append(count)


    return render_template("admin_dashboard.html",total_complaints=total_complaints,resolved_count
                           =resolved_count,pending_count=pending_count,progress=progress,user_count=user_count,  months=months,
        counts=counts)

# ===============================
# ADMIN COMPLAINT
# ===============================
@app.route("/admin_complaints")
@admin_required
def admin_complaints():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    query = Complaint.query

    # 🔎 Search by title or category
    if search:
        query = query.filter(
            or_(
                Complaint.title.ilike(f"%{search}%"),
                Complaint.category.ilike(f"%{search}%")
            )
        )

    # 📌 Filter by status
    if status_filter and status_filter != "All":
        query = query.filter_by(status=status_filter)

    complaints = query.order_by(
        Complaint.date_created.desc()
    ).paginate(page=page, per_page=10)

    return render_template(
        "admin_complaints.html",
        complaints=complaints,
        search=search,
        status_filter=status_filter
    )

# ===============================
# RESOLVE COMPLAINT STATUS (ADMIN)
# ===============================
@app.route("/admin/complaint/resolve/<int:id>")
@admin_required
def resolve_complaint(id):

    page = request.args.get("page", 1, type=int)

    complaint = Complaint.query.get_or_404(id)
    complaint.status = "Resolved"
    complaint.date_resolved = datetime.utcnow()
    db.session.commit()

    return redirect(url_for("admin_complaints", page=page))

@app.route("/admin/update-status/<int:id>", methods=["POST"])
@admin_required
def update_status(id):

    data = request.get_json()
    status = data.get("status")

    complaint = Complaint.query.get_or_404(id)
    complaint.status = status
    if status.lower() == "resolved":
        complaint.date_resolved = datetime.utcnow()
    db.session.commit()

    return {"success": True}


# ===============================
# ANALYTIC PAGE(ADMIN)
# ===============================
@app.route("/admin_analytics")
@admin_required
def admin_analytics():
    # 1️⃣ Complaints Over Time (Monthly)
    monthly_data = db.session.query(
        func.strftime("%Y-%m", Complaint.date_created),
        func.count(Complaint.id)
    ).group_by(
        func.strftime("%Y-%m", Complaint.date_created)
    ).all()

    months = [row[0] for row in monthly_data]
    monthly_counts = [row[1] for row in monthly_data]


    # 2️⃣ Category Distribution
    category_data = db.session.query(
        Complaint.category,
        func.count(Complaint.id)
    ).group_by(Complaint.category).all()

    categories = [row[0] for row in category_data]
    category_counts = [row[1] for row in category_data]


    # 3️⃣ Resolution Time (Average Days)
    resolved = Complaint.query.filter_by(status="Resolved").all()
    resolution_days = []

    for c in resolved:
        if c.date_resolved:
            delta = (c.date_resolved - c.date_created).days
            resolution_days.append(delta)

    avg_resolution = round(sum(resolution_days)/len(resolution_days), 2) if resolution_days else 0


    # 4️⃣ User Activity (Complaints per user)
    user_data = db.session.query(
        User.name,
        func.count(Complaint.id)
    ).join(Complaint).group_by(User.id).all()

    users = [row[0] for row in user_data]
    user_counts = [row[1] for row in user_data]

    return render_template("admin_analytics.html",months=months,
        monthly_counts=monthly_counts,
        categories=categories,
        category_counts=category_counts,
        avg_resolution=avg_resolution,
        users=users,
        user_counts=user_counts)

# ===============================
# ADMIN FEATURES(REPORTS)
# ===============================
@app.route("/admin_reports")
@admin_required
def admin_reports():
    return render_template("admin_reports.html")

@app.route("/admin/report/monthly")
@admin_required
def monthly_report():

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Month", "Total Complaints"])

    data = db.session.query(
        func.strftime("%Y-%m", Complaint.date_created),
        func.count(Complaint.id)
    ).group_by(
        func.strftime("%Y-%m", Complaint.date_created)
    ).all()

    for row in data:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=monthly_report.csv"}
    )

@app.route("/admin/report/performance")
@admin_required
def performance_report():

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Status", "Total"])

    data = db.session.query(
        Complaint.status,
        func.count(Complaint.id)
    ).group_by(Complaint.status).all()

    for row in data:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=performance_report.csv"}
    )

@app.route("/admin/report/users")
@admin_required
def user_report():

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["User Name", "Email", "Total Complaints"])

    data = db.session.query(
        User.name,
        User.email,
        func.count(Complaint.id)
    ).join(Complaint).group_by(User.id).all()

    for row in data:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=user_report.csv"}
    )

@app.route("/admin/report/category")
@admin_required
def category_report():

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Category", "Total Complaints"])

    data = db.session.query(
        Complaint.category,
        func.count(Complaint.id)
    ).group_by(Complaint.category).all()

    for row in data:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=category_report.csv"}
    )

# ===============================
# ADMIN LOGOUT
# ===============================
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("is_admin", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("home"))

# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":

    app.run()









