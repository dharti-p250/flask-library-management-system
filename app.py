from flask import Flask, render_template, request, redirect, session, flash
from db import get_db

app = Flask(__name__)

app.secret_key = "library-management-secret-key"


# ---------------- HOME ----------------

@app.route("/")
def home():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("home.html", books=books)


# ---------------- SIGN UP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            db.close()

            return render_template(
                "signup.html",
                error="Email already registered"
            )

        cursor.execute(
            """
            INSERT INTO users(name, email, password)
            VALUES(%s, %s, %s)
            """,
            (name, email, password)
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect("/signin")

    return render_template("signup.html")


# ---------------- SIGN IN ----------------

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s AND password=%s
            """,
            (email, password)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/")

        return render_template(
            "signin.html",
            error="Invalid email or password"
        )

    return render_template("signin.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- BOOKS ----------------

@app.route("/books")
def books():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "books.html",
        books=books
    )


# ---------------- SEARCH ----------------

@app.route("/search")
def search():

    keyword = request.args.get("keyword", "")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT * FROM books
        WHERE title LIKE %s
        OR author LIKE %s
        """,
        (
            "%" + keyword + "%",
            "%" + keyword + "%"
        )
    )

    books = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "books.html",
        books=books,
        keyword=keyword
    )


# ---------------- RESERVE BOOK ----------------

@app.route("/reserve/<int:book_id>")
def reserve(book_id):

    if "user_id" not in session:
        return redirect("/signin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM books WHERE id=%s",
        (book_id,)
    )

    book = cursor.fetchone()

    if not book:
        cursor.close()
        db.close()
        return "Book not found"

    if book["available"] <= 0:
        cursor.close()
        db.close()
        return "Book is not available"

    cursor.execute(
        """
        INSERT INTO reservations(user_id, book_id)
        VALUES(%s, %s)
        """,
        (session["user_id"], book_id)
    )

    cursor.execute(
        """
        UPDATE books
        SET available = available - 1
        WHERE id=%s
        """,
        (book_id,)
    )

    db.commit()

    cursor.close()
    db.close()

    flash("Book reserved successfully!")

    return redirect("/books")


# ---------------- PROFILE ----------------

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/signin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT books.*, reservations.reserved_at
        FROM reservations
        JOIN books
        ON reservations.book_id = books.id
        WHERE reservations.user_id=%s
        """,
        (session["user_id"],)
    )

    reservations = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "profile.html",
        user=user,
        reservations=reservations
    )


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/signin", methods=["GET", "POST"])
def admin_signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if email == "admin@gmail.com" and password == "admin123":

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin/signin.html",
            error="Invalid admin credentials"
        )

    return render_template("admin/signin.html")


# ---------------- ADMIN HOME ----------------

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin/signin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM books")
    total_books = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cursor.fetchone()["total"]

    cursor.close()
    db.close()

    return render_template(
        "admin/home.html",
        total_books=total_books,
        total_users=total_users
    )


# ---------------- ADMIN BOOKS ----------------

@app.route("/admin/books")
def admin_books():

    if not session.get("admin"):
        return redirect("/admin/signin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "admin/books.html",
        books=books
    )


# ---------------- ADD BOOK ----------------

@app.route("/admin/books/add", methods=["GET", "POST"])
def add_book():

    if not session.get("admin"):
        return redirect("/admin/signin")

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        category = request.form["category"]
        quantity = int(request.form["quantity"])

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO books
            (title, author, category, quantity, available)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (
                title,
                author,
                category,
                quantity,
                quantity
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect("/admin/books")

    return render_template("admin/books.html", add=True)


# ---------------- DELETE BOOK ----------------

@app.route("/admin/books/delete/<int:book_id>")
def delete_book(book_id):

    if not session.get("admin"):
        return redirect("/admin/signin")

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM books WHERE id=%s",
        (book_id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect("/admin/books")


# ---------------- ADMIN LOGOUT ----------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin/signin")


if __name__ == "__main__":
    app.run(debug=True)