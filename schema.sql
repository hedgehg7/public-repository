-- Создание таблицы типов материалов
CREATE TABLE IF NOT EXISTS MaterialType (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    loss_percent REAL NOT NULL
);

-- Создание таблицы материалов
CREATE TABLE IF NOT EXISTS Material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type_id INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    stock_quantity REAL NOT NULL,
    min_stock_quantity REAL NOT NULL,
    package_quantity REAL NOT NULL,
    unit_of_measure TEXT NOT NULL,
    FOREIGN KEY (type_id) REFERENCES MaterialType(id)
);

-- Создание таблицы типов продукции
CREATE TABLE IF NOT EXISTS ProductType (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    coefficient REAL NOT NULL
);

-- Создание таблицы продукции
CREATE TABLE IF NOT EXISTS Product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_number INTEGER NOT NULL UNIQUE,
    type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    min_partner_price REAL NOT NULL,
    roll_width REAL NOT NULL,
    FOREIGN KEY (type_id) REFERENCES ProductType(id)
);

-- Создание связующей таблицы продукция-материалы
CREATE TABLE IF NOT EXISTS ProductMaterial (
    product_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    required_amount REAL NOT NULL,
    PRIMARY KEY (product_id, material_id),
    FOREIGN KEY (product_id) REFERENCES Product(id),
    FOREIGN KEY (material_id) REFERENCES Material(id)
);
