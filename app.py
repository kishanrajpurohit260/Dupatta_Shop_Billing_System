from reportlab.pdfgen import canvas
from flask import send_file
import os
from io import BytesIO
from flask import Flask, render_template, request, redirect, session
import json
from database import connect_db



app = Flask(__name__)

app.secret_key = "dupatta_shop"


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]


    db = connect_db()
    cursor = db.cursor()


    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username,password)
    )


    user = cursor.fetchone()


    if user:
        session["user"] = username
        return redirect("/dashboard")

    else:
        return "Invalid Username or Password"



@app.route("/dashboard")
def dashboard():

    db = connect_db()
    cursor = db.cursor()


    cursor.execute("SELECT COUNT(*) FROM products")
    products = cursor.fetchone()[0]


    cursor.execute("SELECT COUNT(*) FROM bills")
    bills = cursor.fetchone()[0]


    cursor.execute("SELECT SUM(total) FROM bills")
    sales = cursor.fetchone()[0]

    if sales is None:
        sales = 0


    cursor.execute(
        "SELECT COUNT(*) FROM products WHERE stock < 5"
    )

    low_stock = cursor.fetchone()[0]


    return render_template(
        "dashboard.html",
        products=products,
        bills=bills,
        sales=sales,
        low_stock=low_stock
    )

@app.route("/products")
def products():

    search = request.args.get("search")

    db = connect_db()

    cursor = db.cursor()

    if search:

        cursor.execute(
            "SELECT * FROM products WHERE name LIKE %s",
            ("%" + search + "%",)
        )

    else:

        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    return render_template(
        "products.html",
        products=products
    )



@app.route("/add_product", methods=["POST"])
def add_product():

    name = request.form["name"]
    design = request.form["design"]
    price = request.form["price"]
    stock = request.form["stock"]
    hsn_code = request.form["hsn_code"]
    gst = request.form["gst"]
    unit = request.form["unit"]

    db = connect_db()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO products
        (name,design,price,stock,hsn_code,gst,unit)
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        """,
        (name,design,price,stock,hsn_code,gst,unit)
    )


    db.commit()


    return redirect("/products")

@app.route("/delete_product/<int:id>")
def delete_product(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect("/products")

@app.route("/add_stock/<int:id>")
def add_stock(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cursor.fetchone()

    return render_template(
        "add_stock.html",
        product=product
    )

@app.route("/update_stock", methods=["POST"])
def update_stock():

    product_id = request.form["id"]
    new_stock = int(request.form["new_stock"])

    db = connect_db()
    cursor = db.cursor()

    # Current Stock nikaalo
    cursor.execute(
        "SELECT stock FROM products WHERE id=%s",
        (product_id,)
    )

    current_stock = cursor.fetchone()[0]

    # Naya Stock calculate karo
    total_stock = current_stock + new_stock

    # -------------------------------
    # Stock History Save
    # -------------------------------
    cursor.execute(
        """
        INSERT INTO stock_history
        (product_id, added_stock, old_stock, new_stock)
        VALUES(%s,%s,%s,%s)
        """,
        (
            product_id,
            new_stock,
            current_stock,
            total_stock
        )
    )

    # -------------------------------
    # Products Table Update
    # -------------------------------
    cursor.execute(
        """
        UPDATE products
        SET stock=%s
        WHERE id=%s
        """,
        (total_stock, product_id)
    )

    db.commit()

    return redirect("/products")

@app.route("/edit_product/<int:id>")
def edit_product(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cursor.fetchone()

    return render_template(
        "edit_product.html",
        product=product
    )

@app.route("/update_product", methods=["POST"])
def update_product():

    id = request.form["id"]
    name = request.form["name"]
    design = request.form["design"]
    price = request.form["price"]
    stock = request.form["stock"]
    hsn_code = request.form["hsn_code"]
    gst = request.form["gst"]
    unit = request.form["unit"]

    db = connect_db()
    cursor = db.cursor()


    cursor.execute(
        """
        UPDATE products
        SET
        name=%s,
        design=%s,
        price=%s,
        stock=%s,
        hsn_code=%s,
        gst=%s,
        unit=%s
        WHERE id=%s
        """,
        (name,design,price,stock,hsn_code,gst,unit,id)
    )


    db.commit()

    return redirect("/products")


@app.route("/billing")
def billing():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    return render_template(
        "billing.html",
        products=products
    )



@app.route("/create_bill", methods=["POST"])
def create_bill():

    import json

    customer = request.form["customer"]
    mobile = request.form["mobile"]
    customer_address = request.form["customer_address"]
    customer_gstin = request.form["customer_gstin"]
    state = request.form["state"]

    print("FORM DATA:", request.form)
    print("bill_data =", request.form.get("bill_data"))

    bill_data = json.loads(request.form["bill_data"])

    db = connect_db()
    cursor = db.cursor()

    grand_total = 0

    # Grand Total Calculate
    for item in bill_data:

        grand_total += item["qty"] * item["price"]

    # Bill Save
    cursor.execute(
        """
        INSERT INTO bills
        (
        customer_name,
        mobile,
        customer_address,
        customer_gstin,
        state,
        place_of_supply,
        total
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s)
        """,
        (customer,mobile,customer_address,customer_gstin,state,state,grand_total)
    )

    bill_id = cursor.lastrowid

    # Save Every Product
    for item in bill_data:

        cursor.execute(
            """
            INSERT INTO bill_items
            (bill_id,product_id,quantity,price)
            VALUES(%s,%s,%s,%s)
            """,
            (
                bill_id,
                item["product_id"],
                item["qty"],
                item["price"]
            )
        )
        # Stock Update
        cursor.execute(
            """
            UPDATE products
            SET stock = stock - %s
            WHERE id=%s
            """,
            (
                item["qty"],
                item["product_id"]
            )
        )

    db.commit()

    return redirect(f"/bill/{bill_id}")

@app.route("/bill/<int:bill_id>")
def bill(bill_id):

    db = connect_db()
    cursor = db.cursor()

    # Bill Details
    cursor.execute(
    """
    SELECT
    customer_name,
    mobile,
    customer_address,
    customer_gstin,
    state,
    place_of_supply,
    total,
    date
    FROM bills
    WHERE id=%s
    """,
    (bill_id,)
    )

    bill = cursor.fetchone()

    # Bill Items
    cursor.execute(
    """
    SELECT
    products.name,
    products.design,
    bill_items.quantity,
    bill_items.price,
    products.hsn_code,
    products.gst,
    products.unit
    FROM bill_items
    JOIN products
    ON bill_items.product_id = products.id
    WHERE bill_items.bill_id=%s
    """,
    (bill_id,)
    )

    items = cursor.fetchall()
    # Company Settings

    cursor.execute("SELECT * FROM settings LIMIT 1")
    setting = cursor.fetchone()

    return render_template(
    "bill.html",
    bill_id=bill_id,
    customer=bill[0],
    mobile=bill[1],
    customer_address=bill[2],
    customer_gstin=bill[3],
    state=bill[4],
    place_of_supply=bill[5],
    total=bill[6],
    today=bill[7],
    items=items,
    gst_percent = float(items[0][5]),

    shop_name=setting[1],
    owner_name=setting[2],
    shop_mobile=setting[3],
    shop_email=setting[4],
    shop_address=setting[5],
    shop_gstin=setting[6],
    bank_name=setting[7],
    account_no=setting[8],
    ifsc=setting[9]
    )

@app.route("/sales")
def sales():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM bills ORDER BY id DESC"
    )

    bills = cursor.fetchall()

    return render_template(
        "sales.html",
        bills=bills
    )

@app.route("/settings")
def settings():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM settings LIMIT 1")

    setting = cursor.fetchone()

    return render_template(
        "settings.html",
        setting=setting
    )

@app.route("/update_settings", methods=["POST"])
def update_settings():

    shop_name = request.form["shop_name"]
    owner_name = request.form["owner_name"]
    mobile = request.form["mobile"]
    email = request.form["email"]
    address = request.form["address"]
    gstin = request.form["gstin"]
    bank_name = request.form["bank_name"]
    account_no = request.form["account_no"]
    ifsc = request.form["ifsc"]

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE settings
        SET
        shop_name=%s,
        owner_name=%s,
        mobile=%s,
        email=%s,
        address=%s,
        gstin=%s,
        bank_name=%s,
        account_no=%s,
        ifsc=%s
        WHERE id=1
        """,
        (
            shop_name,
            owner_name,
            mobile,
            email,
            address,
            gstin,
            bank_name,
            account_no,
            ifsc
        )
    )

    db.commit()

    return redirect("/settings")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/pdf/<int:id>")
def pdf(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM bills WHERE id=%s",
        (id,)
    )

    bill = cursor.fetchone()

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.drawString(100, 750, "Dupatta Shop Billing System")
    pdf.drawString(100, 700, f"Customer: {bill[1]}")
    pdf.drawString(100, 650, f"Mobile: {bill[2]}")
    pdf.drawString(100, 600, f"Total: {bill[3]}")

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"bill_{id}.pdf",
        mimetype="application/pdf"
    )

@app.route("/stock_history")
def stock_history():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT
    stock_history.id,
    products.name,
    stock_history.old_stock,
    stock_history.added_stock,
    stock_history.new_stock,
    stock_history.date

    FROM stock_history

    JOIN products

    ON stock_history.product_id = products.id

    ORDER BY stock_history.id DESC
    """)

    history = cursor.fetchall()

    return render_template(
        "stock_history.html",
        history=history
    )

@app.route("/purchase")
def purchase():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()

    return render_template(
        "purchase.html",
        products=products,
        suppliers=suppliers
    )

@app.route("/save_purchase", methods=["POST"])
def save_purchase():

    supplier_id = request.form["supplier_id"]
    invoice_no = request.form["invoice_no"]
    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])
    purchase_price = float(request.form["purchase_price"])

    total = quantity * purchase_price

    db = connect_db()
    cursor = db.cursor()

    # Purchase table me save
    cursor.execute(
    """
    INSERT INTO purchases
    (supplier_id, invoice_no, product_id, quantity, purchase_price, total)
    VALUES(%s,%s,%s,%s,%s,%s)
    """,
    (
        supplier_id,
        invoice_no,
        product_id,
        quantity,
        purchase_price,
        total
    )
)

    # Current stock nikalo
    cursor.execute(
        "SELECT stock FROM products WHERE id=%s",
        (product_id,)
    )

    current_stock = cursor.fetchone()[0]

    new_stock = current_stock + quantity

    # Products table update
    cursor.execute(
        """
        UPDATE products
        SET stock=%s
        WHERE id=%s
        """,
        (
            new_stock,
            product_id
        )
    )

    db.commit()

    return redirect("/purchase")

@app.route("/purchase_history")
def purchase_history():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT

    purchases.id,
    suppliers.supplier_name,
    purchases.invoice_no,
    products.name,
    products.design,
    purchases.quantity,
    purchases.purchase_price,
    purchases.total,
    purchases.purchase_date

    FROM purchases

    JOIN suppliers
    ON purchases.supplier_id = suppliers.id

    JOIN products
    ON purchases.product_id = products.id

    ORDER BY purchases.id DESC
    """)

    purchases = cursor.fetchall()

    return render_template(
        "purchase_history.html",
        purchases=purchases
    )

@app.route("/suppliers")
def suppliers():

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM suppliers ORDER BY id DESC"
    )

    suppliers = cursor.fetchall()

    return render_template(
        "suppliers.html",
        suppliers=suppliers
    )

@app.route("/add_supplier", methods=["POST"])
def add_supplier():

    supplier_name = request.form["supplier_name"]
    mobile = request.form["mobile"]
    address = request.form["address"]
    gst_number = request.form["gst_number"]

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO suppliers
        (supplier_name,mobile,address,gst_number)
        VALUES(%s,%s,%s,%s)
        """,
        (supplier_name,mobile,address,gst_number)
    )

    db.commit()

    return redirect("/suppliers")

@app.route("/delete_supplier/<int:id>")
def delete_supplier(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM suppliers WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect("/suppliers")

@app.route("/edit_supplier/<int:id>")
def edit_supplier(id):

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM suppliers WHERE id=%s",
        (id,)
    )

    supplier = cursor.fetchone()

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )

@app.route("/update_supplier", methods=["POST"])
def update_supplier():

    id = request.form["id"]
    supplier_name = request.form["supplier_name"]
    mobile = request.form["mobile"]
    address = request.form["address"]
    gst_number = request.form["gst_number"]

    db = connect_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE suppliers
        SET
        supplier_name=%s,
        mobile=%s,
        address=%s,
        gst_number=%s
        WHERE id=%s
        """,
        (
            supplier_name,
            mobile,
            address,
            gst_number,
            id
        )
    )

    db.commit()

    return redirect("/suppliers")

if __name__ == "__main__":
    app.run(debug=True)

