from flask import Flask, request, render_template, redirect, flash, url_for
import sqlite3
import math
from datetime import datetime
from config import DATABASE
from insert_bd import database_importer
from MaterialCalculator import material_calculator
import os
app = Flask(__name__)
app.secret_key = "secret_key_123"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    
    if not(os.path.isfile(DATABASE)):
        db = database_importer()
        db.import_all_data()
    conn = get_db_connection()
    
    products = conn.execute('''
        SELECT p.id, p.article_number, p.name, pt.type_name, 
               p.min_partner_price, p.roll_width,
               SUM(m.unit_price * pm.required_amount) AS calculated_cost
        FROM Product p
        JOIN ProductType pt ON p.type_id = pt.id
        LEFT JOIN ProductMaterial pm ON p.id = pm.product_id
        LEFT JOIN Material m ON pm.material_id = m.id
        GROUP BY p.id
    ''').fetchall()
    
    conn.close()
    return render_template("index.html", products=products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    """Добавление нового продукта"""
    conn = get_db_connection()
    
    if request.method == "POST":
        article_number = request.form.get("article_number")
        type_id = request.form.get("type_id")
        name = request.form.get("name")
        min_partner_price = request.form.get("min_partner_price")
        roll_width = request.form.get("roll_width")
        
        errors = []
        try:
            article_number = int(article_number)
        except ValueError:
            errors.append("Артикул должен быть целым числом!")
        
        if not name:
            errors.append("Наименование продукта обязательно!")
        
        try:
            min_partner_price = float(min_partner_price)
            if min_partner_price < 0:
                errors.append("Цена не может быть отрицательной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение цены!")
        
        try:
            roll_width = float(roll_width)
            if roll_width <= 0:
                errors.append("Ширина рулона должна быть положительной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение ширины рулона!")
        
        if errors:
            for error in errors:
                flash(error, "error")
            product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
            return render_template("product_form.html", 
                                   product_types=product_types,
                                   article_number=article_number,
                                   type_id=type_id,
                                   name=name,
                                   min_partner_price=min_partner_price,
                                   roll_width=roll_width)
        
    
        try:
            conn.execute('''
                INSERT INTO Product (article_number, type_id, name, 
                                    min_partner_price, roll_width)
                VALUES (?, ?, ?, ?, ?)
            ''', (article_number, type_id, name, 
                  min_partner_price, roll_width))
            conn.commit()
            flash("Продукт успешно добавлен!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                flash("Продукт с таким артикулом уже существует!", "error")
            else:
                flash(f"Ошибка базы данных: {str(e)}", "error")
            product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
            return render_template("product_form.html", 
                                  product_types=product_types,
                                  article_number=article_number,
                                  type_id=type_id,
                                  name=name,
                                  min_partner_price=min_partner_price,
                                  roll_width=roll_width)
    
    product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
    conn.close()
    return render_template("product_form.html", product_types=product_types)

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    """Редактирование существующего продукта"""
    conn = get_db_connection()
    
    if request.method == "POST":
        article_number = request.form.get("article_number")
        type_id = request.form.get("type_id")
        name = request.form.get("name")
        min_partner_price = request.form.get("min_partner_price")
        roll_width = request.form.get("roll_width")
        
        errors = []
        try:
            article_number = int(article_number)
        except ValueError:
            errors.append("Артикул должен быть целым числом!")
        
        if not name:
            errors.append("Наименование продукта обязательно!")
        
        try:
            min_partner_price = float(min_partner_price)
            if min_partner_price < 0:
                errors.append("Цена не может быть отрицательной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение цены!")
        
        try:
            roll_width = float(roll_width)
            if roll_width <= 0:
                errors.append("Ширина рулона должна быть положительной!")
        except (ValueError, TypeError):
            errors.append("Некорректное значение ширины рулона!")
        
        if errors:
            for error in errors:
                flash(error, "error")
            product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
            return render_template("product_form.html", 
                                   product_types=product_types,
                                   article_number=article_number,
                                   type_id=type_id,
                                   name=name,
                                   min_partner_price=min_partner_price,
                                   roll_width=roll_width,
                                   product_id=product_id)
   
        try:
            conn.execute('''
                UPDATE Product SET 
                    article_number = ?,
                    type_id = ?,
                    name = ?,
                    min_partner_price = ?,
                    roll_width = ?
                WHERE id = ?
            ''', (article_number, type_id, name, 
                  min_partner_price, roll_width, product_id))
            conn.commit()
            flash("Продукт успешно обновлен!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                flash("Продукт с таким артикулом уже существует!", "error")
            else:
                flash(f"Ошибка базы данных: {str(e)}", "error")
            product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
            return render_template("product_form.html", 
                                  product_types=product_types,
                                  article_number=article_number,
                                  type_id=type_id,
                                  name=name,
                                  min_partner_price=min_partner_price,
                                  roll_width=roll_width,
                                  product_id=product_id)

    product = conn.execute('''
        SELECT id, article_number, type_id, name, 
               min_partner_price, roll_width
        FROM Product
        WHERE id = ?
    ''', (product_id,)).fetchone()
    
    if not product:
        flash("Продукт не найден!", "error")
        conn.close()
        return redirect(url_for("index"))
    
    product_types = conn.execute("SELECT id, type_name FROM ProductType").fetchall()
    conn.close()
    return render_template("product_form.html", 
                           product_types=product_types,
                           **dict(product),
                           product_id=product_id)

@app.route("/product_materials/<int:product_id>")
def product_materials(product_id):
    """Просмотр материалов для конкретного продукта"""
    conn = get_db_connection()
    
    product = conn.execute('''
        SELECT p.name, p.article_number, pt.type_name
        FROM Product p
        JOIN ProductType pt ON p.type_id = pt.id
        WHERE p.id = ?
    ''', (product_id,)).fetchone()
    
    if not product:
        flash("Продукт не найден!", "error")
        conn.close()
        return redirect(url_for("index"))
    
    materials = conn.execute('''
        SELECT m.name, mt.type_name AS material_type, 
               pm.required_amount, m.unit_of_measure
        FROM ProductMaterial pm
        JOIN Material m ON pm.material_id = m.id
        JOIN MaterialType mt ON m.type_id = mt.id
        WHERE pm.product_id = ?
    ''', (product_id,)).fetchall()
    
    conn.close()
    return render_template("product_materials.html", 
                           product=dict(product),
                           materials=materials)

@app.route("/calculate_material", methods=["GET", "POST"])
def calculate_material():
    """Расчет необходимого материала (Модуль 4)"""
    calculator = material_calculator()
    
    if request.method == "POST":
        result = calculator.process_request(request.form)
        
      
        for message, category in calculator.get_flash_messages():
            flash(message, category)
    
    template_data = calculator.get_template_data()
    return render_template("material_calculator.html", **template_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2030, debug=True)
