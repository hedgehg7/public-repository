import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE


class database_importer:
    def __init__(self, db_url=DATABASE):
        """
        Инициализирует импортер с подключением к базе данных
        :param db_url: URL базы данных (по умолчанию берется из config.py)
        """
        self.engine = create_engine(db_url)
        self.material_types_file = 'Material_type_import.xlsx'
        self.materials_file = 'Materials_import.xlsx'
        self.product_types_file = 'Product_type_import.xlsx'
        self.products_file = 'Products_import.xlsx'
        self.product_materials_file = 'Product_materials_import.xlsx'

    def execute_sql(self, query):
        """
        Выполняет SQL запрос
        :param query: SQL запрос для выполнения
        """
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()

    def create_tables(self):
        """
        Создает все необходимые таблицы в базе данных
        """
        sql_queries = [
            """
            CREATE TABLE IF NOT EXISTS MaterialType (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                loss_percent REAL NOT NULL
            );
            """,
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS ProductType (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                coefficient REAL NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_number INTEGER NOT NULL UNIQUE,
                type_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                min_partner_price REAL NOT NULL,
                roll_width REAL NOT NULL,
                FOREIGN KEY (type_id) REFERENCES ProductType(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ProductMaterial (
                product_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                required_amount REAL NOT NULL,
                PRIMARY KEY (product_id, material_id),
                FOREIGN KEY (product_id) REFERENCES Product(id),
                FOREIGN KEY (material_id) REFERENCES Material(id)
            );
            """
        ]
        
        for query in sql_queries:
            self.execute_sql(query)

    def load_excel_data(self, file_path, sheet_name):
        """
        Загружает данные из Excel файла
        :param file_path: путь к файлу Excel
        :param sheet_name: название листа
        :return: DataFrame с данными
        """
        return pd.read_excel(file_path, sheet_name=sheet_name)

    def load_all_data(self):
        """
        Загружает все данные из Excel файлов
        :return: кортеж с DataFrames (material_types, materials, product_types, products, product_materials)
        """
        material_types = self.load_excel_data(self.material_types_file, 'Material_type_import')
        materials = self.load_excel_data(self.materials_file, 'Materials_import')
        product_types = self.load_excel_data(self.product_types_file, 'Product_type_import')
        products = self.load_excel_data(self.products_file, 'Products_import')
        product_materials = self.load_excel_data(self.product_materials_file, 'Product_materials_import')
        
        return material_types, materials, product_types, products, product_materials

    def insert_material_types(self, material_types):
        """
        Вставляет типы материалов в базу данных
        :param material_types: DataFrame с типами материалов
        """
        material_types.to_sql('MaterialType', self.engine, if_exists='append', index=False)

    def insert_materials(self, materials, material_types):
        """
        Вставляет материалы в базу данных
        :param materials: DataFrame с материалами
        :param material_types: DataFrame с типами материалов
        """
        materials_with_types = pd.merge(
            materials,
            material_types,
            left_on='Тип материала',
            right_on='Тип материала',
            how='left'
        )
        
        materials_to_insert = materials_with_types[[
            'Наименование материала', 'Цена единицы материала', 
            'Количество на складе', 'Минимальное количество',
            'Количество в упаковке', 'Единица измерения'
        ]].copy()
        materials_to_insert['type_id'] = materials_with_types.index + 1
        
        materials_to_insert.columns = [
            'name', 'unit_price', 'stock_quantity', 
            'min_stock_quantity', 'package_quantity', 
            'unit_of_measure', 'type_id'
        ]
        
        materials_to_insert.to_sql('Material', self.engine, if_exists='append', index=False)

    def insert_product_types(self, product_types):
        """
        Вставляет типы продукции в базу данных
        :param product_types: DataFrame с типами продукции
        """
        product_types.to_sql('ProductType', self.engine, if_exists='append', index=False)

    def insert_products(self, products, product_types):
        """
        Вставляет продукцию в базу данных
        :param products: DataFrame с продукцией
        :param product_types: DataFrame с типами продукции
        """
        products_with_types = pd.merge(
            products,
            product_types,
            left_on='Тип продукции',
            right_on='Тип продукции',
            how='left'
        )
        
        products_to_insert = products_with_types[[
            'Артикул', 'Наименование продукции', 
            'Минимальная стоимость для партнера', 'Ширина рулона, м'
        ]].copy()
        products_to_insert['type_id'] = products_with_types.index + 1
        
        products_to_insert.columns = [
            'article_number', 'name', 
            'min_partner_price', 'roll_width',
            'type_id'
        ]
        
        products_to_insert.to_sql('Product', self.engine, if_exists='append', index=False)

    def insert_product_materials(self, product_materials):
        """
        Вставляет связи между продукцией и материалами
        :param product_materials: DataFrame со связями продукции и материалов
        """
        with self.engine.connect() as conn:
            product_ids = pd.read_sql('SELECT id, name FROM Product', conn)
            material_ids = pd.read_sql('SELECT id, name FROM Material', conn)
        
        product_materials_with_ids = pd.merge(
            product_materials,
            product_ids,
            left_on='Продукция',
            right_on='name',
            how='left'
        )
        
        product_materials_with_ids = pd.merge(
            product_materials_with_ids,
            material_ids,
            left_on='Наименование материала',
            right_on='name',
            how='left',
            suffixes=('_product', '_material')
        )
        
        product_materials_to_insert = product_materials_with_ids[[
            'id_product', 'id_material', 'Необходимое количество материала'
        ]]
        
        product_materials_to_insert.columns = [
            'product_id', 'material_id', 'required_amount'
        ]
        
        product_materials_to_insert.to_sql('ProductMaterial', self.engine, if_exists='append', index=False)

    def create_indexes(self):
        """
        Создает индексы для ускорения запросов
        """
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_material_type ON Material(type_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_type ON Product(type_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_material_product ON ProductMaterial(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_material_material ON ProductMaterial(material_id);"
        ]
        
        for query in index_queries:
            self.execute_sql(query)

    def import_all_data(self):
        """
        Основной метод для импорта всех данных
        """
        try:
            # Создаем таблицы
            self.create_tables()
            
            # Загружаем данные
            material_types, materials, product_types, products, product_materials = self.load_all_data()
            
            # Вставляем данные
            self.insert_material_types(material_types)
            self.insert_materials(materials, material_types)
            self.insert_product_types(product_types)
            self.insert_products(products, product_types)
            self.insert_product_materials(product_materials)
            
            # Создаем индексы
            self.create_indexes()
            
            print("Данные успешно импортированы в базу данных")
            return True
        except Exception as e:
            print(f"Ошибка при импорте данных: {str(e)}")
            return False


if __name__ == "__main__":
    importer = DatabaseImporter()
    importer.import_all_data()
