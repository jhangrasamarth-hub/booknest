import os, random, textwrap
from decimal import Decimal
from functools import wraps
import mysql.connector
from markupsafe import escape
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "booknest-dev-key")
DB = dict(host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"),
          password=os.getenv("DB_PASSWORD", ""), database=os.getenv("DB_NAME", "booknest"))
TAX = Decimal("0.05")
BOOK_SQL = "SELECT b.*, c.name AS category FROM books b JOIN categories c ON c.id=b.category_id "

def db(): return mysql.connector.connect(**DB)

def q(sql, args=(), one=False):
    c = db(); cur = c.cursor(dictionary=True); cur.execute(sql, args)
    r = cur.fetchone() if one else cur.fetchall(); c.close(); return r

def run(sql, args=()):
    c = db(); cur = c.cursor(); cur.execute(sql, args); c.commit(); c.close()

def ensure_users():
    for u, p, r in (("Samarth", "admin123", "admin"), ("staff", "staff123", "staff")):
        if not q("SELECT id FROM users WHERE username=%s", (u,), one=True):
            run("INSERT INTO users(username,password,role) VALUES(%s,%s,%s)", (u, generate_password_hash(p), r))

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if session.get("role") not in roles:
                flash("Please sign in with a staff account."); return redirect(url_for("login"))
            return f(*a, **k)
        return w
    return deco

def cart_items():
    cart = session.get("cart", {})
    if not cart: return [], Decimal(0)
    ids = [int(i) for i in cart]
    rows = q(BOOK_SQL + "WHERE b.id IN (%s)" % ",".join(["%s"] * len(ids)), ids)
    items = [dict(book=b, qty=min(cart[str(b["id"])], b["stock"]), amt=b["price"] * min(cart[str(b["id"])], b["stock"])) for b in rows]
    return items, sum((i["amt"] for i in items), Decimal(0))

@app.context_processor
def inject():
    return dict(cart_count=sum(session.get("cart", {}).values()), role=session.get("role"))

# ---------- procedurally generated SVG book covers (no image files needed) ----------
PALETTES = [("#0f3d3e", "#f2c14e", "#e8ddc5"), ("#7a1f2b", "#f4d58d", "#fff3dd"), ("#1d2d50", "#ff9f68", "#f5e6ca"),
            ("#2d4a22", "#e9c46a", "#f1f7e8"), ("#3b2a50", "#f7a8b8", "#f6eaff"), ("#b5502d", "#ffe8b0", "#fff6e6"),
            ("#13293d", "#4fd1c5", "#e7f6f4"), ("#4a3f35", "#d4a373", "#faedcd")]

@app.route("/cover/<int:bid>.svg")
def cover(bid):
    b = q("SELECT title,author FROM books WHERE id=%s", (bid,), one=True)
    if not b: return Response(status=404)
    rnd = random.Random(bid * 97); bg, ac, tx = PALETTES[bid % len(PALETTES)]; shapes = ""
    for _ in range(7):
        k = rnd.choice(("circle", "rect", "ring"))
        x, y, s, o = rnd.randint(0, 300), rnd.randint(0, 260), rnd.randint(40, 150), rnd.choice((.12, .2, .3))
        if k == "circle": shapes += f'<circle cx="{x}" cy="{y}" r="{s//2}" fill="{ac}" opacity="{o}"/>'
        elif k == "ring": shapes += f'<circle cx="{x}" cy="{y}" r="{s//2}" fill="none" stroke="{tx}" stroke-width="3" opacity="{o+.1}"/>'
        else: shapes += f'<rect x="{x}" y="{y}" width="{s}" height="{s//3}" fill="{tx}" opacity="{o}" transform="rotate({rnd.randint(-40,40)} {x} {y})"/>'
    lines = textwrap.wrap(str(b["title"]), 14)[:4]
    t = "".join(f'<text x="30" y="{150+i*34}" font-family="Georgia,serif" font-size="29" font-weight="700" fill="{tx}">{escape(l)}</text>' for i, l in enumerate(lines))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 440"><rect width="300" height="440" fill="{bg}"/>'
           f'<clipPath id="c"><rect width="300" height="440"/></clipPath><g clip-path="url(#c)">{shapes}</g>'
           f'<rect x="30" y="100" width="48" height="5" fill="{ac}"/>{t}'
           f'<text x="30" y="404" font-family="Helvetica,sans-serif" font-size="15" letter-spacing="3" fill="{ac}">{escape(str(b["author"]).upper())}</text>'
           f'<rect width="14" height="440" fill="#000" opacity=".22"/></svg>')
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "max-age=86400"})

# ---------- storefront ----------
@app.route("/")
def home():
    s = q("SELECT COUNT(*) n, COALESCE(SUM(stock),0) c FROM books", one=True)
    return render_template("index.html", stats=s, featured=q(BOOK_SQL + "ORDER BY b.rating DESC, b.id LIMIT 8"),
        hero=q(BOOK_SQL + "ORDER BY b.rating DESC LIMIT 3"),
        cats=q("SELECT c.*, COUNT(b.id) n, MIN(b.id) cover FROM categories c LEFT JOIN books b ON b.category_id=c.id GROUP BY c.id"))

@app.route("/books")
def books():
    term, cat, sort = request.args.get("q", "").strip(), request.args.get("cat", ""), request.args.get("sort", "")
    sql, args = BOOK_SQL + "WHERE (b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s)", [f"%{term}%"] * 3
    if cat.isdigit(): sql += " AND b.category_id=%s"; args.append(int(cat))
    sql += {"low": " ORDER BY b.price", "high": " ORDER BY b.price DESC", "rated": " ORDER BY b.rating DESC"}.get(sort, " ORDER BY b.title")
    return render_template("books.html", books=q(sql, args), cats=q("SELECT * FROM categories"), term=term, cat=cat, sort=sort)

@app.route("/book/<int:bid>")
def book(bid):
    b = q(BOOK_SQL + "WHERE b.id=%s", (bid,), one=True)
    if not b: return redirect(url_for("books"))
    return render_template("book.html", b=b, similar=q(BOOK_SQL + "WHERE b.category_id=%s AND b.id<>%s LIMIT 4", (b["category_id"], bid)))

# ---------- cart & billing ----------
@app.post("/cart/add/<int:bid>")
def cart_add(bid):
    b = q("SELECT title,stock FROM books WHERE id=%s", (bid,), one=True)
    cart = session.get("cart", {}); n = cart.get(str(bid), 0) + 1
    if not b or n > b["stock"]: flash("Sorry, no more copies in stock.")
    else: cart[str(bid)] = n; session["cart"] = cart; flash(f"Added “{b['title']}” to your cart.")
    return redirect(request.referrer or url_for("books"))

@app.post("/cart/update/<int:bid>")
def cart_update(bid):
    cart = session.get("cart", {}); n = int(request.form.get("qty", 0) or 0)
    if n <= 0: cart.pop(str(bid), None)
    else: cart[str(bid)] = n
    session["cart"] = cart; return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    items, sub = cart_items(); return render_template("cart.html", items=items, sub=sub, tax_rate=TAX)

@app.post("/checkout")
def checkout():
    items, _ = cart_items()
    if not items: return redirect(url_for("cart"))
    disc = Decimal(0)
    if session.get("role"):  # only staff may grant a discount
        try: disc = min(max(Decimal(request.form.get("discount") or 0), Decimal(0)), Decimal(100))
        except Exception: disc = Decimal(0)
    c = db(); cur = c.cursor(dictionary=True)
    try:
        sub, rows = Decimal(0), []
        for i in items:  # lock rows, re-check stock inside ONE transaction
            cur.execute("SELECT title,stock,price FROM books WHERE id=%s FOR UPDATE", (i["book"]["id"],)); r = cur.fetchone()
            if r["stock"] < i["qty"]: raise ValueError(f"Only {r['stock']} copies of {r['title']} left.")
            sub += r["price"] * i["qty"]; rows.append((i["book"]["id"], i["qty"], r["price"]))
        d = (sub * disc / 100).quantize(Decimal("0.01")); t = ((sub - d) * TAX).quantize(Decimal("0.01"))
        cur.execute("INSERT INTO sales(customer,user_id,subtotal,discount,tax,total) VALUES(%s,%s,%s,%s,%s,%s)",
                    (request.form.get("customer") or "Walk-in", session.get("uid"), sub, d, t, sub - d + t)); sid = cur.lastrowid
        for bid, qty, price in rows:
            cur.execute("INSERT INTO sale_items(sale_id,book_id,qty,price) VALUES(%s,%s,%s,%s)", (sid, bid, qty, price))
            cur.execute("UPDATE books SET stock=stock-%s WHERE id=%s", (qty, bid))
        c.commit()
    except Exception as e:
        c.rollback(); flash(str(e)); return redirect(url_for("cart"))
    finally: c.close()
    session.pop("cart", None); return redirect(url_for("invoice", sid=sid))

@app.route("/invoice/<int:sid>")
def invoice(sid):
    s = q("SELECT s.*, u.username FROM sales s LEFT JOIN users u ON u.id=s.user_id WHERE s.id=%s", (sid,), one=True)
    if not s: return redirect(url_for("home"))
    return render_template("invoice.html", s=s, items=q("SELECT i.*, b.title FROM sale_items i JOIN books b ON b.id=i.book_id WHERE i.sale_id=%s", (sid,)))

# ---------- staff area ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = q("SELECT * FROM users WHERE username=%s", (request.form["username"],), one=True)
        if u and check_password_hash(u["password"], request.form["password"]):
            session.update(uid=u["id"], role=u["role"], user=u["username"]); return redirect(url_for("admin"))
        flash("Wrong username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("home"))

@app.route("/admin")
@role_required("admin", "staff")
def admin():
    return render_template("admin.html",
        st=q("SELECT (SELECT COUNT(*) FROM books) titles,(SELECT COALESCE(SUM(stock),0) FROM books) copies,"
             "(SELECT COALESCE(SUM(total),0) FROM sales WHERE DATE(sold_at)=CURDATE()) today,(SELECT COUNT(*) FROM sales) bills", one=True),
        low=q(BOOK_SQL + "WHERE b.stock<=b.reorder_level ORDER BY b.stock"),
        days=q("SELECT DATE_FORMAT(sold_at,'%d %b') d, SUM(total) t FROM sales GROUP BY DATE(sold_at), d ORDER BY DATE(sold_at) DESC LIMIT 7")[::-1],
        best=q("SELECT b.title, SUM(i.qty) n FROM sale_items i JOIN books b ON b.id=i.book_id GROUP BY b.id ORDER BY n DESC LIMIT 5"),
        books=q(BOOK_SQL + "ORDER BY b.title"), cats=q("SELECT * FROM categories"))

@app.post("/admin/add")
@role_required("admin")
def add_book():
    f = request.form; isbn = f["isbn"].strip()
    if not (isbn.isdigit() and len(isbn) in (10, 13)) or Decimal(f["price"]) < 0 or int(f["stock"]) < 0:
        flash("ISBN must be 10/13 digits; price and stock cannot be negative.")
    else:
        try:
            run("INSERT INTO books(title,author,category_id,isbn,price,stock,blurb) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (f["title"], f["author"], f["category_id"], isbn, f["price"], f["stock"], f["blurb"])); flash("Book added.")
        except mysql.connector.Error as e: flash(f"Could not add book: {e.msg}")
    return redirect(url_for("admin"))

@app.post("/admin/restock/<int:bid>")
@role_required("admin", "staff")
def restock(bid):
    run("UPDATE books SET stock=stock+%s WHERE id=%s", (max(int(request.form.get("n", 10)), 0), bid)); flash("Stock updated."); return redirect(url_for("admin"))

@app.post("/admin/delete/<int:bid>")
@role_required("admin")
def delete(bid):
    try: run("DELETE FROM books WHERE id=%s", (bid,)); flash("Book deleted.")
    except mysql.connector.Error: flash("This book has sales on record, so it cannot be deleted.")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    ensure_users(); app.run(debug=True)
