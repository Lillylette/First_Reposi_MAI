import sys
import os
import sqlite3
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QApplication, QPushButton, QLabel, QMessageBox, QInputDialog, QDialog, QComboBox,
                             QDateEdit, QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QScrollArea, QTextEdit)
from PyQt6.QtCore import Qt, QDate, QRect
from PyQt6.QtGui import QPixmap, QPainter, QPen, QMouseEvent
from PIL import Image, ImageFilter

def grayscale_image(src_path, dst_path):
    img = Image.open(src_path)
    gray_img = img.convert('L')
    gray_img.save(dst_path)


def init_database(db_filename='photos_app.db'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, db_filename)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON;')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            description TEXT,
            title_date TEXT,
            title_location TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE,
            photo_date TEXT,
            title_id INTEGER,
            comment TEXT,
            FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn, cursor, base_dir

conn, cursor, BASE_DIR = init_database()
GALLERY_DIR = os.path.join(BASE_DIR, "Gallery")

class FilterSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор фильтра")
        self.resize(400, 300)
        layout = QVBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "BLUR", "BoxBlur", "GaussianBlur", "CONTOUR", "DETAIL", "EDGE_ENHANCE",
            "EDGE_ENHANCE_MORE", "EMBOSS", "FIND_EDGES", "SMOOTH", "SMOOTH_MORE",
            "SHARPEN", "UnsharpMask", "RankFilter", "MedianFilter",
            "MinFilter", "MaxFilter", "ModeFilter"
        ])
        layout.addWidget(QLabel("Фильтр:"))
        layout.addWidget(self.filter_combo)
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.accept)
        layout.addWidget(self.select_button)
        self.setLayout(layout)

class FilterPreviewDialog(QDialog):
    def __init__(self, image_path, filter_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр фильтра")
        self.resize(800, 600)
        self.image_path = image_path
        self.filter_name = filter_name
        self.original_image = Image.open(image_path)
        self.filtered_image = self.original_image.copy()
        layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.label = QLabel()
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        self.param_layout = QHBoxLayout()
        self.param_label = QLabel("Параметр:")
        self.param_edit = QLineEdit("3")
        self.param_edit.textChanged.connect(self.update_preview)
        self.param_layout.addWidget(self.param_label)
        self.param_layout.addWidget(self.param_edit)
        layout.addLayout(self.param_layout)
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_image)
        layout.addWidget(self.save_button)
        self.setLayout(layout)
        self.update_preview()

    def update_preview(self):
        try:
            param = int(self.param_edit.text())
            if param < 1:
                param = 3
            elif param % 2 == 0:
                param += 1
            elif param > 31:
                param = 31
        except ValueError:
            param = 3
        if self.filter_name == "BLUR":
            self.filtered_image = self.original_image.filter(ImageFilter.BLUR)
        elif self.filter_name == "BoxBlur":
            self.filtered_image = self.original_image.filter(ImageFilter.BoxBlur(param))
        elif self.filter_name == "GaussianBlur":
            self.filtered_image = self.original_image.filter(ImageFilter.GaussianBlur(param))
        elif self.filter_name == "CONTOUR":
            self.filtered_image = self.original_image.filter(ImageFilter.CONTOUR)
        elif self.filter_name == "DETAIL":
            self.filtered_image = self.original_image.filter(ImageFilter.DETAIL)
        elif self.filter_name == "EDGE_ENHANCE":
            self.filtered_image = self.original_image.filter(ImageFilter.EDGE_ENHANCE)
        elif self.filter_name == "EDGE_ENHANCE_MORE":
            self.filtered_image = self.original_image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        elif self.filter_name == "EMBOSS":
            self.filtered_image = self.original_image.filter(ImageFilter.EMBOSS)
        elif self.filter_name == "FIND_EDGES":
            self.filtered_image = self.original_image.filter(ImageFilter.FIND_EDGES)
        elif self.filter_name == "SMOOTH":
            self.filtered_image = self.original_image.filter(ImageFilter.SMOOTH)
        elif self.filter_name == "SMOOTH_MORE":
            self.filtered_image = self.original_image.filter(ImageFilter.SMOOTH_MORE)
        elif self.filter_name == "SHARPEN":
            self.filtered_image = self.original_image.filter(ImageFilter.SHARPEN)
        elif self.filter_name == "UnsharpMask":
            self.filtered_image = self.original_image.filter(ImageFilter.UnsharpMask(radius=param))
        elif self.filter_name == "RankFilter":
            self.filtered_image = self.original_image.filter(ImageFilter.RankFilter(param, rank=param))
        elif self.filter_name == "MedianFilter":
            self.filtered_image = self.original_image.filter(ImageFilter.MedianFilter(size=param))
        elif self.filter_name == "MinFilter":
            self.filtered_image = self.original_image.filter(ImageFilter.MinFilter(size=param))
        elif self.filter_name == "MaxFilter":
            self.filtered_image = self.original_image.filter(ImageFilter.MaxFilter(size=param))
        elif self.filter_name == "ModeFilter":
            self.filtered_image = self.original_image.filter(ImageFilter.ModeFilter(size=param))
        self.show_image(self.filtered_image)

    def show_image(self, img):
        pixmap = QPixmap()
        img.save("temp_preview.jpg", "JPEG")
        pixmap.load("temp_preview.jpg")
        self.label.setPixmap(pixmap.scaled(self.scroll_area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def save_image(self):
        new_filename, ok = QInputDialog.getText(self, "Сохранить как", "Введите имя нового файла:")
        if ok and new_filename:
            new_filename = new_filename + ".jpg"
            self.filtered_image.save(os.path.join(self.parent().gallery_folder, new_filename))
            self.accept()
            self.new_filename = new_filename


class PreviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Предпросмотр изображения")
        self.setGeometry(600, 300, 600, 400)
        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

    def show_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.label.setPixmap(pixmap.scaled(self.scroll_area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.show()
        else:
            self.label.setText("Не удалось загрузить изображение")

class AddTitleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить заголовок")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Заголовок:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Описание:"))
        self.desc_edit = QLineEdit()
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Дата фотосессии:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Место фотосессии:"))
        self.location_edit = QLineEdit()
        location_layout.addWidget(self.location_edit)
        layout.addLayout(location_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("ОК")
        self.cancel_button = QPushButton("Отмена")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "location": self.location_edit.text().strip()
        }


class ProcessingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Обработка")
        self.resize(400, 300)
        layout = QVBoxLayout()
        self.process_list = QListWidget()
        self.process_list.addItems(["Градации серого", "Фильтры"])
        layout.addWidget(self.process_list)
        self.execute_button = QPushButton("Выполнить")
        self.execute_button.clicked.connect(self.execute_processing)
        layout.addWidget(self.execute_button)
        self.setLayout(layout)

    def execute_processing(self):
        selected = self.process_list.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите обработку")
            return
        if selected == 1:
            self.accept()
            self.result = ("filters", None)
        else:
            new_filename, ok = QInputDialog.getText(self, "Сохранить как", "Введите имя нового файла:")
            if ok and new_filename:
                new_filename = new_filename + ".jpg"
                self.accept()
                self.result = (new_filename, selected)
            else:
                self.result = None


class Second_Window(QWidget):
    def __init__(self):
        super().__init__()
        self.preview_window = None
        self.selected_folder = None
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 600, 450)
        self.setWindowTitle('Добавить фото')
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        self.button_open_folder = QPushButton("Открыть папку")
        self.button_open_folder.clicked.connect(self.open_folder)
        self.button_add_gallery = QPushButton("Добавить в галерею")
        self.button_add_gallery.clicked.connect(self.add_to_gallery)
        top_layout.addWidget(self.button_open_folder)
        top_layout.addStretch()
        top_layout.addWidget(self.button_add_gallery)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.preview_image)
        bottom_layout = QHBoxLayout()
        self.button_delete = QPushButton("Удалить")
        self.button_delete.clicked.connect(self.delete_selected_photo)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.button_delete)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с изображениями")
        if folder_path:
            self.selected_folder = folder_path
            self.list_widget.clear()
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
            for file in files:
                self.list_widget.addItem(file)

    def preview_image(self, item):
        if not self.selected_folder:
            return
        image_path = os.path.join(self.selected_folder, item.text())
        if not self.preview_window:
            self.preview_window = PreviewWindow()
        self.preview_window.show_image(image_path)
    
    def delete_selected_photo(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите фотографию для удаления")
            return
        self.list_widget.takeItem(self.list_widget.row(selected_item))


    def add_to_gallery(self):
        if not self.selected_folder or self.list_widget.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку с фотографиями")
            return

        dialog = AddTitleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            title, description, title_date, title_location = data["title"], data["description"], data["date"], data["location"]

            if not title or not title_date:
                QMessageBox.warning(self, "Ошибка", "Заголовок и дата обязательны")
                return

            cursor.execute('PRAGMA foreign_keys = ON;')

            cursor.execute("""
                INSERT OR REPLACE INTO titles (title, description, title_date, title_location)
                VALUES (?, ?, ?, ?)
            """, (title, description, title_date, title_location))
            conn.commit()

            cursor.execute("SELECT id FROM titles WHERE title = ?", (title,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.critical(self, "Ошибка", "Не удалось получить ID заголовка")
                return
            title_id = row[0]

            if not os.path.exists(GALLERY_DIR):
                os.makedirs(GALLERY_DIR)

            for i in range(self.list_widget.count()):
                file_name = self.list_widget.item(i).text()
                src_path = os.path.join(self.selected_folder, file_name)
                dst_path = os.path.join(GALLERY_DIR, file_name)

                try:
                    shutil.copy2(src_path, dst_path)
                    cursor.execute("""
                        INSERT OR IGNORE INTO photos (file_name, photo_date, title_id, comment)
                        VALUES (?, ?, ?, ?)
                    """, (file_name, title_date, title_id, ""))
                except Exception as e:
                    print(f"Ошибка копирования или записи для файла {file_name}: {e}")

            conn.commit()
            QMessageBox.information(self, "Успех", f"Фотографии добавлены с заголовком '{title}'")

class PhotoCommentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Предпросмотр и комментарий")
        self.resize(600, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.scroll_area = QScrollArea()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.text_edit = QTextEdit()
        self.layout.addWidget(QLabel("Комментарий:"))
        self.layout.addWidget(self.text_edit)

        self.save_button = QPushButton("Записать комментарий")
        self.save_button.clicked.connect(self.save_comment)
        self.layout.addWidget(self.save_button)

        self.current_file = None
        self.save_callback = None

    def update_photo(self, image_path, comment, file_name, save_callback):
        self.current_file = file_name
        self.save_callback = save_callback
        self.text_edit.setPlainText(comment)
        self.show_image(image_path)

    def show_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.label.setPixmap(pixmap.scaled(self.scroll_area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.label.setText("Не удалось загрузить изображение")

    def save_comment(self):
        if self.current_file and self.save_callback:
            new_comment = self.text_edit.toPlainText()
            self.save_callback(new_comment)

class Third_Window(QWidget):
    def __init__(self, conn, cursor, GALLERY_DIR):
        super().__init__()
        self.conn = conn
        self.cursor = cursor
        self.gallery_folder = GALLERY_DIR
        self.preview_window = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Заголовки и фотографии")
        self.setGeometry(350, 350, 600, 400)
        self.layout = QVBoxLayout(self)

        self.title_list = QListWidget()
        self.title_list.itemDoubleClicked.connect(self.on_title_double_clicked)
        self.layout.addWidget(self.title_list)

        self.photos_list = QListWidget()
        self.photos_list.itemDoubleClicked.connect(self.on_photo_double_clicked)
        self.layout.addWidget(self.photos_list)

        button_layout = QHBoxLayout()
        self.delete_photo_button = QPushButton("Удалить фотографию")
        self.delete_photo_button.clicked.connect(self.delete_selected_photo)
        self.delete_session_button = QPushButton("Удалить фотосессию")
        self.delete_session_button.clicked.connect(self.delete_selected_session)
        self.process_button = QPushButton("Обработать изображение")
        self.process_button.clicked.connect(self.open_processing_dialog)

        button_layout.addWidget(self.delete_photo_button)
        button_layout.addWidget(self.delete_session_button)
        button_layout.addWidget(self.process_button)
        self.layout.addLayout(button_layout)

        self.load_titles()

    def load_titles(self):
        self.title_list.clear()
        self.cursor.execute("SELECT title, description, title_date, title_location FROM titles ORDER BY title")
        titles = self.cursor.fetchall()
        for title, description, title_date, title_location in titles:
            display_text = f"{title} | {description} | {title_date} | {title_location}"
            self.title_list.addItem(display_text)

    def on_title_double_clicked(self, item):
        title = item.text().split(" | ")[0]
        self.photos_list.clear()
        self.cursor.execute("SELECT file_name FROM photos WHERE title_id = (SELECT id FROM titles WHERE title = ?) ORDER BY file_name", (title,))
        photos = self.cursor.fetchall()
        if not photos:
            self.photos_list.addItem("Фотографии с таким заголовком отсутствуют")
            return
        for (file_name,) in photos:
            self.photos_list.addItem(file_name)

    def on_photo_double_clicked(self, item):
        file_name = item.text()
        image_path = os.path.join(self.gallery_folder, file_name)
        self.cursor.execute("SELECT comment FROM photos WHERE file_name = ?", (file_name,))
        comment_row = self.cursor.fetchone()
        current_comment = comment_row[0] if comment_row and comment_row[0] else ""

        def save_callback(new_comment):
            self.cursor.execute("UPDATE photos SET comment = ? WHERE file_name = ?", (new_comment, file_name))
            self.conn.commit()

        if not hasattr(self, 'photo_comment_window') or not self.photo_comment_window.isVisible():
            self.photo_comment_window = PhotoCommentWindow()
        self.photo_comment_window.update_photo(image_path, current_comment, file_name, save_callback)
        self.photo_comment_window.show()


    def delete_selected_photo(self):
        selected_item = self.photos_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите фотографию")
            return
        filename = selected_item.text()
        filepath = os.path.join(self.gallery_folder, filename)
        self.cursor.execute("DELETE FROM photos WHERE file_name=?", (filename,))
        self.conn.commit()
        if os.path.exists(filepath):
            os.remove(filepath)
        self.photos_list.takeItem(self.photos_list.row(selected_item))


    def delete_selected_session(self):
        selected_item = self.title_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите фотосессию для удаления")
            return
        title = selected_item.text().split(" | ")[0]
        self.cursor.execute("SELECT file_name FROM photos WHERE title_id = (SELECT id FROM titles WHERE title = ?)", (title,))
        photos = self.cursor.fetchall()
        for (file_name,) in photos:
            file_path = os.path.join(self.gallery_folder, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        self.cursor.execute("DELETE FROM photos WHERE title_id = (SELECT id FROM titles WHERE title = ?)", (title,))
        self.cursor.execute("DELETE FROM titles WHERE title = ?", (title,))
        self.conn.commit()
        self.load_titles()
        self.photos_list.clear()
    
    def open_processing_dialog(self):
        selected_item = self.photos_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите изображение")
            return
        filename = selected_item.text()
        src_path = os.path.join(self.gallery_folder, filename)
        if not os.path.exists(src_path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        self.cursor.execute("SELECT photo_date, title_id, comment FROM photos WHERE file_name=?", (filename,))
        row = self.cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить данные")
            return
        photo_date, title_id, comment = row

        dialog = ProcessingDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.result
            if result[0] == "filters":
                filter_dialog = FilterSelectionDialog(self)
                if filter_dialog.exec() == QDialog.DialogCode.Accepted:
                    filter_name = filter_dialog.filter_combo.currentText()
                    preview_dialog = FilterPreviewDialog(src_path, filter_name, self)
                    if preview_dialog.exec() == QDialog.DialogCode.Accepted:
                        new_filename = preview_dialog.new_filename
                        dst_path = os.path.join(self.gallery_folder, new_filename)
                        self.cursor.execute("INSERT INTO photos (file_name, photo_date, title_id, comment) VALUES (?, ?, ?, ?)",
                                            (new_filename, photo_date, title_id, comment))
                        self.conn.commit()
                        QMessageBox.information(self, "Готово", f"Файл {new_filename} добавлен")
                        self.on_title_double_clicked(self.title_list.currentItem())
            else:
                new_filename, process_type = result
                dst_path = os.path.join(self.gallery_folder, new_filename)
                if process_type == 0: 
                    grayscale_image(src_path, dst_path)
                    self.cursor.execute("INSERT INTO photos (file_name, photo_date, title_id, comment) VALUES (?, ?, ?, ?)",
                                        (new_filename, photo_date, title_id, comment))
                    self.conn.commit()
                    QMessageBox.information(self, "Готово", f"Файл {new_filename} добавлен")
                    self.on_title_double_clicked(self.title_list.currentItem())
                else:
                    return

class First_Window(QWidget):
    def __init__(self, conn, cursor):
        super().__init__()
        self.conn = conn
        self.cursor = cursor
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 500, 400, 400)
        self.setWindowTitle('Первое окно')
        self.button_1 = QPushButton(self)
        self.button_1.resize(150, 150)
        self.button_1.move(25, 110)
        self.button_1.clicked.connect(self.Second_Window)
        self.button_1.setText("Добавить фото")
        self.button_2 = QPushButton(self)
        self.button_2.resize(150, 150)
        self.button_2.move(225, 110)
        self.button_2.clicked.connect(self.Third_Window)
        self.button_2.setText("Открыть свои фото")

    def Second_Window(self):
        self.second_window = Second_Window()
        self.second_window.show()

    def Third_Window(self):
        self.third_window = Third_Window(self.conn, self.cursor, GALLERY_DIR)
        self.third_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = First_Window(conn, cursor)
    ex.show()
    sys.exit(app.exec())
