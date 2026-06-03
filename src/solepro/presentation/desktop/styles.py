"""
Стили для десктопного приложения.
"""
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .ui_settings import DesktopUiSettings


def apply_style(app: QApplication) -> None:
    """
    Применить стили к приложению.
    
    Args:
        app: Экземпляр QApplication
    """
    # Устанавливаем тему Fusion
    app.setStyle("Fusion")
    
    # Создаем и настраиваем палитру
    palette = QPalette()
    
    # Основные цвета
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f9f9f9"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#333333"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#4CAF50"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4CAF50"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    
    # Дополнительные цвета
    palette.setColor(QPalette.ColorRole.Light, QColor("#e8f5e9"))
    palette.setColor(QPalette.ColorRole.Midlight, QColor("#c8e6c9"))
    palette.setColor(QPalette.ColorRole.Dark, QColor("#2e7d32"))
    palette.setColor(QPalette.ColorRole.Mid, QColor("#66bb6a"))
    palette.setColor(QPalette.ColorRole.Shadow, QColor("#1b5e20"))
    
    # Цвета для disabled состояний
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#aaaaaa"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#aaaaaa"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#aaaaaa"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor("#666666"))
    
    # Применяем палитру
    app.setPalette(palette)

    ui_settings = DesktopUiSettings(__file__, project_root_parent_index=4)
    table_font_family = ui_settings.get_str("table_font_family", "Segoe UI")
    table_font_size = ui_settings.get_int("table_font_size", 11)
    table_header_font_family = ui_settings.get_str("table_header_font_family", table_font_family)
    table_header_font_size = ui_settings.get_int("table_header_font_size", table_font_size)
    
    # Дополнительные стили через QSS
    style_sheet = """
        /* === ОСНОВНЫЕ СТИЛИ === */
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QWidget {
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 11pt;
            color: #333333;
        }
        
        /* === ТАБЛИЦЫ === */
        QTableWidget {
            background-color: white;
            alternate-background-color: #f9f9f9;
            gridline-color: #e0e0e0;
            selection-background-color: #c8e6c9;
            selection-color: #1b5e20;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-family: "__TABLE_FONT_FAMILY__";
            font-size: __TABLE_FONT_SIZE__pt;
        }

        QTableView {
            font-family: "__TABLE_FONT_FAMILY__";
            font-size: __TABLE_FONT_SIZE__pt;
        }
        
        QTableWidget::item, QTableView::item {
            padding: 6px 8px;
            border: none;
        }
        
        QTableWidget::item:selected, QTableView::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        QTableWidget QHeaderView::section, QTableView QHeaderView::section {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 10px 8px;
            border: 1px solid #45a049;
            font-family: "__TABLE_HEADER_FONT_FAMILY__";
            font-size: __TABLE_HEADER_FONT_SIZE__pt;
        }
        
        QTableWidget QHeaderView::section:checked, QTableView QHeaderView::section:checked {
            background-color: #2e7d32;
        }
        
        /* === КНОПКИ === */
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            border-radius: 4px;
            font-size: 11pt;
            min-width: 100px;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
            padding-top: 11px;
            padding-bottom: 9px;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QPushButton#danger {
            background-color: #f44336;
        }
        
        QPushButton#danger:hover {
            background-color: #d32f2f;
        }
        
        QPushButton#warning {
            background-color: #ff9800;
        }
        
        QPushButton#warning:hover {
            background-color: #f57c00;
        }
        
        /* === ПОЛЯ ВВОДА === */
        QLineEdit, QTextEdit, QPlainTextEdit {
            padding: 8px;
            border: 2px solid #cccccc;
            border-radius: 4px;
            background-color: white;
            font-size: 11pt;
            min-height: 30px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #4CAF50;
        }
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
            background-color: #f5f5f5;
            border-color: #e0e0e0;
            color: #999999;
        }
        
        /* === ВЫПАДАЮЩИЕ СПИСКИ === */
        QComboBox {
            padding: 8px;
            border: 2px solid #cccccc;
            border-radius: 4px;
            background-color: white;
            font-size: 11pt;
            min-height: 30px;
        }
        
        QComboBox:focus {
            border-color: #4CAF50;
        }
        
        QComboBox:disabled {
            background-color: #f5f5f5;
            border-color: #e0e0e0;
            color: #999999;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left: 1px solid #cccccc;
            background-color: #f5f5f5;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #666666;
            width: 0;
            height: 0;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid #cccccc;
            background-color: white;
            selection-background-color: #4CAF50;
            selection-color: white;
            padding: 4px;
            border-radius: 4px;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item {
            min-height: 28px;
            padding: 6px 12px;
            color: #333333;
            border-radius: 2px;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        
        QComboBox QAbstractItemView::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        /* === ГРУППЫ И РАМКИ === */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #4CAF50;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px 0 6px;
            background-color: white;
            color: #2e7d32;
        }
        
        QFrame {
            border: none;
        }

        QFrame#line {
            border: 1px solid #e0e0e0;
        }

        QTextEdit, QPlainTextEdit {
            border: 2px solid #cccccc;
            border-radius: 4px;
        }

        QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #4CAF50;
        }

        QTextEdit:disabled, QPlainTextEdit:disabled {
            border-color: #e0e0e0;
        }
        
        /* === МЕНЮ === */
        QMenuBar {
            background-color: white;
            padding: 2px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 12px;
            border-radius: 4px;
            color: #333333;
        }
        
        QMenuBar::item:selected {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        
        QMenuBar::item:pressed {
            background-color: #c8e6c9;
        }
        
        QMenu {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 4px;
        }
        
        QMenu::item {
            padding: 8px 24px 8px 16px;
            color: #333333;
            background-color: transparent;
            border-radius: 3px;
        }
        
        QMenu::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #e0e0e0;
            margin: 4px 8px;
        }
        
        /* === ПАНЕЛЬ ИНСТРУМЕНТОВ === */
        QToolBar {
            background-color: white;
            border-bottom: 1px solid #e0e0e0;
            padding: 4px;
            spacing: 4px;
        }
        
        QToolBar QToolButton {
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QToolBar QToolButton:hover {
            background-color: #e8f5e9;
        }
        
        QToolBar QToolButton:pressed {
            background-color: #c8e6c9;
        }
        
        /* === СТАТУС БАР === */
        QStatusBar {
            background-color: #e8f5e9;
            color: #1b5e20;
            font-weight: bold;
            padding: 4px 8px;
            border-top: 1px solid #c8e6c9;
        }
        
        /* === ДИАЛОГИ === */
        QDialog {
            background-color: white;
        }
        
        QDialog QLabel {
            font-size: 11pt;
        }
        
        QDialog QPushButton {
            min-width: 80px;
        }
        
        /* === СООБЩЕНИЯ И УВЕДОМЛЕНИЯ === */
        QMessageBox {
            background-color: white;
        }
        
        QMessageBox QLabel {
            font-size: 12pt;
        }
        
        /* === ПРОГРЕСС БАР === */
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: white;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        
        /* === ВКЛАДКИ === */
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: white;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #e8f5e9;
            color: #1b5e20;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        
        QTabBar::tab:hover {
            background-color: #c8e6c9;
        }
        
        /* === СПИСКИ === */
        QListWidget {
            background-color: white;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 2px;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 3px;
        }
        
        QListWidget::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #e8f5e9;
        }
        
        /* === ДЕРЕВЬЯ === */
        QTreeWidget {
            background-color: white;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        
        QTreeWidget::item {
            padding: 6px;
        }
        
        QTreeWidget::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        QTreeWidget::item:hover {
            background-color: #e8f5e9;
        }
    """
    style_sheet = style_sheet.replace("__TABLE_FONT_FAMILY__", table_font_family)
    style_sheet = style_sheet.replace("__TABLE_FONT_SIZE__", str(table_font_size))
    style_sheet = style_sheet.replace("__TABLE_HEADER_FONT_FAMILY__", table_header_font_family)
    style_sheet = style_sheet.replace("__TABLE_HEADER_FONT_SIZE__", str(table_header_font_size))
    app.setStyleSheet(style_sheet)
