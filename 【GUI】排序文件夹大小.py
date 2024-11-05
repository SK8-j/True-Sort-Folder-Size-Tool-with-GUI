import sys
import os
import shutil
import platform
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget,\
                            QVBoxLayout, QTableWidget, QTableWidgetItem, \
                            QLineEdit, QPushButton, QFileDialog, \
                            QAbstractItemView, QMenu, QAction, QToolTip
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QColor
from PyQt5.QtGui import QCursor

class FolderSizeTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("文件夹大小排序工具")
        self.setGeometry(100, 100, 800, 600)

        self.folder_path = ""
        self.folder_data = []  # 存储文件夹及其大小数据

        self.sort_order = Qt.DescendingOrder  # 排序顺序，默认为降序

        self.current_hovered_row = -1
        self.current_hovered_column = -1

        # UI布局
        self.init_ui()


    def init_ui(self):
        # 主窗口的中央小部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 输入路径框
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("拖拽或输入路径")
        layout.addWidget(self.path_input)

        # 拖拽区
        self.setAcceptDrops(True)

        # 排序按钮
        self.sort_button = QPushButton("从大到小排序", self)
        self.sort_button.setStyleSheet("QPushButton {border-radius: 10px; background-color: #4CAF50; color: white; padding: 10px 20px;} QPushButton:hover {background-color: #45a049;}")
        self.sort_button.clicked.connect(self.sort_folders)
        layout.addWidget(self.sort_button)

        # 表格展示
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)  # 两列: 文件夹/文件名 和 大小
        self.table.setHorizontalHeaderLabels(["文件夹/文件名", "大小 (MB)"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0)  # 文件夹列自适应
        self.table.horizontalHeader().sectionClicked.connect(self.handle_header_click)  # 表头点击事件
        self.table.cellDoubleClicked.connect(self.open_folder)  # 连接双击事件
        layout.addWidget(self.table)

        # 右键菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        row = self.table.rowAt(event.y())
        column = self.table.columnAt(event.x())

        if row != -1 and column != -1:
            # 鼠标进入新的单元格
            if (row != self.current_hovered_row) or (column != self.current_hovered_column):
                # 恢复之前悬浮单元格的背景颜色
                if self.current_hovered_row != -1 and self.current_hovered_column != -1:
                    self.table.item(self.current_hovered_row, self.current_hovered_column).setBackground(QColor(255, 255, 255))  # 恢复为白色背景

                # 设置新的悬浮单元格的背景颜色
                self.table.item(row, column).setBackground(QColor(220, 220, 220))  # 设置为浅灰色背景

                # 更新当前悬浮的单元格
                self.current_hovered_row = row
                self.current_hovered_column = column

                # 显示工具提示
                folder_name = self.table.item(row, 0).text()  # 获取文件夹名称
                folder_size = self.table.item(row, 1).text()  # 获取文件大小
                QToolTip.showText(QCursor.pos(), f"文件夹: {folder_name}\n大小: {folder_size} MB")
        else:
            # 鼠标离开表格区域，恢复背景颜色
            if self.current_hovered_row != -1 and self.current_hovered_column != -1:
                self.table.item(self.current_hovered_row, self.current_hovered_column).setBackground(QColor(255, 255, 255))  # 恢复为白色背景
                self.current_hovered_row = -1
                self.current_hovered_column = -1
                QToolTip.hideText()


    def open_folder(self, row, column):
        """双击打开文件夹"""
        folder_name = self.table.item(row, 0).text()  # 获取文件夹名称
        folder_path = os.path.join(self.folder_path, folder_name)
        folder_path = os.path.normpath(folder_path)  # 规范化路径分隔符
        # print("Opening folder:", folder_path)  # 打印路径以检查是否正确

        if os.path.exists(folder_path):
            # 根据操作系统选择适当的命令
            if platform.system() == "Windows":
                # Windows下调用explorer
                subprocess.Popen(['explorer', folder_path])
            elif platform.system() == "Darwin":
                # macOS下调用open
                subprocess.Popen(['open', folder_path])
            else:
                # Linux下调用xdg-open
                subprocess.Popen(['xdg-open', folder_path])
        else:
            print("Folder path does not exist:", folder_path)

    def handle_header_click(self, index):
        """处理表头点击事件"""
        if index == 0:
            # 按文件夹/文件名排序
            self.folder_data.sort(key=lambda x: x[0], reverse=self.sort_order == Qt.DescendingOrder)
        elif index == 1:
            # 按大小排序
            self.folder_data.sort(key=lambda x: x[1], reverse=self.sort_order == Qt.DescendingOrder)

        # 切换排序顺序
        self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder

        # 更新表格显示
        self.display_folder_data()

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """处理拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            folder_path = urls[0].toLocalFile()
            self.path_input.setText(folder_path)
            self.load_folder_data(folder_path)

    def load_folder_data(self, path):
        """加载文件夹数据并计算大小"""
        self.folder_path = path
        self.folder_data.clear()  # 清空之前的数据
        self.table.setRowCount(0)  # 清空表格

        try:
            # 获取路径下的所有文件和文件夹
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    size = self.get_folder_size(item_path)
                elif os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024 * 1024)  # 转换为MB
                else:
                    continue
                self.folder_data.append((item, size))
            
            self.display_folder_data()  # 显示数据
        except Exception as e:
            print(f"加载文件夹数据失败: {e}")

    def get_folder_size(self, folder):
        """递归计算文件夹的大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)  # 转换为MB

    def display_folder_data(self):
        """将文件夹数据展示在表格中"""
        self.table.setRowCount(len(self.folder_data))
        for i, (name, size) in enumerate(self.folder_data):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{size:.2f}"))

    def sort_folders(self):
        """按文件夹大小排序"""
        self.folder_data.sort(key=lambda x: x[1], reverse=True)
        self.display_folder_data()

    def show_context_menu(self, pos):
        """右键菜单"""
        menu = QMenu(self)

        reset_action = QAction("重置", self)
        reset_action.triggered.connect(self.reset_path)
        menu.addAction(reset_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_path)
        menu.addAction(delete_action)

        menu.exec_(self.table.mapToGlobal(pos))

    def reset_path(self):
        """重置路径和数据"""
        self.path_input.clear()
        self.folder_data.clear()
        self.table.setRowCount(0)

    def delete_path(self):
        """删除路径"""
        try:
            if self.folder_path:
                shutil.rmtree(self.folder_path)
                self.reset_path()
                print(f"已删除路径: {self.folder_path}")
        except Exception as e:
            print(f"删除路径失败: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FolderSizeTool()
    window.show()
    sys.exit(app.exec_())
