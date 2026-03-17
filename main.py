#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardMem Mobile - 艾宾浩斯记忆卡片复习软件（手机版）
基于艾宾浩斯记忆曲线的知识卡片智能复习系统
"""

# 导入并运行Kivy移动版
from mobile_app import CardMemApp
CardMemApp().run()

# ============================================
# 配置常量
# ============================================
# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, "knowledge_cards.json")
TRASH_FILE = os.path.join(DATA_DIR, "trash_cards.json")
DEFAULT_SETTINGS = {
    "daily_limit": 15,
    "mastery_threshold": 4,
    "intervals": [2, 4, 7, 15]  # 艾宾浩斯复习间隔（天）
}

# 颜色方案
COLORS = {
    "primary": "#2C3E50",
    "secondary": "#3498DB",
    "accent": "#E74C3C",
    "background": "#ECF0F1",
    "card_bg": "#FFFFFF",
    "text_main": "#2C3E50",
    "text_secondary": "#7F8C8D",
    "success": "#27AE60",
    "warning": "#F39C12",
    "hover": "#D5DBDB"
}


# ============================================
# 数据管理类
# ============================================
class DataManager:
    """数据管理器 - 负责JSON数据的读取、存储和备份"""

    def __init__(self):
        self.data = self._load_data()
        self.trash_data = self._load_trash_data()

    def _load_trash_data(self) -> dict:
        """加载垃圾站数据"""
        if os.path.exists(TRASH_FILE):
            try:
                with open(TRASH_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载垃圾站数据失败: {e}")
        return {"cards": [], "deleted_history": []}

    def _save_trash_data(self):
        """保存垃圾站数据"""
        try:
            if not os.path.exists(TRASH_FILE):
                with open(TRASH_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.trash_data, f, ensure_ascii=False, indent=2)
            else:
                with open(TRASH_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.trash_data, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            raise PermissionError(f"无法保存垃圾站文件 {TRASH_FILE}: {e}")

    def _load_data(self) -> dict:
        """加载数据文件"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保必要字段存在
                    if "categories" not in data:
                        data["categories"] = {"默认分类": []}
                    # 如果是旧格式（列表），转换为新格式（字典）
                    if isinstance(data["categories"], list):
                        new_cats = {}
                        for cat in data["categories"]:
                            new_cats[cat] = []
                        data["categories"] = new_cats
                    if "cards" not in data:
                        data["cards"] = []
                    if "settings" not in data:
                        data["settings"] = DEFAULT_SETTINGS.copy()
                    # 修复缺少 next_review_date 的卡片
                    today = datetime.now().strftime("%Y-%m-%d")
                    for card in data.get("cards", []):
                        if "next_review_date" not in card:
                            card["next_review_date"] = today
                        if "mastery_count" not in card:
                            card["mastery_count"] = 0
                        if "status" not in card:
                            card["status"] = "new"
                    return data
            except Exception as e:
                print(f"加载数据失败: {e}")
        # 返回默认数据结构
        return {
            "categories": {"默认分类": []},
            "cards": [],
            "settings": DEFAULT_SETTINGS.copy()
        }

    def save_data(self):
        """保存数据到文件"""
        try:
            # 确保目录存在
            data_dir = os.path.dirname(DATA_FILE) or "."
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)

            # 如果文件不存在，先创建（避免Windows权限问题）
            if not os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            else:
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            raise PermissionError(f"无法保存文件 {DATA_FILE}，请检查文件权限或关闭其他程序: {e}")

    def backup(self, filepath: str):
        """备份数据到指定文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def restore(self, filepath: str):
        """从指定文件恢复数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            self.save_data()

    # ----- 卡片操作 -----
    def add_card(self, title: str, category: str, content: str, key_points: List[str] = None,
                 level1_industry: str = None, level2_industry: str = None, level3_industry: str = None) -> dict:
        """添加新卡片"""
        today = datetime.now().strftime("%Y-%m-%d")
        card = {
            "id": str(uuid.uuid4()),
            "title": title,
            "category": category,
            "content": content,
            "key_points": key_points or [],
            "level1_industry": level1_industry or "",
            "level2_industry": level2_industry or "",
            "level3_industry": level3_industry or "",
            "status": "new",  # new, learning, mastered
            "consecutive_remembers": 0,
            "next_review_date": today,
            "review_history": [],
            "created_at": today
        }
        self.data["cards"].append(card)

        # 如果分类不存在，自动添加（支持多级分类格式）
        categories = self.data["categories"]
        if "/" in category:
            # 子行业格式：主行业/子行业
            parts = category.split("/", 1)
            parent = parts[0]
            child = parts[1]
            if parent not in categories:
                categories[parent] = []
            if child not in categories[parent]:
                categories[parent].append(child)
        else:
            # 主行业
            if category not in categories:
                categories[category] = []

        self.save_data()
        return card

    def update_card(self, card_id: str, **kwargs):
        """更新卡片信息"""
        for card in self.data["cards"]:
            if card["id"] == card_id:
                card.update(kwargs)
                self.save_data()
                return True
        return False

    def delete_card(self, card_id: str):
        """删除卡片（移入垃圾站）"""
        # 找到卡片
        card = self.get_card(card_id)
        if card:
            # 添加到垃圾站
            card["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.trash_data["cards"].append(card)
            self._save_trash_data()

            # 从主列表中删除
            self.data["cards"] = [c for c in self.data["cards"] if c["id"] != card_id]
            self.save_data()
            return True
        return False

    def move_to_trash_batch(self, card_ids: List[str]):
        """批量移动卡片到垃圾站"""
        cards_to_trash = []
        for card_id in card_ids:
            card = self.get_card(card_id)
            if card:
                card["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cards_to_trash.append(card)

        if cards_to_trash:
            self.trash_data["cards"].extend(cards_to_trash)
            self._save_trash_data()

            # 从主列表中删除
            self.data["cards"] = [c for c in self.data["cards"] if c["id"] not in card_ids]
            self.save_data()
            return len(cards_to_trash)
        return 0

    # ----- 垃圾站操作 -----
    def get_trash_cards(self) -> List[dict]:
        """获取垃圾站中的所有卡片"""
        return self.trash_data.get("cards", [])

    def restore_card(self, card_id: str) -> bool:
        """从垃圾站恢复卡片"""
        for card in self.trash_data["cards"]:
            if card["id"] == card_id:
                # 移除删除时间戳
                card.pop("deleted_at", None)
                # 恢复到主列表
                self.data["cards"].append(card)
                self.save_data()

                # 从垃圾站中移除
                self.trash_data["cards"] = [c for c in self.trash_data["cards"] if c["id"] != card_id]
                self._save_trash_data()
                return True
        return False

    def restore_trash_batch(self, card_ids: List[str]) -> int:
        """批量从垃圾站恢复卡片"""
        restored_count = 0
        for card_id in card_ids:
            if self.restore_card(card_id):
                restored_count += 1
        return restored_count

    def permanently_delete_card(self, card_id: str) -> bool:
        """彻底删除卡片（从垃圾站中永久删除）"""
        self.trash_data["cards"] = [c for c in self.trash_data["cards"] if c["id"] != card_id]
        self._save_trash_data()
        return True

    def permanently_delete_trash_batch(self, card_ids: List[str]) -> int:
        """批量彻底删除卡片"""
        self.trash_data["cards"] = [c for c in self.trash_data["cards"] if c["id"] not in card_ids]
        self._save_trash_data()
        return len(card_ids)

    def empty_trash(self):
        """清空垃圾站"""
        self.trash_data["cards"] = []
        self._save_trash_data()

    def get_trash_count(self) -> int:
        """获取垃圾站中卡片数量"""
        return len(self.trash_data.get("cards", []))

    def get_card(self, card_id: str) -> Optional[dict]:
        """获取卡片"""
        for card in self.data["cards"]:
            if card["id"] == card_id:
                return card
        return None

    def get_cards_by_category(self, category: str) -> List[dict]:
        """获取指定分类的卡片"""
        if category is None or category == "all":
            return self.data["cards"]

        # 如果是主行业，返回该主行业及其所有子行业的卡片
        if "/" not in category:
            return [c for c in self.data["cards"] if c["category"].startswith(category + "/") or c["category"] == category]

        # 如果是子行业（二级/三级分类），返回该分类及其所有子分类的卡片
        return [c for c in self.data["cards"] if c["category"].startswith(category + "/") or c["category"] == category]

    def get_today_review_cards(self) -> List[dict]:
        """获取今日需要复习的卡片"""
        today = datetime.now().strftime("%Y-%m-%d")
        settings = self.data["settings"]
        daily_limit = settings.get("daily_limit", 15)

        # 筛选需要复习的卡片
        review_cards = [
            c for c in self.data["cards"]
            if c["status"] != "mastered" and c["next_review_date"] <= today
        ]

        # 按下次复习日期排序
        review_cards.sort(key=lambda x: x["next_review_date"])

        return review_cards[:daily_limit]

    # ----- 分类操作 -----
    def get_all_categories(self) -> dict:
        """获取所有分类（树形结构）"""
        return self.data.get("categories", {"默认分类": []})

    def get_flat_categories(self) -> List[str]:
        """获取扁平化的分类列表"""
        result = []
        categories = self.get_all_categories()
        for parent, children in categories.items():
            if parent == "默认分类":
                result.append(parent)
                continue
            result.append(parent)
            if children and isinstance(children, dict):
                for child, grandchildren in children.items():
                    result.append(f"{parent}/{child}")
                    if grandchildren and isinstance(grandchildren, list):
                        for grandchild in grandchildren:
                            result.append(f"{parent}/{child}/{grandchild}")
            elif children and isinstance(children, list):
                # 兼容旧版 list 结构
                for child in children:
                    result.append(f"{parent}/{child}")
        return result

    def add_category(self, parent: str, child: str = None, grandchild: str = None):
        """添加分类

        Args:
            parent: 一级行业名称
            child: 二级行业名称（可选）
            grandchild: 三级行业名称（可选）
        """
        categories = self.data["categories"]

        if grandchild:
            # 添加三级分类
            if parent not in categories:
                categories[parent] = {}
            if not isinstance(categories[parent], dict):
                categories[parent] = {}
            if child not in categories[parent]:
                categories[parent][child] = []
            if grandchild not in categories[parent][child]:
                categories[parent][child].append(grandchild)
        elif child:
            # 添加二级分类
            if parent not in categories:
                categories[parent] = {}
            if not isinstance(categories[parent], dict):
                categories[parent] = {}
            if child not in categories[parent]:
                categories[parent][child] = []
        else:
            # 添加一级分类
            if parent and parent not in categories:
                categories[parent] = {}
        self.save_data()

    def delete_category(self, category: str):
        """删除分类（同时删除该分类下的卡片）"""
        if category == "默认分类":
            return False

        categories = self.data["categories"]

        # 检查是否是三级分类
        if "/" in category:
            parts = category.split("/")
            if len(parts) == 3:
                # 三级分类：一级/二级/三级
                parent, child, grandchild = parts
                if parent in categories and isinstance(categories[parent], dict):
                    if child in categories[parent]:
                        if grandchild in categories[parent][child]:
                            categories[parent][child].remove(grandchild)
                        # 删除该三级分类下的卡片
                        self.data["cards"] = [c for c in self.data["cards"] if c["category"] != category]
                self.save_data()
                return True
            elif len(parts) == 2:
                # 二级分类：一级/二级
                parent, child = parts
                if parent in categories and isinstance(categories[parent], dict):
                    if child in categories[parent]:
                        # 删除该二级分类及其所有三级分类下的卡片
                        to_delete = [category]
                        grandchildren = categories[parent][child]
                        if isinstance(grandchildren, list):
                            for gc in grandchildren:
                                to_delete.append(f"{parent}/{child}/{gc}")
                        del categories[parent][child]
                        self.data["cards"] = [c for c in self.data["cards"] if c["category"] not in to_delete]
                self.save_data()
                return True

        # 如果是一级分类
        if category in categories:
            # 删除该一级分类及其所有子分类下的卡片
            to_delete = [category]
            children = categories.get(category, {})
            if isinstance(children, dict):
                for child, grandchildren in children.items():
                    to_delete.append(f"{category}/{child}")
                    if isinstance(grandchildren, list):
                        for gc in grandchildren:
                            to_delete.append(f"{category}/{child}/{gc}")

            self.data["cards"] = [c for c in self.data["cards"] if c["category"] not in to_delete]
            del categories[category]
            self.save_data()
            return True

        return False

    def delete_categories_batch(self, categories: List[str]):
        """批量删除分类"""
        for cat in categories:
            self.delete_category(cat)

    def rename_category(self, old_name: str, new_name: str):
        """重命名分类"""
        categories = self.data["categories"]

        if old_name in categories:
            # 重命名主行业
            categories[new_name] = categories.pop(old_name)
            # 更新所有相关卡片的分类
            for card in self.data["cards"]:
                if card["category"] == old_name:
                    card["category"] = new_name
        elif "/" in old_name:
            # 重命名子行业
            parts = old_name.split("/")
            parent = parts[0]
            child = parts[1]
            if parent in categories and child in categories[parent]:
                idx = categories[parent].index(child)
                categories[parent][idx] = new_name
                # 更新相关卡片
                for card in self.data["cards"]:
                    if card["category"] == old_name:
                        card["category"] = f"{parent}/{new_name}"

        self.save_data()

    # ----- 设置操作 -----
    def update_settings(self, **kwargs):
        """更新设置"""
        self.data["settings"].update(kwargs)
        self.save_data()

    def get_settings(self) -> dict:
        """获取设置"""
        return self.data["settings"].copy()


# ============================================
# 关键词提取工具
# ============================================
def extract_keywords(content: str) -> List[str]:
    """从内容中自动提取关键词作为待确认重点

    提取规则：
    1. 方法名（带括号的如 append()）
    2. 核心概念（被引号或书名号包围的词）
    3. 常见术语模式
    """
    keywords = []

    # 提取方法名/函数名 pattern: word()
    method_pattern = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)', content)
    keywords.extend(method_pattern[:3])  # 最多取3个

    # 提取被引号包围的词
    quoted = re.findall(r'["""\']([^""\']+)[""\']', content)
    keywords.extend(quoted[:2])

    # 提取被书名号包围的词
    book_title = re.findall(r'《([^》]+)》', content)
    keywords.extend(book_title[:2])

    # 提取常见术语模式
    term_pattern = re.findall(r'\b(\w+曲线|\w+原理|\w+定律|\w+方法|\w+效应)\b', content)
    keywords.extend(term_pattern[:2])

    # 去重并返回
    seen = set()
    result = []
    for kw in keywords:
        kw = kw.strip()
        if kw and kw not in seen and len(kw) > 1:
            seen.add(kw)
            result.append(kw)

    return []  # 不再使用自动提取，改用手动加粗标注


def extract_bold_from_excel_cell(cell) -> List[str]:
    """从Excel单元格中提取加粗文字

    Args:
        cell: openpyxl单元格对象（需要使用rich_text=True加载的worksheet中的单元格）

    Returns:
        加粗文字列表
    """
    if cell is None:
        return []

    bold_words = []

    # 检查单元格是否有富文本内容
    if hasattr(cell, 'value') and cell.value is not None:
        from openpyxl.cell.rich_text import TextBlock, CellRichText

        # 获取单元格的默认字体加粗状态
        cell_default_bold = cell.font.bold if cell.font else False

        # 检查是否是富文本 CellRichText
        if isinstance(cell.value, CellRichText):
            for part in cell.value:
                is_bold = False
                text = None

                if isinstance(part, str):
                    # 普通字符串使用单元格的默认字体
                    is_bold = cell_default_bold
                    text = part
                elif isinstance(part, TextBlock):
                    # TextBlock 有自己的字体设置
                    text = part.text
                    if part.font:
                        is_bold = part.font.b
                    else:
                        # 没有单独字体设置，使用单元格默认字体
                        is_bold = cell_default_bold

                if is_bold and text:
                    bold_words.append(text.strip())
        elif hasattr(cell, 'font') and cell.font and cell.font.bold:
            # 非富文本，整个单元格加粗
            bold_words.append(str(cell.value).strip())

    return bold_words


def extract_bold_from_text_widget(text_widget) -> List[str]:
    """从Text组件中提取加粗文字

    Args:
        text_widget: tk.Text组件

    Returns:
        加粗文字列表（去重，最多5个）
    """
    bold_words = []

    # 遍历所有加粗的tag
    try:
        # 直接获取bold tag的所有范围
        ranges = text_widget.tag_ranges('bold')
        for i in range(0, len(ranges), 2):
            start = ranges[i]
            end = ranges[i + 1]
            text = text_widget.get(start, end).strip()
            if text:
                bold_words.append(text)
    except Exception as e:
        print(f"提取加粗文字失败: {e}")

    # 去重并最多返回5个
    seen = set()
    result = []
    for word in bold_words:
        if word not in seen:
            seen.add(word)
            result.append(word)
            if len(result) >= 5:
                break

    return result


def setup_bold_text_widget(text_widget):
    """为Text组件设置加粗功能

    配置加粗tag并绑定Ctrl+B快捷键

    Args:
        text_widget: tk.Text组件
    """
    # 配置加粗tag样式
    text_widget.tag_config('bold', font=('微软雅黑', 11, 'bold'))

    def toggle_bold(event=None):
        """Ctrl+B切换加粗"""
        try:
            # 检查是否有选中的文本
            start_idx = text_widget.index('sel.first')
            end_idx = text_widget.index('sel.last')

            # 如果没有选中文本（start == end），直接返回
            if start_idx == end_idx:
                return 'break'

            # 检查是否已经加粗
            tags = text_widget.tag_names(start_idx)
            if 'bold' in tags:
                # 取消加粗
                text_widget.tag_remove('bold', start_idx, end_idx)
            else:
                # 添加加粗
                text_widget.tag_add('bold', start_idx, end_idx)

            return 'break'
        except tk.TclError as e:
            # 没有选中文本时抛出异常
            print(f"[DEBUG] TclError: {e}")
            return 'break'

    # 绑定Ctrl+B快捷键
    text_widget.bind('<Control-b>', toggle_bold)
    text_widget.bind('<Control-B>', toggle_bold)

    return toggle_bold


def _apply_bold_to_text(text_widget, keyword: str):
    """在Text组件中查找并加粗指定文字

    Args:
        text_widget: tk.Text组件
        keyword: 要加粗的文字
    """
    content = text_widget.get(1.0, tk.END)
    start_pos = 1.0

    while True:
        # 查找关键字位置
        pos = text_widget.search(keyword, start_pos, stopindex=tk.END)
        if not pos:
            break
        # 计算结束位置
        end_pos = f"{pos}+{len(keyword)}c"
        # 添加加粗tag
        text_widget.tag_add('bold', pos, end_pos)
        # 继续查找下一个
        start_pos = end_pos


def create_cloze_text(content: str, key_points: List[str]) -> str:
    """创建挖空文本

    将重点内容替换为下划线
    """
    if not key_points:
        return content

    cloze_text = content
    for point in key_points:
        # 替换为重点数量的下划线（保留原长度）
        underline = "______" * max(1, len(point) // 5)
        cloze_text = cloze_text.replace(point, underline)

    return cloze_text


# ============================================
# 主应用类
# ============================================
class CardMemApp:
    """CardMem 主应用程序"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CardMem - 知识卡片复习")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS["background"])

        self.data_manager = DataManager()
        self.sync_manager = get_sync_manager(DATA_DIR)  # 初始化同步管理器
        self.current_category = None  # None表示显示全部卡片
        self.current_card = None
        self.review_index = 0
        self.review_cards = []
        self.selected_cards = set()  # 选中的卡片ID集合
        self.checkbox_vars = {}  # 复选框变量字典

        self._setup_ui()
        self._refresh_data()

    def _setup_ui(self):
        """设置UI布局"""
        # ----- 顶部工具栏 -----
        toolbar = tk.Frame(self.root, bg=COLORS["primary"], height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)

        # 工具栏按钮
        btn_style = {"bg": COLORS["secondary"], "fg": "white", "relief": tk.FLAT, "padx": 15, "pady": 8}

        tk.Button(toolbar, text="📥 导入卡片", command=self._show_import_dialog, **btn_style).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="📤 导出备份", command=self._export_backup, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="📥 恢复数据", command=self._import_backup, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="☁️ 同步设置", command=self._show_sync_dialog, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="⚙️ 设置", command=self._show_settings_dialog, **btn_style).pack(side=tk.LEFT, padx=5)

        # 主内容区
        content = tk.Frame(self.root, bg=COLORS["background"])
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ----- 左侧分类栏 -----
        left_frame = tk.Frame(content, bg=COLORS["card_bg"], width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="行业分类", bg=COLORS["card_bg"], font=("微软雅黑", 12, "bold"),
                 fg=COLORS["text_main"]).pack(pady=10)

        # 使用Treeview实现树形分类结构
        self.category_tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        self.category_tree.pack(fill=tk.BOTH, expand=True, padx=10)

        # 配置Treeview样式
        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 11), background=COLORS["card_bg"],
                        fieldbackground=COLORS["card_bg"], foreground=COLORS["text_main"])
        style.configure("Treeview.Item", font=("微软雅黑", 11))
        style.configure("Treeview.Heading", font=("微软雅黑", 11))

        # 绑定点击事件
        self.category_tree.bind("<<TreeviewSelect>>", self._on_category_select)
        # 绑定双击展开/收起事件
        self.category_tree.bind("<Double-1>", self._on_category_double_click)

        # 显示统计说明
        tk.Label(left_frame, text="(仅展示已有分类)", bg=COLORS["card_bg"], font=("微软雅黑", 9),
                 fg=COLORS["text_secondary"]).pack(pady=(0, 10))

        # ----- 中间卡片列表/复习区 -----
        self.middle_frame = tk.Frame(content, bg=COLORS["background"])
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 切换按钮
        self.view_switcher = tk.Frame(self.middle_frame, bg=COLORS["background"])
        self.view_switcher.pack(fill=tk.X)

        self.btn_list_view = tk.Button(self.view_switcher, text="📋 卡片列表",
                                        command=self._show_list_view,
                                        bg=COLORS["secondary"], fg="white",
                                        relief=tk.FLAT, padx=20, pady=8)
        self.btn_list_view.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_review_view = tk.Button(self.view_switcher, text="📖 今日复习",
                                          command=self._show_review_view,
                                          bg=COLORS["primary"], fg="white",
                                          relief=tk.FLAT, padx=20, pady=8)
        self.btn_review_view.pack(side=tk.LEFT, padx=5)

        self.btn_trash_view = tk.Button(self.view_switcher, text="🗑️ 垃圾站",
                                         command=self._show_trash_view,
                                         bg=COLORS["primary"], fg="white",
                                         relief=tk.FLAT, padx=20, pady=8)
        self.btn_trash_view.pack(side=tk.LEFT)

        # 右侧全选和批量删除按钮
        self.list_toolbar = tk.Frame(self.view_switcher, bg=COLORS["background"])
        self.list_toolbar.pack(side=tk.RIGHT, fill=tk.X)

        self.btn_select_all = tk.Button(self.list_toolbar, text="全选",
                                        command=self._select_all_cards,
                                        bg=COLORS["secondary"], fg="white",
                                        relief=tk.FLAT, padx=10, pady=4)
        self.btn_select_all.pack(side=tk.LEFT, padx=2)

        self.btn_batch_delete = tk.Button(self.list_toolbar, text="批量删除",
                                          command=self._batch_delete_cards,
                                          bg=COLORS["accent"], fg="white",
                                          relief=tk.FLAT, padx=10, pady=4)
        self.btn_batch_delete.pack(side=tk.LEFT, padx=2)

        # 卡片列表容器
        self.list_container = tk.Frame(self.middle_frame, bg=COLORS["background"])
        self.list_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # 复习界面容器
        self.review_container = tk.Frame(self.middle_frame, bg=COLORS["background"])
        # 初始不显示

        # ----- 右侧统计栏 -----
        right_frame = tk.Frame(content, bg=COLORS["card_bg"], width=180)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="学习统计", bg=COLORS["card_bg"], font=("微软雅黑", 12, "bold"),
                 fg=COLORS["text_main"]).pack(pady=10)

        # 今日任务
        self.today_task_frame = tk.Frame(right_frame, bg=COLORS["card_bg"])
        self.today_task_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(self.today_task_frame, text="今日任务", bg=COLORS["card_bg"],
                 font=("微软雅黑", 10), fg=COLORS["text_secondary"]).pack()
        self.today_count_label = tk.Label(self.today_task_frame, text="0", bg=COLORS["card_bg"],
                                          font=("微软雅黑", 32, "bold"), fg=COLORS["secondary"])
        self.today_count_label.pack()

        # 分割线
        tk.Frame(right_frame, bg=COLORS["background"], height=1).pack(fill=tk.X, padx=15, pady=10)

        # 分类统计
        self.category_stats_frame = tk.Frame(right_frame, bg=COLORS["card_bg"])
        self.category_stats_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(self.category_stats_frame, text="分类统计", bg=COLORS["card_bg"],
                 font=("微软雅黑", 10), fg=COLORS["text_secondary"]).pack(anchor=tk.W)

        self.stats_text = tk.Text(right_frame, bg=COLORS["card_bg"], borderwidth=0,
                                  font=("微软雅黑", 9), height=15, state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    # ============================================
    # 数据刷新
    # ============================================
    def _refresh_data(self):
        """刷新所有数据展示"""
        self._refresh_categories()
        self._refresh_stats()
        self._refresh_card_list()

    def _refresh_categories(self):
        """刷新分类列表（树形结构，只显示有卡片的分类）"""
        # 清空现有项目
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)

        # 获取所有有卡片的分类
        cards = self.data_manager.data.get("cards", [])
        used_categories = set()
        for card in cards:
            if card.get("category"):
                used_categories.add(card["category"])

        # 同时包含"默认分类"
        used_categories.add("默认分类")

        # 获取分类树形结构
        categories = self.data_manager.get_all_categories()

        # 用于存储有卡片的完整分类路径
        valid_category_paths = set()

        # 遍历分类树，找出有卡片的分类及其父分类
        for cat, children in categories.items():
            if cat in used_categories:
                valid_category_paths.add(cat)
            if children:
                if isinstance(children, list):
                    for child in children:
                        full_path = f"{cat}/{child}"
                        if full_path in used_categories or child in used_categories:
                            valid_category_paths.add(cat)
                            valid_category_paths.add(full_path)
                elif isinstance(children, dict):
                    for child, sub_children in children.items():
                        full_path_2 = f"{cat}/{child}"
                        if full_path_2 in used_categories or child in used_categories:
                            valid_category_paths.add(cat)
                            valid_category_paths.add(full_path_2)
                        if sub_children:
                            for sub_child in sub_children:
                                full_path_3 = f"{cat}/{child}/{sub_child}"
                                if full_path_3 in used_categories or sub_child in used_categories:
                                    valid_category_paths.add(cat)
                                    valid_category_paths.add(full_path_2)
                                    valid_category_paths.add(full_path_3)

        # 添加"全部卡片"选项
        self.category_tree.insert("", 0, iid="all", text="📋 全部卡片", values=("all",))

        # 构建树形结构
        for cat, children in categories.items():
            # 检查一级分类是否有卡片
            if cat in valid_category_paths:
                if cat == "默认分类":
                    # 默认分类用特殊图标
                    cat_item = self.category_tree.insert("", "end", iid="默认分类", text="📁 默认分类", values=("默认分类",))
                else:
                    cat_item = self.category_tree.insert("", "end", iid=cat, text=f"📁 {cat}", values=(cat,))

                # 显示子分类
                if children:
                    if isinstance(children, list):
                        for child in children:
                            full_path = f"{cat}/{child}"
                            if full_path in valid_category_paths:
                                self.category_tree.insert(cat_item, "end", iid=full_path, text=f"  └─ {child}", values=(full_path,))
                    elif isinstance(children, dict):
                        for child, sub_children in children.items():
                            full_path_2 = f"{cat}/{child}"
                            if full_path_2 in valid_category_paths:
                                child_item = self.category_tree.insert(cat_item, "end", iid=full_path_2, text=f"  └─ {child}", values=(full_path_2,))
                                if sub_children:
                                    for sub_child in sub_children:
                                        full_path_3 = f"{cat}/{child}/{sub_child}"
                                        if full_path_3 in valid_category_paths:
                                            self.category_tree.insert(child_item, "end", iid=full_path_3, text=f"      └─ {sub_child}", values=(full_path_3,))

    def _refresh_stats(self):
        """刷新统计数据"""
        settings = self.data_manager.get_settings()
        daily_limit = settings.get("daily_limit", 15)

        # 今日任务数
        today_cards = self.data_manager.get_today_review_cards()
        self.today_count_label.config(text=str(len(today_cards)))

        # 分类统计
        stats = "📊 掌握进度\n\n"
        total = len(self.data_manager.data["cards"])
        mastered = len([c for c in self.data_manager.data["cards"] if c["status"] == "mastered"])

        if total > 0:
            progress = mastered / total * 100
            stats += f"总卡片: {total}\n"
            stats += f"已掌握: {mastered} ({progress:.0f}%)\n"
            stats += f"学习中: {total - mastered}\n\n"
        else:
            stats += "暂无卡片\n\n"

        # 各分类数量
        stats += "📁 分类明细\n"
        for cat in self.data_manager.data["categories"]:
            count = len([c for c in self.data_manager.data["cards"] if c["category"] == cat])
            stats += f"  {cat}: {count}\n"

        # 垃圾站数量
        trash_count = self.data_manager.get_trash_count()
        stats += f"\n🗑️ 垃圾站: {trash_count} 张\n"

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)

    def _refresh_card_list(self):
        """刷新卡片列表"""
        # 清除现有卡片
        for widget in self.list_container.winfo_children():
            widget.destroy()

        cards = self.data_manager.get_cards_by_category(self.current_category)

        if not cards:
            tk.Label(self.list_container, text="暂无卡片，请导入",
                     bg=COLORS["background"], font=("微软雅黑", 12),
                     fg=COLORS["text_secondary"]).pack(pady=50)
            return

        # 卡片列表
        canvas = tk.Canvas(self.list_container, bg=COLORS["background"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.list_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cards_frame = tk.Frame(canvas, bg=COLORS["background"])
        canvas.create_window((0, 0), window=cards_frame, anchor=tk.NW)

        for card in cards:
            self._create_card_widget(cards_frame, card)

        cards_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_card_widget(self, parent, card: dict):
        """创建卡片展示组件"""
        card_frame = tk.Frame(parent, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        card_frame.pack(fill=tk.X, pady=5, padx=5)

        # 状态颜色
        status_colors = {
            "new": COLORS["text_secondary"],
            "learning": COLORS["secondary"],
            "mastered": COLORS["success"]
        }
        status_texts = {
            "new": "未复习",
            "learning": "复习中",
            "mastered": "已掌握"
        }

        # 标题行
        title_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 复选框
        var = tk.BooleanVar(value=card["id"] in self.selected_cards)
        self.checkbox_vars[card["id"]] = var

        def on_checkbox_change(card_id=card["id"], var=var):
            if var.get():
                self.selected_cards.add(card_id)
            else:
                self.selected_cards.discard(card_id)

        var.trace_add("write", lambda *args, card_id=card["id"], v=var: on_checkbox_change(card_id, v))

        checkbox = tk.Checkbutton(title_frame, variable=var, bg=COLORS["card_bg"],
                                  activebackground=COLORS["card_bg"])
        checkbox.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(title_frame, text=card["title"], bg=COLORS["card_bg"],
                 font=("微软雅黑", 11, "bold"), fg=COLORS["text_main"]).pack(side=tk.LEFT)

        status_color = status_colors.get(card["status"], COLORS["text_secondary"])
        status_label = tk.Label(title_frame, text=status_texts.get(card["status"], ""),
                                bg=status_color, fg="white", font=("微软雅黑", 8),
                                padx=8, pady=2)
        status_label.pack(side=tk.RIGHT)

        # 信息行
        info_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # 构建行业显示
        level1 = card.get("level1_industry", "")
        level2 = card.get("level2_industry", "")
        level3 = card.get("level3_industry", "")
        industry_text = ""
        if level1:
            industry_text = level1
            if level2:
                industry_text += f"/{level2}"
                if level3:
                    industry_text += f"/{level3}"
        if not industry_text:
            industry_text = card.get("category", "默认分类")

        tk.Label(info_frame, text=f"行业: {industry_text}", bg=COLORS["card_bg"],
                 font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack(side=tk.LEFT)

        if card.get("key_points"):
            points_str = ", ".join(card["key_points"][:2])
            tk.Label(info_frame, text=f"重点: {points_str}", bg=COLORS["card_bg"],
                     font=("微软雅黑", 9), fg=COLORS["accent"]).pack(side=tk.LEFT, padx=10)

        # 操作按钮
        btn_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="编辑", command=lambda: self._edit_card(card),
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="标记重点", command=lambda: self._mark_key_points(card),
                  bg=COLORS["warning"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="删除", command=lambda: self._delete_card(card["id"]),
                  bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.RIGHT, padx=2)

    # ============================================
    # 视图切换
    # ============================================
    def _show_list_view(self):
        """切换到卡片列表视图"""
        self.btn_list_view.config(bg=COLORS["secondary"])
        self.btn_review_view.config(bg=COLORS["primary"])
        self.btn_trash_view.config(bg=COLORS["primary"])
        self._show_toolbar()

        self.review_container.pack_forget()
        self.list_container.pack(fill=tk.BOTH, expand=True, pady=10)
        self._refresh_card_list()

    def _show_review_view(self):
        """切换到复习视图"""
        self.btn_list_view.config(bg=COLORS["primary"])
        self.btn_review_view.config(bg=COLORS["secondary"])
        self.btn_trash_view.config(bg=COLORS["primary"])
        self._hide_toolbar()

        self.list_container.pack_forget()
        self.review_container.pack(fill=tk.BOTH, expand=True, pady=10)

        self._start_review()

    def _show_trash_view(self):
        """切换到垃圾站视图"""
        self.btn_list_view.config(bg=COLORS["primary"])
        self.btn_review_view.config(bg=COLORS["primary"])
        self.btn_trash_view.config(bg=COLORS["secondary"])
        self._hide_toolbar()

        self.review_container.pack_forget()
        self.list_container.pack(fill=tk.BOTH, expand=True, pady=10)

        self._refresh_trash_list()

    def _hide_toolbar(self):
        """隐藏列表工具栏"""
        self.list_toolbar.pack_forget()

    def _show_toolbar(self):
        """显示列表工具栏"""
        self.list_toolbar.pack(side=tk.RIGHT, fill=tk.X)

    def _refresh_trash_list(self):
        """刷新垃圾站列表"""
        # 清除现有卡片
        for widget in self.list_container.winfo_children():
            widget.destroy()

        cards = self.data_manager.get_trash_cards()

        if not cards:
            tk.Label(self.list_container, text="🗑️ 垃圾站为空",
                     bg=COLORS["background"], font=("微软雅黑", 14),
                     fg=COLORS["text_secondary"]).pack(pady=50)
            return

        # 垃圾站工具栏
        trash_toolbar = tk.Frame(self.list_container, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        trash_toolbar.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(trash_toolbar, text="🔄 批量恢复", command=self._batch_restore_trash,
                  bg=COLORS["success"], fg="white", relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(trash_toolbar, text="🗑️ 批量彻底删除", command=self._batch_permanent_delete,
                  bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(trash_toolbar, text="⚠️ 清空垃圾站", command=self._empty_trash,
                  bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=15, pady=8).pack(side=tk.RIGHT, padx=5, pady=5)

        # 卡片列表
        canvas = tk.Canvas(self.list_container, bg=COLORS["background"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.list_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cards_frame = tk.Frame(canvas, bg=COLORS["background"])
        canvas.create_window((0, 0), window=cards_frame, anchor=tk.NW)

        for card in cards:
            self._create_trash_card_widget(cards_frame, card)

        cards_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_trash_card_widget(self, parent, card: dict):
        """创建垃圾站卡片组件"""
        card_frame = tk.Frame(parent, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        card_frame.pack(fill=tk.X, pady=5, padx=5)

        # 标题行
        title_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(title_frame, text=card["title"], bg=COLORS["card_bg"],
                 font=("微软雅黑", 11, "bold"), fg=COLORS["text_main"]).pack(side=tk.LEFT)

        # 显示删除时间
        deleted_at = card.get("deleted_at", "未知时间")
        tk.Label(title_frame, text=f"删除于: {deleted_at}", bg=COLORS["card_bg"],
                 font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack(side=tk.RIGHT)

        # 信息行
        info_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # 构建行业显示
        level1 = card.get("level1_industry", "")
        level2 = card.get("level2_industry", "")
        level3 = card.get("level3_industry", "")
        industry_text = ""
        if level1:
            industry_text = level1
            if level2:
                industry_text += f"/{level2}"
                if level3:
                    industry_text += f"/{level3}"
        if not industry_text:
            industry_text = card.get("category", "默认分类")

        tk.Label(info_frame, text=f"行业: {industry_text}", bg=COLORS["card_bg"],
                 font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack(side=tk.LEFT)

        if card.get("key_points"):
            points_str = ", ".join(card["key_points"][:2])
            tk.Label(info_frame, text=f"重点: {points_str}", bg=COLORS["card_bg"],
                     font=("微软雅黑", 9), fg=COLORS["accent"]).pack(side=tk.LEFT, padx=10)

        # 操作按钮
        btn_frame = tk.Frame(card_frame, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="🔄 恢复", command=lambda: self._restore_card(card["id"]),
                  bg=COLORS["success"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ 彻底删除", command=lambda: self._permanent_delete_card(card["id"]),
                  bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.RIGHT, padx=2)

    def _restore_card(self, card_id: str):
        """恢复单个卡片"""
        if self.data_manager.restore_card(card_id):
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            messagebox.showinfo("成功", "卡片已恢复！")
            self._refresh_trash_list()
            self._refresh_stats()

    def _permanent_delete_card(self, card_id: str):
        """永久删除单个卡片"""
        if messagebox.askyesno("确认", "确定要彻底删除此卡片吗？此操作不可恢复！"):
            self.data_manager.permanently_delete_card(card_id)
            self._refresh_trash_list()

    def _batch_restore_trash(self):
        """批量恢复垃圾站中的卡片"""
        # 使用简单的对话框让用户输入要恢复的卡片ID
        dialog = tk.Toplevel(self.root)
        dialog.title("批量恢复")
        dialog.geometry("400x300")
        dialog.transient(self.root)

        tk.Label(dialog, text="请选择要恢复的操作:", font=("微软雅黑", 12, "bold")).pack(pady=20)

        trash_cards = self.data_manager.get_trash_cards()

        if not trash_cards:
            tk.Label(dialog, text="垃圾站为空", font=("微软雅黑", 11)).pack()
            dialog.after(1500, dialog.destroy)
            return

        tk.Label(dialog, text=f"垃圾站中共有 {len(trash_cards)} 张卡片",
                 font=("微软雅黑", 11)).pack(pady=10)

        def restore_all():
            count = self.data_manager.restore_trash_batch([c["id"] for c in trash_cards])
            messagebox.showinfo("成功", f"已恢复 {count} 张卡片！")
            dialog.destroy()
            self._refresh_trash_list()
            self._refresh_stats()

        tk.Button(dialog, text="全部恢复", command=restore_all,
                  bg=COLORS["success"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

        tk.Label(dialog, text="或输入要恢复的卡片序号（用逗号分隔）:",
                 font=("微软雅黑", 10)).pack(pady=10)

        entry = tk.Entry(dialog, font=("微软雅黑", 10), width=30)
        entry.pack(pady=5)

        def restore_selected():
            try:
                indices = [int(x.strip()) - 1 for x in entry.get().split(",") if x.strip().isdigit()]
                selected_ids = [trash_cards[i]["id"] for i in indices if 0 <= i < len(trash_cards)]
                count = self.data_manager.restore_trash_batch(selected_ids)
                messagebox.showinfo("成功", f"已恢复 {count} 张卡片！")
                dialog.destroy()
                self._refresh_trash_list()
                self._refresh_stats()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的序号")

        tk.Button(dialog, text="恢复选中", command=restore_selected,
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

    def _batch_permanent_delete(self):
        """批量彻底删除"""
        dialog = tk.Toplevel(self.root)
        dialog.title("批量彻底删除")
        dialog.geometry("400x300")
        dialog.transient(self.root)

        tk.Label(dialog, text="请选择要彻底删除的操作:", font=("微软雅黑", 12, "bold")).pack(pady=20)

        trash_cards = self.data_manager.get_trash_cards()

        if not trash_cards:
            tk.Label(dialog, text="垃圾站为空", font=("微软雅黑", 11)).pack()
            dialog.after(1500, dialog.destroy)
            return

        tk.Label(dialog, text=f"垃圾站中共有 {len(trash_cards)} 张卡片",
                 font=("微软雅黑", 11)).pack(pady=10)

        def delete_all():
            if messagebox.askyesno("确认", "确定要彻底删除所有卡片吗？此操作不可恢复！"):
                count = self.data_manager.permanently_delete_trash_batch([c["id"] for c in trash_cards])
                messagebox.showinfo("成功", f"已彻底删除 {count} 张卡片！")
                dialog.destroy()
                self._refresh_trash_list()

        tk.Button(dialog, text="全部彻底删除", command=delete_all,
                  bg=COLORS["accent"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

        tk.Label(dialog, text="或输入要删除的卡片序号（用逗号分隔）:",
                 font=("微软雅黑", 10)).pack(pady=10)

        entry = tk.Entry(dialog, font=("微软雅黑", 10), width=30)
        entry.pack(pady=5)

        def delete_selected():
            try:
                indices = [int(x.strip()) - 1 for x in entry.get().split(",") if x.strip().isdigit()]
                selected_ids = [trash_cards[i]["id"] for i in indices if 0 <= i < len(trash_cards)]
                count = self.data_manager.permanently_delete_trash_batch(selected_ids)
                messagebox.showinfo("成功", f"已彻底删除 {count} 张卡片！")
                dialog.destroy()
                self._refresh_trash_list()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的序号")

        tk.Button(dialog, text="删除选中", command=delete_selected,
                  bg=COLORS["accent"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

    def _empty_trash(self):
        """清空垃圾站"""
        trash_count = self.data_manager.get_trash_count()
        if trash_count == 0:
            messagebox.showinfo("提示", "垃圾站已经是空的")
            return

        if messagebox.askyesno("确认", f"确定要清空垃圾站吗？\n将彻底删除 {trash_count} 张卡片，此操作不可恢复！"):
            self.data_manager.empty_trash()
            messagebox.showinfo("成功", "垃圾站已清空！")
            self._refresh_trash_list()

    def _start_review(self):
        """开始复习"""
        self.review_cards = self.data_manager.get_today_review_cards()
        self.review_index = 0

        # 清除复习容器
        for widget in self.review_container.winfo_children():
            widget.destroy()

        if not self.review_cards:
            tk.Label(self.review_container, text="🎉 今日无复习任务",
                     bg=COLORS["background"], font=("微软雅黑", 16),
                     fg=COLORS["success"], pady=50).pack()
            tk.Label(self.review_container, text="可以新增卡片或手动选择复习",
                     bg=COLORS["background"], font=("微软雅黑", 11),
                     fg=COLORS["text_secondary"]).pack()
            return

        self._show_current_review_card()

    def _show_current_review_card(self):
        """显示当前复习卡片"""
        # 清除当前内容
        for widget in self.review_container.winfo_children():
            widget.destroy()

        if self.review_index >= len(self.review_cards):
            tk.Label(self.review_container, text="🎉 今日复习任务已完成！",
                     bg=COLORS["background"], font=("微软雅黑", 18, "bold"),
                     fg=COLORS["success"], pady=50).pack()
            tk.Button(self.review_container, text="返回列表", command=self._show_list_view,
                      bg=COLORS["secondary"], fg="white", relief=tk.FLAT,
                      padx=20, pady=10).pack()
            return

        card = self.review_cards[self.review_index]

        # 卡片标题
        tk.Label(self.review_container, text=f"({self.review_index + 1}/{len(self.review_cards)}) {card['title']}",
                 bg=COLORS["background"], font=("微软雅黑", 14, "bold"),
                 fg=COLORS["text_main"]).pack(pady=(20, 10))

        # 行业信息
        level1 = card.get("level1_industry", "")
        level2 = card.get("level2_industry", "")
        level3 = card.get("level3_industry", "")
        industry_text = ""
        if level1:
            industry_text = level1
            if level2:
                industry_text += f"/{level2}"
                if level3:
                    industry_text += f"/{level3}"
        if not industry_text:
            industry_text = card.get("category", "默认分类")

        tk.Label(self.review_container, text=f"行业: {industry_text}",
                 bg=COLORS["background"], font=("微软雅黑", 10),
                 fg=COLORS["text_secondary"]).pack(pady=(0, 10))

        # 挖空内容区
        cloze_frame = tk.Frame(self.review_container, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        cloze_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # 判断是否已设置重点
        if not card.get("key_points"):
            # 未设置重点，显示原内容
            tk.Label(cloze_frame, text=card["content"], bg=COLORS["card_bg"],
                     font=("微软雅黑", 12), fg=COLORS["text_main"],
                     wraplength=600, justify=tk.LEFT, padx=20, pady=20).pack(expand=True)
            tk.Label(cloze_frame, text="⚠️ 请先设置重点后再复习",
                     bg=COLORS["warning"], fg="white", font=("微软雅黑", 10),
                     pady=5).pack(fill=tk.X)
        else:
            # 显示挖空内容
            cloze_text = create_cloze_text(card["content"], card["key_points"])

            # 使用Text组件以便高亮
            text_widget = tk.Text(cloze_frame, bg="#F8F9FA", borderwidth=0,
                                  font=("微软雅黑", 12), wrap=tk.WORD,
                                  padx=20, pady=20, height=8)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_widget.insert(1.0, cloze_text)
            text_widget.config(state=tk.DISABLED)

            # 按钮区
            btn_frame = tk.Frame(self.review_container, bg=COLORS["background"])
            btn_frame.pack(pady=15)

            tk.Button(btn_frame, text="显示答案", command=lambda: self._show_answer(card, cloze_frame),
                      bg=COLORS["secondary"], fg="white", font=("微软雅黑", 12),
                      relief=tk.FLAT, padx=25, pady=10).pack(side=tk.LEFT, padx=10)

        # 导航按钮
        nav_frame = tk.Frame(self.review_container, bg=COLORS["background"])
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="上一张", command=self._prev_review_card,
                  bg=COLORS["primary"], fg="white", relief=tk.FLAT,
                  padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="下一张", command=self._next_review_card,
                  bg=COLORS["primary"], fg="white", relief=tk.FLAT,
                  padx=15, pady=8).pack(side=tk.LEFT, padx=5)

    def _show_answer(self, card: dict, cloze_frame: tk.Frame):
        """显示答案"""
        # 清除挖空区内容
        for widget in cloze_frame.winfo_children():
            widget.destroy()

        # 显示完整内容，重点标红
        text_widget = tk.Text(cloze_frame, bg=COLORS["card_bg"], borderwidth=0,
                              font=("微软雅黑", 12), wrap=tk.WORD,
                              padx=20, pady=20, height=8)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 插入内容并高亮重点
        content = card["content"]
        text_widget.insert(1.0, content)

        # 高亮重点
        for point in card.get("key_points", []):
            start_idx = "1.0"
            while True:
                pos = text_widget.search(point, start_idx, stopindex=tk.END)
                if not pos:
                    break
                end_idx = f"{pos}+{len(point)}c"
                text_widget.tag_add("highlight", pos, end_idx)
                start_idx = end_idx

        text_widget.tag_config("highlight", foreground=COLORS["accent"], font=("微软雅黑", 12, "bold"))
        text_widget.config(state=tk.DISABLED)

        # 记住/没记住按钮
        btn_frame = tk.Frame(self.review_container, bg=COLORS["background"])
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="✓ 记住了", command=lambda: self._record_review(card, True),
                  bg=COLORS["success"], fg="white", font=("微软雅黑", 12),
                  relief=tk.FLAT, padx=25, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="✗ 没记住", command=lambda: self._record_review(card, False),
                  bg=COLORS["accent"], fg="white", font=("微软雅黑", 12),
                  relief=tk.FLAT, padx=25, pady=10).pack(side=tk.LEFT, padx=10)

    def _record_review(self, card: dict, remembered: bool):
        """记录复习结果"""
        settings = self.data_manager.get_settings()
        intervals = settings.get("intervals", [2, 4, 7, 15])
        mastery_threshold = settings.get("mastery_threshold", 4)

        today = datetime.now()

        # 更新复习历史
        review_record = {
            "date": today.strftime("%Y-%m-%d"),
            "remembered": remembered
        }
        card["review_history"].append(review_record)

        if remembered:
            # 记住了
            card["consecutive_remembers"] += 1

            # 计算下次复习日期
            if card["consecutive_remembers"] >= mastery_threshold:
                # 达到阈值，标记为掌握
                card["status"] = "mastered"
                card["next_review_date"] = None
            else:
                card["status"] = "learning"
                idx = min(card["consecutive_remembers"], len(intervals) - 1)
                next_date = today + timedelta(days=intervals[idx])
                card["next_review_date"] = next_date.strftime("%Y-%m-%d")
        else:
            # 没记住，重置
            card["consecutive_remembers"] = 0
            card["status"] = "learning"
            next_date = today + timedelta(days=1)
            card["next_review_date"] = next_date.strftime("%Y-%m-%d")

        # 保存
        self.data_manager.update_card(card["id"], **card)

        # 自动同步到云盘
        self.sync_manager.sync_to_cloud(self.data_manager)

        # 下一张
        self.review_index += 1
        self._show_current_review_card()

    def _prev_review_card(self):
        """上一张"""
        if self.review_index > 0:
            self.review_index -= 1
            self._show_current_review_card()

    def _next_review_card(self):
        """下一张"""
        self.review_index += 1
        self._show_current_review_card()

    # ============================================
    # 事件处理
    # ============================================
    def _on_category_select(self, event):
        """分类选择事件"""
        selection = self.category_tree.selection()
        if selection:
            item = selection[0]
            category = self.category_tree.item(item, "values")[0]
            if category == "all":
                self.current_category = None  # 全部卡片
            else:
                self.current_category = category
            self._refresh_card_list()

    def _on_category_double_click(self, event):
        """双击分类展开/收起"""
        # 获取点击位置的item
        item = self.category_tree.identify("item", event.x, event.y)
        if item:
            # 如果有子节点，则展开/收起
            children = self.category_tree.get_children(item)
            if children:
                if self.category_tree.item(item, "open"):
                    self.category_tree.item(item, open=False)
                else:
                    self.category_tree.item(item, open=True)

    def _add_category(self):
        """新增分类（支持多级）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新增行业分类")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # 主行业
        tk.Label(dialog, text="主行业名称:", font=("微软雅黑", 11)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        parent_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=20)
        parent_entry.grid(row=0, column=1, padx=10, pady=10)

        # 二级行业
        tk.Label(dialog, text="二级行业名称:", font=("微软雅黑", 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        child_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=20)
        child_entry.grid(row=1, column=1, padx=10, pady=10)

        # 提示
        tk.Label(dialog, text="提示: 二级行业可以留空，只添加主行业",
                 font=("微软雅黑", 9), fg=COLORS["text_secondary"]).grid(row=2, column=1, sticky=tk.W, padx=10)

        def confirm():
            parent = parent_entry.get().strip()
            child = child_entry.get().strip()

            if parent:
                self.data_manager.add_category(parent, child if child else None)
                self._refresh_categories()
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请输入主行业名称")

        tk.Button(dialog, text="确定", command=confirm,
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=20).grid(row=3, column=1, pady=20)

    def _delete_category(self):
        """删除分类（支持多选批量删除）"""
        selection = self.category_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的分类")
            return

        # 获取所有选中的分类
        selected_cats = []
        for item in selection:
            cat = self.category_tree.item(item, "values")[0]
            # 过滤掉"全部卡片"
            if cat != "all":
                selected_cats.append(cat)

        if not selected_cats:
            messagebox.showwarning("提示", "请选择有效的分类")
            return

        count = len(selected_cats)
        confirm_msg = f"确定删除选中的 {count} 个分类及其所有卡片吗？"
        if count == 1:
            confirm_msg = f"确定删除分类「{selected_cats[0]}」及其所有卡片吗？"

        if messagebox.askyesno("确认", confirm_msg):
            self.data_manager.delete_categories_batch(selected_cats)
            self.current_category = None  # 全部卡片
            self._refresh_data()
            messagebox.showinfo("成功", f"已删除 {count} 个分类")

    def _select_all_categories(self):
        """全选所有分类（用于批量删除）"""
        # 获取所有分类项
        all_items = self.category_tree.get_children()
        if not all_items:
            messagebox.showinfo("提示", "没有可选择的分类")
            return

        # 选中所有项目
        self.category_tree.selection_set(all_items)
        selected_count = len(all_items)
        messagebox.showinfo("已选中", f"已选中 {selected_count} 个分类\n点击「删除」按钮可批量删除")

    def _clear_all_categories(self):
        """清空所有分类（保留默认分类和所有卡片）"""
        categories = self.data_manager.get_all_categories()

        # 获取所有非默认分类
        cats_to_delete = [cat for cat in categories.keys() if cat != "默认分类"]

        if not cats_to_delete:
            messagebox.showinfo("提示", "没有可删除的分类")
            return

        count = len(cats_to_delete)
        if messagebox.askyesno("确认", f"确定清空所有 {count} 个分类吗？\n注意：分类将删除，但卡片会保留在「默认分类」中。"):
            # 删除所有非默认分类
            self.data_manager.delete_categories_batch(cats_to_delete)
            # 将所有卡片移动到默认分类
            for card in self.data_manager.data["cards"]:
                if "/" in card["category"]:
                    card["category"] = "默认分类"
            self.data_manager.save_data()
            self.current_category = None  # 全部卡片
            self._refresh_data()
            messagebox.showinfo("成功", f"已清空 {count} 个分类，所有卡片已移至「默认分类」")

    def _delete_card(self, card_id: str):
        """删除卡片（移入垃圾站）"""
        if messagebox.askyesno("确认", "确定删除此卡片吗？\n卡片将被移入垃圾站，可从垃圾站恢复。"):
            self.data_manager.delete_card(card_id)
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()

    def _select_all_cards(self):
        """全选/取消全选"""
        cards = self.data_manager.get_cards_by_category(self.current_category)
        card_ids = {card["id"] for card in cards}

        # 检查是否全选
        if self.selected_cards == card_ids:
            # 取消全选
            self.selected_cards.clear()
        else:
            # 全选
            self.selected_cards = card_ids

        # 更新所有复选框状态
        for card_id, var in self.checkbox_vars.items():
            var.set(card_id in self.selected_cards)

    def _batch_delete_cards(self):
        """批量删除选中的卡片"""
        if not self.selected_cards:
            messagebox.showwarning("提示", "请先选择要删除的卡片")
            return

        count = len(self.selected_cards)
        if messagebox.askyesno("确认", f"确定删除选中的 {count} 张卡片吗？\n卡片将被移入垃圾站，可从垃圾站恢复。"):
            self.data_manager.move_to_trash_batch(list(self.selected_cards))
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self.selected_cards.clear()
            self.checkbox_vars.clear()
            self._refresh_data()
            messagebox.showinfo("成功", f"已删除 {count} 张卡片到垃圾站")

    def _edit_card(self, card: dict):
        """编辑卡片"""
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑卡片")
        dialog.geometry("500x500")
        dialog.transient(self.root)

        # 标题
        tk.Label(dialog, text="知识点标题:", font=("微软雅黑", 11)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        title_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        title_entry.grid(row=0, column=1, padx=10, pady=10)
        title_entry.insert(0, card["title"])

        # 一级行业
        tk.Label(dialog, text="一级行业:", font=("微软雅黑", 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        level1_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level1_entry.grid(row=1, column=1, padx=10, pady=10)
        level1_entry.insert(0, card.get("level1_industry", ""))

        # 二级行业
        tk.Label(dialog, text="二级行业:", font=("微软雅黑", 11)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        level2_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level2_entry.grid(row=2, column=1, padx=10, pady=10)
        level2_entry.insert(0, card.get("level2_industry", ""))

        # 三级行业
        tk.Label(dialog, text="三级行业:", font=("微软雅黑", 11)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        level3_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level3_entry.grid(row=3, column=1, padx=10, pady=10)
        level3_entry.insert(0, card.get("level3_industry", ""))

        # 分类（兼容旧版）
        tk.Label(dialog, text="分类(兼容):", font=("微软雅黑", 10), fg=COLORS["text_secondary"]).grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        flat_cats = self.data_manager.get_flat_categories()
        category_combo = ttk.Combobox(dialog, values=flat_cats,
                                       font=("微软雅黑", 10), width=33)
        category_combo.grid(row=4, column=1, padx=10, pady=10)
        category_combo.set(card["category"])

        # 内容
        tk.Label(dialog, text="知识点内容:", font=("微软雅黑", 11)).grid(row=5, column=0, sticky=tk.NW, padx=10, pady=10)
        content_text = tk.Text(dialog, font=("微软雅黑", 11), width=35, height=8)
        content_text.grid(row=5, column=1, padx=10, pady=10)
        content_text.insert(1.0, card["content"])
        # 设置加粗功能（Ctrl+B快捷键）
        setup_bold_text_widget(content_text)
        # 同步显示原有的重点标记
        for point in card.get("key_points", []):
            _apply_bold_to_text(content_text, point)

        # 添加提示和备用按钮
        tk.Label(dialog, text="提示: 选中文字后按 Ctrl+B 加粗标注重点", font=("微软雅黑", 9), fg=COLORS["text_secondary"]).grid(row=6, column=1, sticky=tk.W, padx=10)

        def manual_toggle_bold():
            try:
                start_idx = content_text.index('sel.first')
                end_idx = content_text.index('sel.last')
                if start_idx == end_idx:
                    messagebox.showwarning("提示", "请先选中要加粗的文字")
                    return
                tags = content_text.tag_names(start_idx)
                if 'bold' in tags:
                    content_text.tag_remove('bold', start_idx, end_idx)
                else:
                    content_text.tag_add('bold', start_idx, end_idx)
            except tk.TclError:
                messagebox.showwarning("提示", "请先选中要加粗的文字")

        tk.Button(dialog, text="加粗选中文字", command=manual_toggle_bold,
                  bg=COLORS["warning"], fg="white", relief=tk.FLAT, padx=10, pady=3).grid(row=6, column=1, sticky=tk.E, padx=10)

        def save():
            level1 = level1_entry.get().strip()
            level2 = level2_entry.get().strip()
            level3 = level3_entry.get().strip()

            # 构建category
            if level1:
                if level2:
                    if level3:
                        category = f"{level1}/{level2}/{level3}"
                    else:
                        category = f"{level1}/{level2}"
                else:
                    category = level1
            else:
                category = category_combo.get().strip() or "默认分类"

            content = content_text.get(1.0, tk.END).strip()

            # 提取加粗文字作为重点
            key_points = extract_bold_from_text_widget(content_text)

            self.data_manager.update_card(card["id"],
                title=title_entry.get().strip(),
                category=category,
                content=content,
                key_points=key_points,
                level1_industry=level1,
                level2_industry=level2,
                level3_industry=level3
            )
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()
            dialog.destroy()

        tk.Button(dialog, text="保存", command=save,
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=20).grid(row=7, column=1, pady=20)

    def _mark_key_points(self, card: dict):
        """标记重点"""
        dialog = tk.Toplevel(self.root)
        dialog.title("标记重点")
        dialog.geometry("700x500")
        dialog.transient(self.root)

        # 监听关闭事件，关闭时自动保存
        def on_close():
            # 自动保存加粗的重点
            key_points = extract_bold_from_text_widget(content_text)
            if len(key_points) > 5:
                key_points = key_points[:5]  # 最多保存5个
            self.data_manager.update_card(card["id"], key_points=key_points)
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

        # 已有重点
        existing_points = card.get("key_points", [])

        tk.Label(dialog, text="在内容中选中文字，按 Ctrl+B 加粗标注重点（最多5个）", font=("微软雅黑", 12, "bold")).pack(pady=10)

        # 内容编辑区（可编辑）
        content_frame = tk.Frame(dialog, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        content_text = tk.Text(content_frame, font=("微软雅黑", 11), wrap=tk.WORD,
                               padx=15, pady=15, bg="#FEF9E7")
        content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        content_text.insert(1.0, card["content"])
        # 设置加粗功能（Ctrl+B快捷键）
        setup_bold_text_widget(content_text)
        # 同步显示原有的重点标记
        for point in existing_points:
            _apply_bold_to_text(content_text, point)

        # 底部提示和按钮
        tk.Label(dialog, text="提示: 选中文字后按 Ctrl+B 加粗/取消加粗", font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack(pady=(0, 5))

        # 备用加粗按钮
        def manual_toggle_bold():
            try:
                start_idx = content_text.index('sel.first')
                end_idx = content_text.index('sel.last')
                if start_idx == end_idx:
                    messagebox.showwarning("提示", "请先选中要加粗的文字")
                    return
                selected_text = content_text.get(start_idx, end_idx).strip()
                if not selected_text:
                    messagebox.showwarning("提示", "选中的文字为空")
                    return
                tags = content_text.tag_names(start_idx)
                if 'bold' in tags:
                    content_text.tag_remove('bold', start_idx, end_idx)
                    messagebox.showinfo("提示", f"已取消「{selected_text}」的加粗")
                else:
                    content_text.tag_add('bold', start_idx, end_idx)
                    messagebox.showinfo("提示", f"已加粗「{selected_text}」")
            except tk.TclError:
                messagebox.showwarning("提示", "请先选中要加粗的文字")

        # 按钮区域
        btn_area = tk.Frame(dialog, bg=COLORS["background"])
        btn_area.pack(pady=10)

        tk.Button(btn_area, text="加粗选中文字", command=manual_toggle_bold,
                  bg=COLORS["warning"], fg="white", relief=tk.FLAT, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        def confirm():
            # 提取加粗文字作为重点
            key_points = extract_bold_from_text_widget(content_text)

            if len(key_points) > 5:
                messagebox.showwarning("提示", "重点不能超过5个")
                return

            self.data_manager.update_card(card["id"], key_points=key_points)
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()
            dialog.destroy()
            messagebox.showinfo("成功", f"已保存 {len(key_points)} 个重点！")

        tk.Button(btn_area, text="保存重点", command=confirm,
                  bg=COLORS["success"], fg="white", font=("微软雅黑", 12),
                  relief=tk.FLAT, padx=25, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(dialog, text="保存重点", command=confirm,
                  bg=COLORS["success"], fg="white", font=("微软雅黑", 12),
                  relief=tk.FLAT, padx=25, pady=10).pack(pady=10)

    # ============================================
    # 导入导出
    # ============================================
    def _show_import_dialog(self):
        """显示导入对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("导入卡片")
        dialog.geometry("500x350")
        dialog.transient(self.root)

        tk.Label(dialog, text="导入方式:", font=("微软雅黑", 11, "bold")).pack(pady=10)

        # 手动导入
        tk.Button(dialog, text="手动单张录入", command=lambda: [dialog.destroy(), self._manual_import()],
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

        tk.Label(dialog, text="或", font=("微软雅黑", 10), fg=COLORS["text_secondary"]).pack()

        # 批量导入 - 只支持Excel
        tk.Button(dialog, text="导入 Excel 表格", command=lambda: [dialog.destroy(), self._excel_import()],
                  bg=COLORS["success"], fg="white", relief=tk.FLAT,
                  padx=20, pady=10).pack(pady=10)

        tk.Label(dialog, text="Excel表格格式：\n第A列-标题 | 第B列-一级行业 | 第C列-二级行业\n第D列-三级行业 | 第E列-知识内容\n（第一行是标题，不导入）",
                 font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack(pady=20)

    def _manual_import(self):
        """手动单张录入"""
        dialog = tk.Toplevel(self.root)
        dialog.title("手动录入卡片")
        dialog.geometry("500x550")
        dialog.transient(self.root)

        # 标题
        tk.Label(dialog, text="知识点标题:", font=("微软雅黑", 11)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        title_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        title_entry.grid(row=0, column=1, padx=10, pady=10)

        # 一级行业
        tk.Label(dialog, text="一级行业:", font=("微软雅黑", 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        level1_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level1_entry.grid(row=1, column=1, padx=10, pady=10)

        # 二级行业
        tk.Label(dialog, text="二级行业:", font=("微软雅黑", 11)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        level2_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level2_entry.grid(row=2, column=1, padx=10, pady=10)

        # 三级行业
        tk.Label(dialog, text="三级行业:", font=("微软雅黑", 11)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        level3_entry = tk.Entry(dialog, font=("微软雅黑", 11), width=35)
        level3_entry.grid(row=3, column=1, padx=10, pady=10)

        # 分类 - 使用下拉框选择（旧版兼容）
        tk.Label(dialog, text="分类(兼容):", font=("微软雅黑", 10), fg=COLORS["text_secondary"]).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        flat_cats = self.data_manager.get_flat_categories()
        category_combo = ttk.Combobox(dialog, values=flat_cats,
                                       font=("微软雅黑", 10), width=33)
        category_combo.grid(row=4, column=1, padx=10, pady=5)
        category_combo.set("默认分类")

        # 添加新分类的输入框
        tk.Label(dialog, text="或添加新分类:", font=("微软雅黑", 10), fg=COLORS["text_secondary"]).grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)

        # 主行业输入
        tk.Label(dialog, text="主行业:", font=("微软雅黑", 9)).grid(row=6, column=0, sticky=tk.W, padx=10)
        parent_entry = tk.Entry(dialog, font=("微软雅黑", 9), width=15)
        parent_entry.grid(row=6, column=1, sticky=tk.W, padx=10)

        # 子行业输入
        tk.Label(dialog, text="子行业:", font=("微软雅黑", 9)).grid(row=7, column=0, sticky=tk.W, padx=10)
        child_entry = tk.Entry(dialog, font=("微软雅黑", 9), width=15)
        child_entry.grid(row=7, column=1, sticky=tk.W, padx=10)

        # 内容
        tk.Label(dialog, text="知识点内容:", font=("微软雅黑", 11)).grid(row=8, column=0, sticky=tk.NW, padx=10, pady=10)
        content_text = tk.Text(dialog, font=("微软雅黑", 11), width=35, height=8)
        content_text.grid(row=8, column=1, padx=10, pady=10)
        # 设置加粗功能（Ctrl+B快捷键）
        setup_bold_text_widget(content_text)
        # 添加提示
        tk.Label(dialog, text="提示: 选中文字后按 Ctrl+B 加粗标注重点", font=("微软雅黑", 9), fg=COLORS["text_secondary"]).grid(row=9, column=1, sticky=tk.W, padx=10)

        def save():
            title = title_entry.get().strip()
            level1 = level1_entry.get().strip()
            level2 = level2_entry.get().strip()
            level3 = level3_entry.get().strip()

            # 优先使用手动输入的行业分类
            new_parent = parent_entry.get().strip()
            new_child = child_entry.get().strip()

            # 构建category字段
            if level1:
                if level2:
                    if level3:
                        category = f"{level1}/{level2}/{level3}"
                    else:
                        category = f"{level1}/{level2}"
                else:
                    category = level1
            elif new_parent:
                # 兼容旧版手动添加方式
                if new_child:
                    self.data_manager.add_category(new_parent, new_child)
                    category = f"{new_parent}/{new_child}"
                else:
                    self.data_manager.add_category(new_parent)
                    category = new_parent
            else:
                category = category_combo.get().strip() or "默认分类"

            # 如果没有手动输入行业但有新分类，用新分类补充
            if not level1 and new_parent:
                level1 = new_parent
                level2 = new_child

            content = content_text.get(1.0, tk.END).strip()

            if not title or not content:
                messagebox.showwarning("提示", "标题和内容不能为空")
                return

            # 提取加粗文字作为重点
            key_points = extract_bold_from_text_widget(content_text)

            self.data_manager.add_card(title, category, content, key_points,
                                       level1_industry=level1,
                                       level2_industry=level2,
                                       level3_industry=level3)
            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()
            dialog.destroy()
            messagebox.showinfo("成功", f"卡片已导入！\n已自动提取 {len(key_points)} 个重点。")

        tk.Button(dialog, text="保存", command=save,
                  bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=20).grid(row=10, column=1, pady=20)

    def _excel_import(self):
        """从 Excel 文件导入知识卡片

        固定格式：A列-标题，B列-一级行业，C列-二级行业，D列-三级行业，E列-知识内容
        第一行是标题，不导入
        支持E列单元格的加粗文字自动提取为重点
        """
        filepath = filedialog.askopenfilename(
            title="选择导入文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )

        if not filepath:
            return

        try:
            # 加载工作簿
            wb = openpyxl.load_workbook(filepath)
            ws = wb.active

            count = 0
            bold_count_total = 0
            # 从第2行开始读取（跳过标题行）
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                # 检查行是否有效
                if not row or all(cell.value is None for cell in row):
                    continue

                try:
                    # 按固定列顺序读取：A列-标题, B列-一级行业, C列-二级行业, D列-三级行业, E列-知识内容
                    title_cell = row[0]
                    title = str(title_cell.value).strip() if title_cell.value else ""
                    if not title:
                        continue

                    level1_cell = row[1] if len(row) > 1 else None
                    level1 = str(level1_cell.value).strip() if level1_cell and level1_cell.value else "默认分类"

                    level2_cell = row[2] if len(row) > 2 else None
                    level2 = str(level2_cell.value).strip() if level2_cell and level2_cell.value else None

                    level3_cell = row[3] if len(row) > 3 else None
                    level3 = str(level3_cell.value).strip() if level3_cell and level3_cell.value else None

                    content_cell = row[4] if len(row) > 4 else None
                    if not content_cell or not content_cell.value:
                        continue

                    # 获取文本内容
                    content = str(content_cell.value).strip()

                    # 提取E列中的加粗文字作为重点
                    key_points = extract_bold_from_excel_cell(content_cell)

                    # 构建分类路径
                    if level3:
                        category = f"{level1}/{level2}/{level3}"
                        self.data_manager.add_category(level1, level2, level3)
                    elif level2:
                        category = f"{level1}/{level2}"
                        self.data_manager.add_category(level1, level2)
                    else:
                        category = level1
                        self.data_manager.add_category(level1)

                    self.data_manager.add_card(title, category, content, key_points,
                                               level1_industry=level1,
                                               level2_industry=level2,
                                               level3_industry=level3)
                    count += 1
                    bold_count_total += len(key_points)
                except Exception as e:
                    print(f"导入第{row_idx}行失败: {e}")
                    continue

            wb.close()

            # 自动同步到云盘
            self.sync_manager.sync_to_cloud(self.data_manager)
            self._refresh_data()
            messagebox.showinfo("成功", f"成功导入 {count} 张卡片！\n共自动提取 {bold_count_total} 个加粗重点。")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_backup(self):
        """导出备份"""
        filepath = filedialog.asksaveasfilename(
            title="导出备份",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialfile=f"cardmem_backup_{datetime.now().strftime('%Y%m%d')}"
        )

        if filepath:
            self.data_manager.backup(filepath)
            messagebox.showinfo("成功", f"备份已保存到:\n{filepath}")

    def _import_backup(self):
        """导入恢复"""
        if not messagebox.askyesno("确认", "恢复数据将覆盖当前所有数据，确定继续吗？"):
            return

        filepath = filedialog.askopenfilename(
            title="选择备份文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                self.data_manager.restore(filepath)
                self._refresh_data()
                messagebox.showinfo("成功", "数据恢复成功！")
            except Exception as e:
                messagebox.showerror("错误", f"恢复失败: {str(e)}")

    # ============================================
    # 同步功能
    # ============================================
    def _show_sync_dialog(self):
        """显示同步设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("云盘同步设置")
        dialog.geometry("500x400")
        dialog.transient(self.root)

        # 检查同步状态
        sync_status = self.sync_manager.get_sync_status()

        tk.Label(dialog, text="☁️ 云盘同步设置", font=("微软雅黑", 16, "bold")).pack(pady=20)

        # 同步状态显示
        status_frame = tk.Frame(dialog, bg=COLORS["card_bg"], relief=tk.RAISED, bd=1)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        if sync_status['enabled']:
            tk.Label(status_frame, text="✅ 同步已启用", font=("微软雅黑", 11, "bold"),
                    fg=COLORS["success"]).pack(pady=10)
            tk.Label(status_frame, text=f"同步文件夹: {sync_status['sync_folder']}",
                    font=("微软雅黑", 10), wraplength=400).pack(pady=5)

            if sync_status.get('local_mtime'):
                tk.Label(status_frame, text=f"本地数据: {sync_status['local_mtime']}",
                        font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack()
            if sync_status.get('cloud_mtime'):
                tk.Label(status_frame, text=f"云盘数据: {sync_status['cloud_mtime']}",
                        font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack()
            if sync_status.get('last_sync_time'):
                tk.Label(status_frame, text=f"上次同步: {sync_status['last_sync_time']}",
                        font=("微软雅黑", 9), fg=COLORS["text_secondary"]).pack()
        else:
            tk.Label(status_frame, text="❌ 同步未启用", font=("微软雅黑", 11, "bold"),
                    fg=COLORS["accent"]).pack(pady=10)
            tk.Label(status_frame, text="请设置云盘同步文件夹以启用同步功能",
                    font=("微软雅黑", 10)).pack(pady=10)

        # 设置同步文件夹
        tk.Label(dialog, text="选择云盘同步文件夹:", font=("微软雅黑", 11)).pack(pady=(20, 10))

        folder_frame = tk.Frame(dialog, bg=COLORS["background"])
        folder_frame.pack(fill=tk.X, padx=20)

        folder_var = tk.StringVar(value=sync_status.get('sync_folder', ''))
        folder_entry = tk.Entry(folder_frame, textvariable=folder_var, font=("微软雅黑", 10), width=35)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def select_folder():
            folder = filedialog.askdirectory(title="选择云盘同步文件夹")
            if folder:
                folder_var.set(folder)

        tk.Button(folder_frame, text="浏览", command=select_folder,
                 bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)

        # 提示文字
        hint_text = """支持的云盘同步文件夹:
• 百度网盘: 我的同步盘/BaiduNetdiskSave/CardMem
• OneDrive: ~/OneDrive/CardMem
• 阿里云盘: ~/阿里云盘同步文件夹/CardMem
• 其他支持文件同步的云盘均可"""
        tk.Label(dialog, text=hint_text, font=("微软雅黑", 9), fg=COLORS["text_secondary"],
                justify=tk.LEFT).pack(pady=10)

        # 按钮区域
        btn_frame = tk.Frame(dialog, bg=COLORS["background"])
        btn_frame.pack(pady=20)

        def save_and_sync():
            folder = folder_var.get().strip()
            if folder:
                if self.sync_manager.set_sync_folder(folder):
                    messagebox.showinfo("成功", f"同步文件夹已设置:\n{folder}")
                    dialog.destroy()
                    # 保存设置后自动同步
                    self._do_sync()
                else:
                    messagebox.showerror("错误", "文件夹路径无效")
            else:
                messagebox.showwarning("提示", "请选择同步文件夹")

        tk.Button(btn_frame, text="保存设置并同步", command=save_and_sync,
                 bg=COLORS["success"], fg="white", font=("微软雅黑", 11),
                 relief=tk.FLAT, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

        def force_sync():
            result = self.sync_manager.force_sync(self.data_manager)
            if result.get('success'):
                # 重新加载数据
                self.data_manager.data = self.data_manager._load_data()
                self.data_manager.trash_data = self.data_manager._load_trash_data()
                self._refresh_data()
                messagebox.showinfo("同步完成", result.get('message', '同步成功'))
            else:
                messagebox.showerror("同步失败", result.get('message', '未知错误'))

        if sync_status['enabled']:
            tk.Button(btn_frame, text="🔄 立即同步", command=force_sync,
                     bg=COLORS["secondary"], fg="white", font=("微软雅黑", 11),
                     relief=tk.FLAT, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    def _do_sync(self):
        """执行自动同步"""
        if not self.sync_manager.is_sync_enabled():
            return

        result = self.sync_manager.auto_sync(self.data_manager)
        if result.get('action') == 'download':
            # 有数据更新，重新加载
            self.data_manager.data = self.data_manager._load_data()
            self.data_manager.trash_data = self.data_manager._load_trash_data()
            self._refresh_data()

    def _auto_sync_on_startup(self):
        """启动时自动检查同步"""
        if self.sync_manager.is_sync_enabled():
            # 自动检查并同步
            result = self.sync_manager.auto_sync(self.data_manager)
            if result.get('action') == 'download':
                # 重新加载数据
                self.data_manager.data = self.data_manager._load_data()
                self.data_manager.trash_data = self.data_manager._load_trash_data()

    # ============================================
    # 设置
    # ============================================
    def _show_settings_dialog(self):
        """显示设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("400x350")
        dialog.transient(self.root)

        settings = self.data_manager.get_settings()

        tk.Label(dialog, text="复习设置", font=("微软雅黑", 14, "bold")).pack(pady=15)

        # 每日任务数量
        frame1 = tk.Frame(dialog, bg=COLORS["background"])
        frame1.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame1, text="每日复习任务数量:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
        daily_var = tk.IntVar(value=settings.get("daily_limit", 15))
        daily_spin = tk.Spinbox(frame1, from_=5, to=50, textvariable=daily_var, width=10)
        daily_spin.pack(side=tk.RIGHT)

        # 完全掌握阈值
        frame2 = tk.Frame(dialog, bg=COLORS["background"])
        frame2.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame2, text="完全掌握所需次数:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
        mastery_var = tk.IntVar(value=settings.get("mastery_threshold", 4))
        mastery_spin = tk.Spinbox(frame2, from_=2, to=6, textvariable=mastery_var, width=10)
        mastery_spin.pack(side=tk.RIGHT)

        # 复习间隔
        tk.Label(dialog, text="艾宾浩斯复习间隔（天）:", font=("微软雅黑", 11)).pack(pady=(20, 10))

        intervals = settings.get("intervals", [2, 4, 7, 15])
        interval_vars = []
        for i, label in enumerate(["第1次记住后:", "连续2次后:", "连续3次后:", "连续4次后:"]):
            frame = tk.Frame(dialog, bg=COLORS["background"])
            frame.pack(fill=tk.X, padx=20, pady=3)

            tk.Label(frame, text=label, font=("微软雅黑", 10), width=15, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.IntVar(value=intervals[i] if i < len(intervals) else 2)
            spin = tk.Spinbox(frame, from_=1, to=30, textvariable=var, width=10)
            spin.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text="天", font=("微软雅黑", 10)).pack(side=tk.LEFT)
            interval_vars.append(var)

        def save():
            self.data_manager.update_settings(
                daily_limit=daily_var.get(),
                mastery_threshold=mastery_var.get(),
                intervals=[var.get() for var in interval_vars]
            )
            self._refresh_stats()
            dialog.destroy()
            messagebox.showinfo("成功", "设置已保存！")

        tk.Button(dialog, text="保存设置", command=save,
                  bg=COLORS["secondary"], fg="white", font=("微软雅黑", 12),
                  relief=tk.FLAT, padx=25, pady=10).pack(pady=25)

    # ============================================
    # 运行应用
    # ============================================
    def run(self):
        """启动应用"""
        # 启动时自动检查云盘同步
        self._auto_sync_on_startup()
        # 刷新数据展示
        self._refresh_data()
        self.root.mainloop()


# ============================================
# 入口
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("CardMem - 知识卡片复习软件")
    print("=" * 50)
    print("正在启动...")

    app = CardMemApp()
    app.run()
