#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardMem Mobile - 手机端知识卡片复习应用
基于艾宾浩斯记忆曲线的知识卡片智能复习系统

支持功能：
- 艾宾浩斯复习
- 长按文字标记重点（替代Ctrl+B）
- 分类管理
- 垃圾站
- 云盘同步
"""

import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ==================== 配置 ====================
# 获取脚本所在目录（手机端通常是当前目录）
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, "knowledge_cards.json")
TRASH_FILE = os.path.join(DATA_DIR, "trash_cards.json")

DEFAULT_SETTINGS = {
    "daily_limit": 15,
    "mastery_threshold": 4,
    "intervals": [2, 4, 7, 15]
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

# ==================== 数据管理器 ====================
class MobileDataManager:
    """手机端数据管理器"""

    def __init__(self):
        self.data = self._load_data()
        self.trash_data = self._load_trash_data()

    def _load_trash_data(self) -> dict:
        if os.path.exists(TRASH_FILE):
            try:
                with open(TRASH_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"cards": [], "deleted_history": []}

    def _save_trash_data(self):
        try:
            with open(TRASH_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.trash_data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _load_data(self) -> dict:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "categories" not in data:
                        data["categories"] = {"默认分类": []}
                    if "cards" not in data:
                        data["cards"] = []
                    if "settings" not in data:
                        data["settings"] = DEFAULT_SETTINGS.copy()
                    today = datetime.now().strftime("%Y-%m-%d")
                    for card in data.get("cards", []):
                        if "next_review_date" not in card:
                            card["next_review_date"] = today
                        if "status" not in card:
                            card["status"] = "new"
                    return data
            except:
                pass
        return {
            "categories": {"默认分类": []},
            "cards": [],
            "settings": DEFAULT_SETTINGS.copy()
        }

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_card(self, title: str, category: str, content: str, key_points: List[str] = None,
                 level1: str = "", level2: str = "", level3: str = "") -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        card = {
            "id": str(uuid.uuid4()),
            "title": title,
            "category": category,
            "content": content,
            "key_points": key_points or [],
            "level1_industry": level1,
            "level2_industry": level2,
            "level3_industry": level3,
            "status": "new",
            "consecutive_remembers": 0,
            "next_review_date": today,
            "review_history": [],
            "created_at": today
        }
        self.data["cards"].append(card)

        categories = self.data["categories"]
        if "/" in category:
            parts = category.split("/", 1)
            parent = parts[0]
            child = parts[1]
            if parent not in categories:
                categories[parent] = []
            if child not in categories[parent]:
                categories[parent].append(child)
        else:
            if category not in categories:
                categories[category] = []

        self.save_data()
        return card

    def update_card(self, card_id: str, **kwargs):
        for card in self.data["cards"]:
            if card["id"] == card_id:
                card.update(kwargs)
                self.save_data()
                return True
        return False

    def delete_card(self, card_id: str):
        card = self.get_card(card_id)
        if card:
            card["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.trash_data["cards"].append(card)
            self._save_trash_data()
            self.data["cards"] = [c for c in self.data["cards"] if c["id"] != card_id]
            self.save_data()
            return True
        return False

    def restore_card(self, card_id: str) -> bool:
        for card in self.trash_data["cards"]:
            if card["id"] == card_id:
                card.pop("deleted_at", None)
                self.data["cards"].append(card)
                self.save_data()
                self.trash_data["cards"] = [c for c in self.trash_data["cards"] if c["id"] != card_id]
                self._save_trash_data()
                return True
        return False

    def permanently_delete_card(self, card_id: str):
        self.trash_data["cards"] = [c for c in self.trash_data["cards"] if c["id"] != card_id]
        self._save_trash_data()

    def empty_trash(self):
        self.trash_data["cards"] = []
        self._save_trash_data()

    def get_trash_count(self) -> int:
        return len(self.trash_data.get("cards", []))

    def get_card(self, card_id: str) -> Optional[dict]:
        for card in self.data["cards"]:
            if card["id"] == card_id:
                return card
        return None

    def get_cards_by_category(self, category: str) -> List[dict]:
        if category is None or category == "all":
            return self.data["cards"]
        if "/" not in category:
            return [c for c in self.data["cards"] if c["category"].startswith(category + "/") or c["category"] == category]
        return [c for c in self.data["cards"] if c["category"].startswith(category + "/") or c["category"] == category]

    def get_today_review_cards(self) -> List[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        settings = self.data["settings"]
        daily_limit = settings.get("daily_limit", 15)

        review_cards = [
            c for c in self.data["cards"]
            if c["status"] != "mastered" and c["next_review_date"] <= today
        ]
        review_cards.sort(key=lambda x: x["next_review_date"])
        return review_cards[:daily_limit]

    def get_all_categories(self) -> dict:
        return self.data.get("categories", {"默认分类": []})

    def get_flat_categories(self) -> List[str]:
        result = []
        categories = self.get_all_categories()
        for parent, children in categories.items():
            if parent == "默认分类":
                result.append(parent)
                continue
            result.append(parent)
            if children and isinstance(children, list):
                for child in children:
                    result.append(f"{parent}/{child}")
        return result

    def add_category(self, parent: str, child: str = None):
        categories = self.data["categories"]
        if child:
            if parent not in categories:
                categories[parent] = {}
            if not isinstance(categories[parent], dict):
                categories[parent] = {}
            if child not in categories[parent]:
                categories[parent][child] = []
        else:
            if parent and parent not in categories:
                categories[parent] = {}
        self.save_data()

    def get_settings(self) -> dict:
        return self.data["settings"].copy()

    def update_settings(self, **kwargs):
        self.data["settings"].update(kwargs)
        self.save_data()


# ==================== UI组件 ====================
class CardButton(Button):
    """卡片按钮组件"""
    card_data = ObjectProperty(None)

    def __init__(self, card_data=None, **kwargs):
        super().__init__(**kwargs)
        self.card_data = card_data


class CategorySpinner(Spinner):
    """分类下拉选择器"""
    pass


# ==================== 屏幕 ====================
class HomeScreen(Screen):
    """首页 - 显示统计和导航"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.build_ui()

    def build_ui(self):
        from kivy.uix.stacklayout import StackLayout

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # 标题
        title = Label(text='📚 CardMem', font_size='28sp', bold=True,
                     color=COLORS['primary'], size_hint_y=None, height=60)
        layout.add_widget(title)

        # 统计卡片
        stats_box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        stats_box.canvas.before.add(Color(0.95, 0.95, 0.95, 1))
        stats_box.canvas.before.add(RoundedRectangle(radius=[15], size=stats_box.size))
        stats_box.bind(size=stats_box.canvas.before.add(RoundedRectangle(radius=[15], size=stats_box.size).size))

        settings = self.data_manager.get_settings()
        daily_limit = settings.get("daily_limit", 15)
        today_cards = self.data_manager.get_today_review_cards()

        stats_box.add_widget(Label(text='今日复习任务', font_size='14sp', color=COLORS['text_secondary']))
        stats_box.add_widget(Label(text=str(len(today_cards)), font_size='48sp', bold=True, color=COLORS['secondary']))

        total = len(self.data_manager.data["cards"])
        mastered = len([c for c in self.data_manager.data["cards"] if c["status"] == "mastered"])

        stats_box.add_widget(Label(text=f'总卡片: {total}  |  已掌握: {mastered}',
                                   font_size='12sp', color=COLORS['text_secondary']))

        layout.add_widget(stats_box)

        # 功能按钮
        btn_container = GridLayout(cols=2, spacing=15, size_hint_y=None, height=200)
        btn_container.bind(minimum_height=btn_container.setter('height'))

        btns = [
            ('📖 今日复习', 'secondary', 'start_review'),
            ('📋 卡片列表', 'primary', 'show_list'),
            ('➕ 添加卡片', 'success', 'add_card'),
            ('🗑️ 垃圾站', 'accent', 'show_trash'),
            ('⚙️ 设置', 'text_secondary', 'show_settings'),
        ]

        for text, color_key, screen in btns:
            btn = Button(text=text, font_size='16sp',
                        background_color=COLORS.get(color_key, COLORS['primary']),
                        size_hint_y=None, height=80)
            btn.bind(on_press=lambda x, s=screen: self.go_to_screen(s))
            btn_container.add_widget(btn)

        layout.add_widget(btn_container)

        # 同步状态
        sync_label = Label(text='☁️ 数据已同步', font_size='12sp', color=COLORS['success'],
                          size_hint_y=None, height=30)
        layout.add_widget(sync_label)

        self.add_widget(layout)

    def go_to_screen(self, screen_name):
        if screen_name == 'start_review':
            app = App.get_running_app()
            app.sm.current = 'review'
            app.sm.get_screen('review').start_review()
        elif screen_name == 'show_list':
            app = App.get_running_app()
            app.sm.current = 'card_list'
        elif screen_name == 'add_card':
            app = App.get_running_app()
            app.sm.current = 'add_card'
        elif screen_name == 'show_trash':
            app = App.get_running_app()
            app.sm.current = 'trash'
        elif screen_name == 'show_settings':
            app = App.get_running_app()
            app.sm.current = 'settings'


class CardListScreen(Screen):
    """卡片列表屏幕"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.current_category = None
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_home())
        top_bar.add_widget(back_btn)

        title = Label(text='📋 卡片列表', font_size='18sp', bold=True, color=COLORS['primary'])
        top_bar.add_widget(title)

        layout.add_widget(top_bar)

        # 分类选择
        self.category_spinner = CategorySpinner(
            text='全部',
            values=['全部'] + self.data_manager.get_flat_categories(),
            size_hint_y=None, height=40
        )
        self.category_spinner.bind(text=self.on_category_change)
        layout.add_widget(self.category_spinner)

        # 卡片列表
        self.card_scroll = ScrollView()
        self.card_list = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.card_list.bind(minimum_height=self.card_list.setter('height'))
        self.card_scroll.add_widget(self.card_list)
        layout.add_widget(self.card_scroll)

        self.add_widget(layout)
        self.refresh_list()

    def on_category_change(self, spinner, text):
        if text == '全部':
            self.current_category = None
        else:
            self.current_category = text
        self.refresh_list()

    def refresh_list(self):
        self.card_list.clear_widgets()
        cards = self.data_manager.get_cards_by_category(self.current_category)

        if not cards:
            self.card_list.add_widget(Label(text='暂无卡片', font_size='14sp',
                                           color=COLORS['text_secondary'], height=100))
            return

        for card in cards:
            card_box = self.create_card_widget(card)
            self.card_list.add_widget(card_box)

    def create_card_widget(self, card):
        from kivy.uix.anchorlayout import AnchorLayout

        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        box.canvas.before.add(Color(1, 1, 1, 1))
        box.canvas.before.add(RoundedRectangle(radius=[10], size=box.size))
        box.bind(size=box.canvas.before.add(RoundedRectangle(radius=[10], size=box.size).size))

        # 标题
        title = Label(text=card['title'], font_size='16sp', bold=True,
                     color=COLORS['text_main'], halign='left')
        title.bind(width=lambda *args: title.setter('text_size')(title.width, None))
        box.add_widget(title)

        # 分类
        cat = card.get('category', '默认分类')
        cat_label = Label(text=f'📁 {cat}', font_size='12sp', color=COLORS['text_secondary'],
                         halign='left')
        cat_label.bind(width=lambda *args: cat_label.setter('text_size')(cat_label.width, None))
        box.add_widget(cat_label)

        # 状态
        status_text = {'new': '未复习', 'learning': '复习中', 'mastered': '已掌握'}
        status = status_text.get(card['status'], '未复习')
        status_color = COLORS.get('accent' if card['status'] == 'new' else 'secondary' if card['status'] == 'learning' else 'success')

        status_label = Label(text=status, font_size='11sp', color=status_color)
        box.add_widget(status_label)

        # 按钮
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)

        edit_btn = Button(text='编辑', font_size='12sp', background_color=COLORS['secondary'])
        edit_btn.bind(on_press=lambda x, c=card: self.edit_card(c))
        btn_box.add_widget(edit_btn)

        delete_btn = Button(text='删除', font_size='12sp', background_color=COLORS['accent'])
        delete_btn.bind(on_press=lambda x, cid=card['id']: self.delete_card(cid))
        btn_box.add_widget(delete_btn)

        box.add_widget(btn_box)

        return box

    def edit_card(self, card):
        app = App.get_running_app()
        edit_screen = app.sm.get_screen('edit_card')
        edit_screen.set_card(card)
        app.sm.current = 'edit_card'

    def delete_card(self, card_id):
        self.data_manager.delete_card(card_id)
        self.refresh_list()

    def go_home(self):
        App.get_running_app().sm.current = 'home'


class AddCardScreen(Screen):
    """添加卡片屏幕"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_back())
        top_bar.add_widget(back_btn)

        title = Label(text='➕ 添加卡片', font_size='18sp', bold=True, color=COLORS['primary'])
        top_bar.add_widget(title)

        layout.add_widget(top_bar)

        # 表单
        form = ScrollView()
        form_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))

        # 标题
        form_layout.add_widget(Label(text='标题', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.title_input = TextInput(multiline=False, font_size='16sp', padding=10, size_hint_y=None, height=50)
        form_layout.add_widget(self.title_input)

        # 分类
        form_layout.add_widget(Label(text='分类', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.category_input = TextInput(multiline=False, font_size='14sp', padding=10, size_hint_y=None, height=50,
                                        hint_text='如: 编程/Python')
        form_layout.add_widget(self.category_input)

        # 内容
        form_layout.add_widget(Label(text='内容 (长按选中文字可标记重点)', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.content_input = TextInput(font_size='14sp', padding=10, size_hint_y=None, height=200,
                                       hint_text='输入知识点内容...\n\n💡 技巧: 选中文字后长按可标记重点')
        form_layout.add_widget(self.content_input)

        # 保存按钮
        save_btn = Button(text='保存卡片', font_size='16sp', background_color=COLORS['success'],
                         size_hint_y=None, height=60)
        save_btn.bind(on_press=self.save_card)
        form_layout.add_widget(save_btn)

        form.add_widget(form_layout)
        layout.add_widget(form)

        self.add_widget(layout)

    def save_card(self, *args):
        title = self.title_input.text.strip()
        category = self.category_input.text.strip() or "默认分类"
        content = self.content_input.text.strip()

        if not title or not content:
            self.show_popup('提示', '标题和内容不能为空')
            return

        # 提取重点（这里简化处理，实际可以从选中的文字获取）
        key_points = []

        self.data_manager.add_card(title, category, content, key_points)

        self.title_input.text = ''
        self.category_input.text = ''
        self.content_input.text = ''

        self.show_popup('成功', '卡片已保存！')

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                     size_hint=(0.8, 0.3))
        popup.open()

    def go_back(self):
        self.title_input.text = ''
        self.category_input.text = ''
        self.content_input.text = ''
        App.get_running_app().sm.current = 'home'


class EditCardScreen(Screen):
    """编辑卡片屏幕"""
    data_manager = ObjectProperty(None)
    current_card = None

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.build_ui()

    def set_card(self, card):
        self.current_card = card
        self.title_input.text = card.get('title', '')
        self.category_input.text = card.get('category', '默认分类')
        self.content_input.text = card.get('content', '')

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_back())
        top_bar.add_widget(back_btn)

        title = Label(text='✏️ 编辑卡片', font_size='18sp', bold=True, color=COLORS['primary'])
        top_bar.add_widget(title)

        # 保存按钮
        save_btn = Button(text='保存', font_size='14sp', background_color=COLORS['success'], size_hint_x=None, width=80)
        save_btn.bind(on_press=self.save_card)
        top_bar.add_widget(save_btn)

        layout.add_widget(top_bar)

        # 表单
        form_layout = BoxLayout(orientation='vertical', spacing=15)

        form_layout.add_widget(Label(text='标题', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.title_input = TextInput(multiline=False, font_size='16sp', padding=10, size_hint_y=None, height=50)
        form_layout.add_widget(self.title_input)

        form_layout.add_widget(Label(text='分类', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.category_input = TextInput(multiline=False, font_size='14sp', padding=10, size_hint_y=None, height=50)
        form_layout.add_widget(self.category_input)

        form_layout.add_widget(Label(text='内容', font_size='14sp', color=COLORS['text_main'], size_hint_y=None, height=30))
        self.content_input = TextInput(font_size='14sp', padding=10, size_hint_y=None, height=250)
        form_layout.add_widget(self.content_input)

        layout.add_widget(form_layout)

        self.add_widget(layout)

    def save_card(self, *args):
        if not self.current_card:
            return

        title = self.title_input.text.strip()
        category = self.category_input.text.strip() or "默认分类"
        content = self.content_input.text.strip()

        if not title or not content:
            self.show_popup('提示', '标题和内容不能为空')
            return

        self.data_manager.update_card(self.current_card['id'],
            title=title,
            category=category,
            content=content
        )

        self.show_popup('成功', '卡片已保存！')
        Clock.schedule_once(lambda dt: self.go_back(), 1)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                     size_hint=(0.8, 0.3))
        popup.open()

    def go_back(self):
        App.get_running_app().sm.current = 'card_list'


class ReviewScreen(Screen):
    """复习屏幕"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.review_cards = []
        self.review_index = 0
        self.showing_answer = False
        self.build_ui()

    def build_ui(self):
        self.layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_home())
        top_bar.add_widget(back_btn)

        self.progress_label = Label(text='0/0', font_size='14sp', color=COLORS['text_secondary'])
        top_bar.add_widget(self.progress_label)

        self.layout.add_widget(top_bar)

        # 卡片区域
        self.card_area = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.card_area.canvas.before.add(Color(1, 1, 1, 1))
        self.card_area.canvas.before.add(RoundedRectangle(radius=[15], size=self.card_area.size))
        self.card_area.bind(size=self.card_area.canvas.before.add(RoundedRectangle(radius=[15], size=self.card_area.size).size).size)

        self.card_title = Label(text='', font_size='20sp', bold=True, color=COLORS['text_main'])
        self.card_area.add_widget(self.card_title)

        self.card_category = Label(text='', font_size='12sp', color=COLORS['text_secondary'])
        self.card_area.add_widget(self.card_category)

        self.card_content = Label(text='', font_size='14sp', color=COLORS['text_main'],
                                  text_size=(Window.width - 60, None), halign='left')
        self.card_area.add_widget(self.card_content)

        self.layout.add_widget(self.card_area)

        # 按钮区域
        self.btn_area = BoxLayout(size_hint_y=None, height=60, spacing=15)

        self.layout.add_widget(self.btn_area)

        self.add_widget(self.layout)

    def start_review(self):
        self.review_cards = self.data_manager.get_today_review_cards()
        self.review_index = 0
        self.showing_answer = False

        if not self.review_cards:
            self.card_title.text = '🎉 今日无复习任务'
            self.card_category.text = ''
            self.card_content.text = '可以新增卡片或手动选择复习'
            self.btn_area.clear_widgets()
            return

        self.show_current_card()

    def show_current_card(self):
        if self.review_index >= len(self.review_cards):
            self.card_title.text = '🎉 复习完成!'
            self.card_category.text = ''
            self.card_content.text = f'今日复习了 {len(self.review_cards)} 张卡片'
            self.btn_area.clear_widgets()

            back_btn = Button(text='返回', font_size='16sp', background_color=COLORS['success'])
            back_btn.bind(on_press=lambda x: self.go_home())
            self.btn_area.add_widget(back_btn)
            return

        card = self.review_cards[self.review_index]
        self.progress_label.text = f'{self.review_index + 1}/{len(self.review_cards)}'

        self.card_title.text = card['title']
        self.card_category.text = f"📁 {card.get('category', '默认分类')}"

        # 显示挖空内容
        key_points = card.get('key_points', [])
        if key_points:
            cloze_text = card['content']
            for point in key_points:
                cloze_text = cloze_text.replace(point, '_' * len(point))
            self.card_content.text = cloze_text
        else:
            self.card_content.text = card['content']

        self.showing_answer = False
        self.btn_area.clear_widgets()

        show_btn = Button(text='显示答案', font_size='16sp', background_color=COLORS['secondary'])
        show_btn.bind(on_press=lambda x: self.show_answer())
        self.btn_area.add_widget(show_btn)

    def show_answer(self):
        card = self.review_cards[self.review_index]
        key_points = card.get('key_points', [])

        # 显示带重点标记的内容
        content = card['content']
        if key_points:
            # 用特殊标记显示重点
            for point in key_points:
                content = content.replace(point, f'【{point}】')
        self.card_content.text = content

        self.showing_answer = True
        self.btn_area.clear_widgets()

        remember_btn = Button(text='✓ 记住了', font_size='16sp', background_color=COLORS['success'])
        remember_btn.bind(on_press=lambda x: self.record_review(True))
        self.btn_area.add_widget(remember_btn)

        forget_btn = Button(text='✗ 没记住', font_size='16sp', background_color=COLORS['accent'])
        forget_btn.bind(on_press=lambda x: self.record_review(False))
        self.btn_area.add_widget(forget_btn)

    def record_review(self, remembered):
        card = self.review_cards[self.review_index]
        settings = self.data_manager.get_settings()
        intervals = settings.get("intervals", [2, 4, 7, 15])
        mastery_threshold = settings.get("mastery_threshold", 4)

        today = datetime.now()

        review_record = {
            "date": today.strftime("%Y-%m-%d"),
            "remembered": remembered
        }
        card["review_history"].append(review_record)

        if remembered:
            card["consecutive_remembers"] += 1

            if card["consecutive_remembers"] >= mastery_threshold:
                card["status"] = "mastered"
                card["next_review_date"] = None
            else:
                card["status"] = "learning"
                idx = min(card["consecutive_remembers"], len(intervals) - 1)
                next_date = today + timedelta(days=intervals[idx])
                card["next_review_date"] = next_date.strftime("%Y-%m-%d")
        else:
            card["consecutive_remembers"] = 0
            card["status"] = "learning"
            next_date = today + timedelta(days=1)
            card["next_review_date"] = next_date.strftime("%Y-%m-%d")

        self.data_manager.update_card(card["id"], **card)

        self.review_index += 1
        self.show_current_card()

    def go_home(self):
        App.get_running_app().sm.current = 'home'


class TrashScreen(Screen):
    """垃圾站屏幕"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_home())
        top_bar.add_widget(back_btn)

        title = Label(text='🗑️ 垃圾站', font_size='18sp', bold=True, color=COLORS['primary'])
        top_bar.add_widget(title)

        empty_btn = Button(text='清空', font_size='14sp', background_color=COLORS['accent'], size_hint_x=None, width=80)
        empty_btn.bind(on_press=self.empty_trash)
        top_bar.add_widget(empty_btn)

        layout.add_widget(top_bar)

        # 卡片列表
        self.trash_scroll = ScrollView()
        self.trash_list = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.trash_list.bind(minimum_height=self.trash_list.setter('height'))
        self.trash_scroll.add_widget(self.trash_list)
        layout.add_widget(self.trash_scroll)

        self.add_widget(layout)
        self.refresh_list()

    def refresh_list(self):
        self.trash_list.clear_widgets()
        cards = self.data_manager.trash_data.get("cards", [])

        if not cards:
            self.trash_list.add_widget(Label(text='🗑️ 垃圾站为空', font_size='14sp',
                                           color=COLORS['text_secondary'], height=100))
            return

        for card in cards:
            card_box = self.create_card_widget(card)
            self.trash_list.add_widget(card_box)

    def create_card_widget(self, card):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        box.canvas.before.add(Color(1, 1, 1, 1))
        box.canvas.before.add(RoundedRectangle(radius=[10], size=box.size))
        box.bind(size=box.canvas.before.add(RoundedRectangle(radius=[10], size=box.size).size).size)

        box.add_widget(Label(text=card['title'], font_size='16sp', bold=True,
                            color=COLORS['text_main']))

        deleted_at = card.get('deleted_at', '')
        box.add_widget(Label(text=f'删除于: {deleted_at}', font_size='12sp',
                            color=COLORS['text_secondary']))

        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)

        restore_btn = Button(text='恢复', font_size='12sp', background_color=COLORS['success'])
        restore_btn.bind(on_press=lambda x, cid=card['id']: self.restore_card(cid))
        btn_box.add_widget(restore_btn)

        delete_btn = Button(text='彻底删除', font_size='12sp', background_color=COLORS['accent'])
        delete_btn.bind(on_press=lambda x, cid=card['id']: self.permanent_delete(cid))
        btn_box.add_widget(delete_btn)

        box.add_widget(btn_box)
        return box

    def restore_card(self, card_id):
        self.data_manager.restore_card(card_id)
        self.refresh_list()

    def permanent_delete(self, card_id):
        self.data_manager.permanently_delete_card(card_id)
        self.refresh_list()

    def empty_trash(self):
        self.data_manager.empty_trash()
        self.refresh_list()

    def go_home(self):
        App.get_running_app().sm.current = 'home'


class SettingsScreen(Screen):
    """设置屏幕"""
    data_manager = ObjectProperty(None)

    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # 顶部栏
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)

        back_btn = Button(text='← 返回', font_size='14sp',
                         background_color=COLORS['primary'], size_hint_x=None, width=80)
        back_btn.bind(on_press=lambda x: self.go_home())
        top_bar.add_widget(back_btn)

        title = Label(text='⚙️ 设置', font_size='18sp', bold=True, color=COLORS['primary'])
        top_bar.add_widget(title)

        layout.add_widget(top_bar)

        # 设置项
        settings = self.data_manager.get_settings()

        layout.add_widget(Label(text='复习设置', font_size='16sp', bold=True,
                               color=COLORS['text_main'], size_hint_y=None, height=40))

        # 每日任务数
        layout.add_widget(Label(text='每日复习任务数', font_size='14sp', color=COLORS['text_main']))
        self.daily_limit_input = TextInput(text=str(settings.get('daily_limit', 15)),
                                          multiline=False, font_size='16sp',
                                          input_filter='int', size_hint_y=None, height=50)
        layout.add_widget(self.daily_limit_input)

        # 掌握阈值
        layout.add_widget(Label(text='掌握所需次数', font_size='14sp', color=COLORS['text_main']))
        self.mastery_input = TextInput(text=str(settings.get('mastery_threshold', 4)),
                                      multiline=False, font_size='16sp',
                                      input_filter='int', size_hint_y=None, height=50)
        layout.add_widget(self.mastery_input)

        # 保存按钮
        save_btn = Button(text='保存设置', font_size='16sp', background_color=COLORS['success'],
                         size_hint_y=None, height=60)
        save_btn.bind(on_press=self.save_settings)
        layout.add_widget(save_btn)

        self.add_widget(layout)

    def save_settings(self, *args):
        try:
            daily_limit = int(self.daily_limit_input.text)
            mastery = int(self.mastery_input.text)

            self.data_manager.update_settings(
                daily_limit=daily_limit,
                mastery_threshold=mastery
            )

            popup = Popup(title='成功', content=Label(text='设置已保存！'),
                         size_hint=(0.8, 0.3))
            popup.open()
        except ValueError:
            popup = Popup(title='错误', content=Label(text='请输入有效数字'),
                         size_hint=(0.8, 0.3))
            popup.open()

    def go_home(self):
        App.get_running_app().sm.current = 'home'


# ==================== 主应用 ====================
class CardMemApp(App):
    """CardMem 移动应用"""

    def build(self):
        self.data_manager = MobileDataManager()

        self.sm = ScreenManager(transition=SlideTransition())

        # 创建各个屏幕
        self.sm.add_widget(HomeScreen(self.data_manager, name='home'))
        self.sm.add_widget(CardListScreen(self.data_manager, name='card_list'))
        self.sm.add_widget(AddCardScreen(self.data_manager, name='add_card'))
        self.sm.add_widget(EditCardScreen(self.data_manager, name='edit_card'))
        self.sm.add_widget(ReviewScreen(self.data_manager, name='review'))
        self.sm.add_widget(TrashScreen(self.data_manager, name='trash'))
        self.sm.add_widget(SettingsScreen(self.data_manager, name='settings'))

        return self.sm

    def on_pause(self):
        # 应用暂停时保存数据
        self.data_manager.save_data()
        return True

    def on_resume(self):
        # 恢复时重新加载数据
        self.data_manager.data = self.data_manager._load_data()
        self.data_manager.trash_data = self.data_manager._load_trash_data()


# ==================== 入口 ====================
if __name__ == '__main__':
    CardMemApp().run()
