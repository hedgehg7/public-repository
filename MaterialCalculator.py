import math
from flask import flash
from model import model_db


class material_calculator:
    def __init__(self, db_connection=None):
        """
        Инициализация калькулятора материалов
        :param db_connection: соединение с базой данных (если None, создается новое)
        """
        
        self.conn = db_connection if db_connection else model_db().init_db()
        self.errors = []
        self.result = None
        self.form_data = {
            'product_type_id': '',
            'material_type_id': '',
            'product_count': '',
            'param1': '',
            'param2': '',
            'current_stock': '0',
        }

    def __del__(self):
        """Закрываем соединение с БД при уничтожении объекта"""
        if self.conn:
            self.conn.close()

    def get_product_types(self):
        """Получает список типов продукции из БД"""
        return self.conn.execute("SELECT id, type_name FROM ProductType").fetchall()

    def get_material_types(self):
        """Получает список типов материалов из БД"""
        return self.conn.execute("SELECT id, type_name FROM MaterialType").fetchall()

    def validate_input(self, form_data):
        """
        Валидирует входные данные
        :param form_data: словарь с данными формы
        :return: кортеж (валидные данные или None, список ошибок)
        """
        self.errors = []
        self.form_data = form_data.copy()

        try:
            product_type_id = int(form_data.get('product_type_id', ''))
            material_type_id = int(form_data.get('material_type_id', ''))
            product_count = int(form_data.get('product_count', ''))
            param1 = float(form_data.get('param1', ''))
            param2 = float(form_data.get('param2', ''))
            current_stock = float(form_data.get('current_stock', '0'))

            if product_count <= 0:
                self.errors.append("Количество продукции должно быть положительным!")
            if param1 <= 0:
                self.errors.append("Параметр 1 должен быть положительным!")
            if param2 <= 0:
                self.errors.append("Параметр 2 должен быть положительным!")
            if current_stock < 0:
                self.errors.append("Текущий запас не может быть отрицательным!")

            if not self.errors:
                return {
                    'product_type_id': product_type_id,
                    'material_type_id': material_type_id,
                    'product_count': product_count,
                    'param1': param1,
                    'param2': param2,
                    'current_stock': current_stock
                }

        except (ValueError, TypeError):
            self.errors.append("Некорректные входные данные!")

        return None

    def get_coefficients(self, product_type_id, material_type_id):
        """
        Получает коэффициенты из БД
        :return: кортеж (product_coeff, loss_percent) или (None, None) если не найдены
        """
        product_coeff = self.conn.execute(
            'SELECT coefficient FROM ProductType WHERE id = ?',
            (product_type_id,)
        ).fetchone()

        loss_percent = self.conn.execute(
            'SELECT loss_percent FROM MaterialType WHERE id = ?',
            (material_type_id,)
        ).fetchone()

        if not product_coeff or not loss_percent:
            self.errors.append("Указаны несуществующие типы продукции или материалов!")
            return None, None

        return product_coeff['coefficient'], loss_percent['loss_percent']

    def calculate_material(self, valid_data):
        """
        Выполняет расчет необходимого материала
        :param valid_data: валидированные данные
        :return: результат расчета или None при ошибке
        """
        try:
            product_coeff, loss_percent = self.get_coefficients(
                valid_data['product_type_id'],
                valid_data['material_type_id']
            )

            if product_coeff is None or loss_percent is None:
                return None

            # Рассчитываем количество материала на одну единицу продукции
            material_per_unit = (
                valid_data['param1'] * 
                valid_data['param2'] * 
                product_coeff
            )

            # Учитываем брак материала
            if loss_percent >= 1:
                raise ValueError("Потери материала не могут быть 100% и более")

            adjusted_material_per_unit = material_per_unit / (1 - loss_percent)

            # Общее необходимое количество материала
            total_material_needed = adjusted_material_per_unit * valid_data['product_count']

            # Учитываем текущий запас
            material_to_order = total_material_needed - valid_data['current_stock']

            # Если материала достаточно
            if material_to_order <= 0:
                return 0

            # Округляем до целого числа
            return math.ceil(material_to_order)

        except ZeroDivisionError:
            self.errors.append("Ошибка расчета: потеря материала не может быть 100%!")
        except ValueError as e:
            self.errors.append(f"Ошибка расчета: {str(e)}")
        except Exception as e:
            self.errors.append(f"Неизвестная ошибка расчета: {str(e)}")

        return None

    def process_request(self, request_form):
        """
        Обрабатывает запрос на расчет
        :param request_form: данные формы из Flask request.form
        :return: результат расчета или None при ошибке
        """
        # Обновляем данные формы
        for key in self.form_data:
            if key in request_form:
                self.form_data[key] = request_form[key]

        # Валидация данных
        valid_data = self.validate_input(self.form_data)
        if not valid_data:
            return None

        # Выполняем расчет
        self.result = self.calculate_material(valid_data)
        return self.result

    def get_flash_messages(self):
        """Возвращает сообщения об ошибках для отображения через flash"""
        return [(error, "error") for error in self.errors]

    def get_template_data(self):
        """Возвращает данные для передачи в шаблон"""
        return {
            'product_types': self.get_product_types(),
            'material_types': self.get_material_types(),
            'result': self.result,
            'form_data': self.form_data
        }
