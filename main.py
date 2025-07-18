# main.py
import sys
import os
import re
from datetime import datetime
from collections import deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QCompleter, QMessageBox, QScrollArea,
    QDialog, QListWidget, QInputDialog, QListWidgetItem, QComboBox,
    QMenu, QLabel, QAbstractItemView, QFileDialog,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSettings, QSize, QStringListModel, QTimer
from PySide6.QtGui import QAction, QIcon

import database

# <<< HistoryLineEdit 和 InputRow 类 (无变化) >>>
class HistoryLineEdit(QLineEdit):
    def __init__(self, history_key, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.history_key = history_key
        self.history = deque(self.settings.value(self.history_key, []), maxlen=5)
    def add_to_history(self, text):
        if not text: return
        if text in self.history: self.history.remove(text)
        self.history.appendleft(text)
        self.settings.setValue(self.history_key, list(self.history))

class InputRow(QWidget):
    delete_requested = Signal(object)
    add_new_value_row = Signal(object)
    def __init__(self, row_type="PRIMARY", main_window=None):
        super().__init__()
        self.main_window = main_window
        self.row_type = row_type
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        if self.row_type == "PRIMARY":
            self.key_input = HistoryLineEdit("key_history")
            self.key_input.setPlaceholderText("输入或选择 键 (Key)")
            self.key_completer = QCompleter(self.main_window.key_model, self)
            self.key_input.setCompleter(self.key_completer)
            self.layout.addWidget(self.key_input)
        else:
            spacer = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            self.layout.addSpacerItem(spacer)
            self.separator_input = HistoryLineEdit("separator_history")
            self.separator_input.setPlaceholderText("符")
            self.separator_input.setFixedWidth(40)
            self.separator_input.setText(",")
            self.layout.addWidget(self.separator_input)
        self.value_input = HistoryLineEdit("value_history")
        self.value_input.setPlaceholderText("输入或选择 值 (Value)")
        self.value_completer = QCompleter(self.main_window.value_model, self)
        self.value_input.setCompleter(self.value_completer)
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(24, 24)
        self.delete_btn = QPushButton("X")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        self.layout.addWidget(self.value_input)
        self.layout.addWidget(self.add_btn)
        self.layout.addWidget(self.delete_btn)
        for completer in [getattr(self, 'key_completer', None), self.value_completer]:
            if completer:
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setMaxVisibleItems(20)
        if self.row_type == "PRIMARY":
            self.key_input.editingFinished.connect(lambda: self.key_input.add_to_history(self.key_input.text()))
        self.value_input.editingFinished.connect(lambda: self.value_input.add_to_history(self.value_input.text()))
        self.add_btn.clicked.connect(lambda: self.add_new_value_row.emit(self))
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
    def get_data(self):
        if hasattr(self, 'key_input'):
            return ("PRIMARY", self.key_input.text().strip(), self.value_input.text().strip())
        else:
            return ("SECONDARY", self.separator_input.text(), self.value_input.text().strip())

# <<< DataManagerWidget (回归到 QListWidget) >>>
class DataManagerWidget(QWidget):
    data_changed = Signal()
    def __init__(self, title, table_name, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.settings = QSettings()
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.search_box = QLineEdit(placeholderText=f"搜索{title}...")
        self.sort_btn = QPushButton("排序")
        self.sort_menu = QMenu()
        self.sort_btn.setMenu(self.sort_menu)
        top_layout.addWidget(self.search_box)
        top_layout.addWidget(self.sort_btn)
        
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setToolTip("双击编辑，右键删除，拖动排序")
        
        layout.addLayout(top_layout)
        layout.addWidget(self.list_widget)
        
        self.setup_sort_menu()
        self.connect_signals()
        self.populate_list()

    def setup_sort_menu(self):
        self.sort_menu.addAction("手动排序", lambda: self.set_sort_order("sort_order"))
        self.sort_menu.addAction("按字母升序", lambda: self.set_sort_order("alpha_asc"))
        self.sort_menu.addAction("按字母降序", lambda: self.set_sort_order("alpha_desc"))

    def set_sort_order(self, order):
        self.settings.setValue(f"sort_order/{self.table_name}", order)
        self.settings.sync()
        self.populate_list()

    def connect_signals(self):
        self.list_widget.itemDoubleClicked.connect(self.edit_item)
        self.search_box.textChanged.connect(self.filter_list)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)

    def on_rows_moved(self, parent, start, end, destination, row):
        if self.settings.value(f"sort_order/{self.table_name}", "sort_order") == "sort_order":
            QTimer.singleShot(0, self.update_db_sort_order)

    def populate_list(self):
        order = self.settings.value(f"sort_order/{self.table_name}", "sort_order")
        self.list_widget.setDragEnabled(order == "sort_order")
        
        self.list_widget.clear()
        for item_id, item_text, _, is_group, _ in database.get_all_items(self.table_name, order):
            if not is_group:
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, item_id)
                self.list_widget.addItem(item)

    def update_db_sort_order(self):
        id_order = [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]
        database.update_sort_order(self.table_name, id_order)
        self.data_changed.emit()

    def filter_list(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def show_context_menu(self, pos):
        menu = QMenu()
        add_item_action = menu.addAction("添加新项...")
        item = self.list_widget.itemAt(pos)
        if item:
            menu.addSeparator()
            delete_action = menu.addAction("删除该项")
        else:
            delete_action = None
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == add_item_action: self.add_item()
        elif action == delete_action and item: self.delete_item(item)

    def add_item(self):
        text, ok = QInputDialog.getText(self, "添加新项", "请输入内容:")
        if ok and text:
            success, msg = database.add_item(self.table_name, text)
            if success:
                self.populate_list()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "错误", msg)

    def edit_item(self, item):
        item_id = item.data(Qt.UserRole)
        old_text = item.text()
        new_text, ok = QInputDialog.getText(self, "编辑项", "请输入新内容:", text=old_text)
        if ok and new_text and new_text != old_text:
            success, msg = database.update_item_text(self.table_name, item_id, new_text)
            if success:
                item.setText(new_text)
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "错误", msg)

    def delete_item(self, item):
        item_id = item.data(Qt.UserRole)
        if QMessageBox.question(self, "确认删除", f"确定要删除 '{item.text()}' 吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            # 注意：这里不再是递归删除
            success, msg = database.delete_item(self.table_name, item_id)
            if success:
                self.populate_list()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "错误", msg)

class ManagementDialog(QDialog):
    data_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据管理")
        self.setMinimumSize(700, 500)
        main_layout = QVBoxLayout(self)
        data_layout = QHBoxLayout()
        self.keys_manager = DataManagerWidget("键", "keys")
        self.values_manager = DataManagerWidget("值", "value_items")
        data_layout.addWidget(self.keys_manager)
        data_layout.addWidget(self.values_manager)
        io_layout = QHBoxLayout()
        self.export_btn = QPushButton("导出为md")
        self.import_btn = QPushButton("导入为md")
        io_layout.addStretch()
        io_layout.addWidget(self.export_btn)
        io_layout.addWidget(self.import_btn)
        io_layout.addStretch()
        main_layout.addLayout(data_layout)
        main_layout.addLayout(io_layout)
        self.keys_manager.data_changed.connect(self.data_changed.emit)
        self.values_manager.data_changed.connect(self.data_changed.emit)
        self.export_btn.clicked.connect(self.export_to_md)
        self.import_btn.clicked.connect(self.import_from_md)
    def export_to_md(self):
        file_name = f"QuickKV导出-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
        path, _ = QFileDialog.getSaveFileName(self, "导出为 Markdown", file_name, "Markdown Files (*.md)")
        if not path: return
        content = f"# QuickKV 数据导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for title, manager in [("键 (Keys)", self.keys_manager), ("值 (Values)", self.values_manager)]:
            content += f"## --- {title} ---\n\n"
            for i in range(manager.list_widget.count()):
                item = manager.list_widget.item(i)
                content += f"- {item.text()}\n"
            content += "\n"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "成功", f"数据已成功导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出文件失败: {e}")
    def import_from_md(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入 Markdown 文件", "", "Markdown Files (*.md)")
        if not path: return
        reply = QMessageBox.question(self, "确认导入", "此操作将完全覆盖当前所有的键和值，且不可撤销。\n是否继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            keys_data, values_data = self.parse_md_content(lines)
            database.replace_all_items("keys", keys_data)
            database.replace_all_items("value_items", values_data)
            self.keys_manager.populate_list()
            self.values_manager.populate_list()
            self.data_changed.emit()
            QMessageBox.information(self, "成功", "数据导入成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入文件失败: {e}")
    def parse_md_content(self, lines):
        keys_data, values_data = [], []
        current_list = None
        for line in lines:
            if line.startswith("## --- 键"):
                current_list = keys_data
                continue
            elif line.startswith("## --- 值"):
                current_list = values_data
                continue
            if current_list is None or not line.strip().startswith('-'):
                continue
            text = line.strip()[1:].strip()
            if text:
                current_list.append((text, 0, 0, len(current_list)))
        return keys_data, values_data

# <<< 主窗口 (与上一版完全相同，此处省略) >>>
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.setOrganizationName("MyCompany")
        QApplication.setApplicationName("QuickKV")
        self.settings = QSettings()
        self.management_dialog = None
        self.setWindowTitle("QuickKV")
        self.key_model = QStringListModel(self)
        self.value_model = QStringListModel(self)
        self.current_layout_name = ""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        top_bar_layout = QHBoxLayout()
        self.layout_combo = QComboBox()
        self.layout_manage_btn = QPushButton("管理组合")
        self.confirm_button = QPushButton("确定 (复制)")
        self.manage_button = QPushButton("管理数据")
        self.add_group_button = QPushButton("添加新键组 (+)")
        top_bar_layout.addWidget(QLabel("组合:"))
        top_bar_layout.addWidget(self.layout_combo)
        top_bar_layout.addWidget(self.layout_manage_btn)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.manage_button)
        top_bar_layout.addWidget(self.confirm_button)
        self.main_layout.addLayout(top_bar_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.addWidget(self.add_group_button)
        self.rows_layout.addStretch()
        scroll_area.setWidget(self.rows_container)
        self.add_group_button.clicked.connect(lambda: self.add_new_row(row_type="PRIMARY"))
        self.confirm_button.clicked.connect(self.process_and_copy)
        self.manage_button.clicked.connect(self.open_management_dialog)
        self.layout_combo.currentIndexChanged.connect(self.on_layout_switch)
        self.layout_manage_btn.clicked.connect(self.manage_layouts)
        self.on_data_changed()
        self.load_layouts()
        self.load_window_settings()
    def on_data_changed(self):
        self.key_model.setStringList([k[1] for k in database.get_all_items("keys")])
        self.value_model.setStringList([v[1] for v in database.get_all_items("value_items")])
    def on_layout_switch(self, index):
        if index == -1 or self.layout_combo.signalsBlocked(): return
        new_layout_name = self.layout_combo.currentText()
        if self.current_layout_name and self.current_layout_name != new_layout_name:
            self.save_current_layout_rows()
        self.current_layout_name = new_layout_name
        self.setWindowTitle(f"QuickKV - {self.current_layout_name}")
        self.load_layout_rows()
    def manage_layouts(self):
        self.save_current_layout_rows()
        self.settings.sync()
        layouts = self.settings.value("layouts", ["默认组合"])
        current_name = self.layout_combo.currentText()
        menu = QMenu()
        add_action = menu.addAction("添加新组合...")
        rename_action = menu.addAction("重命名当前组合...")
        if len(layouts) > 1 and current_name != "默认组合":
            delete_action = menu.addAction("删除当前组合...")
        else: delete_action = None
        action = menu.exec(self.layout_manage_btn.mapToGlobal(self.layout_manage_btn.rect().bottomLeft()))
        if action == add_action:
            text, ok = QInputDialog.getText(self, "添加新组合", "请输入新组合名称:")
            if ok and text and text not in layouts:
                layouts.append(text)
                self.settings.setValue("layouts", layouts)
                self.load_layouts(new_layout_to_select=text)
        elif action == rename_action:
            if current_name == "默认组合":
                QMessageBox.information(self, "提示", "无法重命名“默认组合”。")
                return
            new_name, ok = QInputDialog.getText(self, "重命名组合", "请输入新的组合名称:", text=current_name)
            if ok and new_name and new_name != current_name and new_name not in layouts:
                layouts[layouts.index(current_name)] = new_name
                self.settings.setValue("layouts", layouts)
                self.settings.setValue(f"layout_rows/{new_name}", self.settings.value(f"layout_rows/{current_name}"))
                self.settings.remove(f"layout_rows/{current_name}")
                self.load_layouts(new_layout_to_select=new_name)
        elif action == delete_action:
            if QMessageBox.question(self, "确认删除", f"确定要删除组合 '{current_name}' 吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                layouts.remove(current_name)
                self.settings.setValue("layouts", layouts)
                self.settings.remove(f"layout_rows/{current_name}")
                self.load_layouts()
        self.settings.sync()
    def closeEvent(self, event):
        self.save_current_layout_rows()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("current_layout", self.layout_combo.currentText())
        self.settings.sync()
        super().closeEvent(event)
    def add_new_row(self, row_type="PRIMARY", key="", value="", separator=",", insert_after_widget=None):
        row = InputRow(row_type=row_type, main_window=self)
        if row_type == "PRIMARY":
            row.key_input.setText(key)
            row.value_input.setText(value)
        else:
            row.separator_input.setText(separator)
            row.value_input.setText(value)
        row.delete_requested.connect(self.delete_row)
        row.add_new_value_row.connect(self.add_secondary_row)
        if insert_after_widget:
            index = self.rows_layout.indexOf(insert_after_widget)
            self.rows_layout.insertWidget(index + 1, row)
        else:
            self.rows_layout.insertWidget(self.rows_layout.count() - 2, row)
    def add_secondary_row(self, sender_widget):
        index = self.rows_layout.indexOf(sender_widget)
        while index + 1 < self.rows_layout.count() - 2:
            next_widget = self.rows_layout.itemAt(index + 1).widget()
            if isinstance(next_widget, InputRow) and next_widget.row_type == "SECONDARY":
                index += 1
            else:
                break
        self.add_new_row(row_type="SECONDARY", insert_after_widget=self.rows_layout.itemAt(index).widget())
    def open_management_dialog(self):
        if self.management_dialog is None or not self.management_dialog.isVisible():
            self.management_dialog = ManagementDialog(self)
            self.management_dialog.data_changed.connect(self.on_data_changed)
            self.management_dialog.show()
        self.management_dialog.activateWindow()
    def delete_row(self, row_widget):
        if row_widget.row_type == "PRIMARY":
            start_index = self.rows_layout.indexOf(row_widget)
            row_widget.deleteLater()
            while start_index < self.rows_layout.count() - 2:
                widget = self.rows_layout.itemAt(start_index).widget()
                if isinstance(widget, InputRow) and widget.row_type == "SECONDARY":
                    widget.deleteLater()
                else:
                    break
        else:
            row_widget.deleteLater()
    def process_and_copy(self):
        output_text = []
        current_group = None
        for i in range(self.rows_layout.count()):
            widget = self.rows_layout.itemAt(i).widget()
            if not isinstance(widget, InputRow): continue
            row_type, data1, data2 = widget.get_data()
            if row_type == "PRIMARY":
                if current_group and current_group["key"]:
                    values_str = current_group["values"][0]
                    for j, val in enumerate(current_group["values"][1:]):
                        sep = current_group["separators"][j]
                        values_str += f"{sep}{val}"
                    output_text.append(f"{current_group['key']} {values_str}")
                if data1 and data2:
                    current_group = {"key": data1, "values": [data2], "separators": []}
                    widget.key_input.add_to_history(data1)
                    widget.value_input.add_to_history(data2)
                else:
                    current_group = None
            elif row_type == "SECONDARY" and current_group:
                if data2:
                    current_group["values"].append(data2)
                    current_group["separators"].append(data1)
                    widget.value_input.add_to_history(data2)
                    widget.separator_input.add_to_history(data1)
        if current_group and current_group["key"]:
            values_str = current_group["values"][0]
            for i, val in enumerate(current_group["values"][1:]):
                sep = current_group["separators"][i]
                values_str += f"{sep}{val}"
            output_text.append(f"{current_group['key']} {values_str}")
        if not output_text: QMessageBox.information(self, "提示", "没有可复制的内容。"); return
        QApplication.clipboard().setText("\n".join(output_text))
        QMessageBox.information(self, "成功", f"内容已复制到剪贴板！")
    def load_layout_rows(self):
        self.clear_all_rows()
        rows_data = self.settings.value(f"layout_rows/{self.current_layout_name}", [])
        if rows_data:
            for row_data in rows_data:
                if len(row_data) == 3:
                    self.add_new_row(row_type=row_data[0], key=row_data[1], value=row_data[2])
                elif len(row_data) == 4:
                    self.add_new_row(row_type=row_data[0], separator=row_data[1], value=row_data[2])
        else:
            self.add_new_row(row_type="PRIMARY")
    def save_current_layout_rows(self):
        if not hasattr(self, 'current_layout_name') or not self.current_layout_name: return
        rows_data = []
        for i in range(self.rows_layout.count()):
            widget = self.rows_layout.itemAt(i).widget()
            if isinstance(widget, InputRow):
                rows_data.append(widget.get_data())
        self.settings.setValue(f"layout_rows/{self.current_layout_name}", rows_data)
    def load_window_settings(self):
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))
    def load_layouts(self, new_layout_to_select=None):
        self.layout_combo.blockSignals(True)
        self.layout_combo.clear()
        layouts = self.settings.value("layouts", ["默认组合"])
        if not layouts: layouts = ["默认组合"]
        if "默认组合" not in layouts: layouts.insert(0, "默认组合")
        self.settings.setValue("layouts", list(dict.fromkeys(layouts)))
        self.layout_combo.addItems(layouts)
        name_to_select = new_layout_to_select or self.settings.value("current_layout", "默认组合")
        # <<< BUGFIX: 修正此处的错误 >>>
        index = self.layout_combo.findText(name_to_select)
        if index == -1: index = 0
        self.layout_combo.setCurrentIndex(index)
        self.layout_combo.blockSignals(False)
        self.on_layout_switch(index)
    def clear_all_rows(self):
        while self.rows_layout.count() > 2:
            item = self.rows_layout.itemAt(0)
            if item and item.widget(): item.widget().deleteLater()
            self.rows_layout.takeAt(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    database.ensure_db_tables()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
