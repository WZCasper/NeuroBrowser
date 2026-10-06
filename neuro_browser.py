import sys
import os
import json
import math
import ctypes
import re
from urllib.parse import quote_plus
import psutil

# Настройка процессов Windows для иконки в панели задач
APP_ID = 'casper.neurobrowser.2.0'
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
except Exception:
    pass

# Флаги Chromium для максимальной совместимости с видеоплеерами, Widevine и ускорением
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--ignore-certificate-errors "
    "--no-sandbox "
    "--autoplay-policy=no-user-gesture-required "
    "--enable-gpu-rasterization "
    "--enable-accelerated-2d-canvas "
    "--enable-accelerated-video-decode "
    "--enable-webgl "
    "--disable-web-security "
    "--allow-running-insecure-content"
)

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLineEdit, QLabel, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QStackedWidget, QSizePolicy,
    QInputDialog, QTabWidget, QTabBar
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineUrlRequestInterceptor, 
    QWebEngineScript, QWebEngineSettings
)

class AdBlockUrlInterceptor(QWebEngineUrlRequestInterceptor):
    """ Точечный сетевой блокиратор рекламных сетей (Сетевой уровень, не ломает плееры) """
    AD_DOMAINS = [
        "doubleclick.net", "googleadservices.com", "googlesyndication.com",
        "adservice.google.com", "taboola.com", "outbrain.com",
        "popcash.net", "popads.net", "adsterra.com", "exoclick.com",
        "propellerads.com", "clickadu.com", "adcash.com", "juicyads.com",
        "trafficjunky.com", "hilltopads.com", "a-ads.com", "adform.net",
        "criteo.com", "scorecardresearch.com", "bet365.com", "1xbet.com",
        "mostbet.com", "pin-up.club", "yandex.ru/ads", "an.yandex.ru",
        "mc.yandex.ru", "mgid.com", "betwinner.com", "melbet.com",
        "fonbet.ru", "parimatch.com", "vavada.com", "joycasino.com"
    ]

    AD_PATTERNS = [
        "/ads.js", "/ad.js", "/pop.js", "/popup.js", "/banner/", "/banners/",
        "adsterra", "popunder", "clickunder", "exoclick", "popcash"
    ]

    def interceptRequest(self, info):
        url_str = info.requestUrl().toString().lower()
        
        # Строгий белый список для видеопотоков и видеоплееров
        if any(whitelist in url_str for whitelist in [".m3u8", ".mp4", ".ts", ".webm", "blob:", "player", "embed", "kodik", "collaps", "videocdn", "voidboost", "alloha", "hdrezka", "kinopoisk", "youtube"]):
            return

        for domain in self.AD_DOMAINS:
            if domain in url_str:
                info.block(True)
                return

        for pattern in self.AD_PATTERNS:
            if pattern in url_str and "player" not in url_str:
                info.block(True)
                return

def get_kinopoisk_js() -> str:
    """ Кнопка бесплатного просмотра для Кинопоиска """
    return """
    (function() {
        function injectKinopoiskBtn() {
            if (!window.location.hostname.includes('kinopoisk.ru')) return;
            if (document.getElementById('kp-watch-free-btn')) return;

            const path = window.location.pathname;
            if (path.includes('/film/') || path.includes('/series/')) {
                const btn = document.createElement('a');
                btn.id = 'kp-watch-free-btn';
                btn.innerHTML = '▶ СМОТРЕТЬ БЕСПЛАТНО';
                btn.href = '#';
                
                Object.assign(btn.style, {
                    position: 'fixed',
                    top: '120px', 
                    right: '30px',
                    zIndex: '9999999',
                    padding: '12px 24px',
                    backgroundColor: '#111111',
                    color: '#ff6600',
                    border: '2px solid #ff6600',
                    fontWeight: 'bold',
                    fontSize: '14px',
                    fontFamily: 'Segoe UI, sans-serif',
                    borderRadius: '8px',
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.8)',
                    cursor: 'pointer',
                    textDecoration: 'none',
                    transition: 'all 0.25s ease'
                });

                btn.onmouseover = () => {
                    btn.style.backgroundColor = '#ff6600';
                    btn.style.color = '#111111';
                    btn.style.boxShadow = '0 6px 20px rgba(255, 102, 0, 0.5)';
                };
                btn.onmouseout = () => {
                    btn.style.backgroundColor = '#111111';
                    btn.style.color = '#ff6600';
                    btn.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.8)';
                };

                btn.onclick = function(e) {
                    e.preventDefault();
                    let currentUrl = window.location.href;
                    let newUrl = currentUrl.replace('kinopoisk.ru', 'kinokino.vip');
                    window.location.href = newUrl;
                };

                document.body.appendChild(btn);
            }
        }
        setInterval(injectKinopoiskBtn, 1000);
    })();
    """

def get_home_page_html() -> str:
    """ HTML/CSS/JS код Домашней страницы с брендовыми иконками """
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <title>Домашняя страница</title>
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; user-select: none; }
      body {
        background: #050508;
        color: #fff;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        padding: 20px;
      }
      h1 {
        font-size: 26px;
        margin-bottom: 35px;
        background: linear-gradient(90deg, #00f3ff, #bc13fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 2px;
      }
      .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 150px));
        grid-auto-rows: 140px;
        gap: 20px;
        width: 100%;
        max-width: 1000px;
        max-height: 75vh;
        justify-content: center;
        align-content: center;
      }
      .tile {
        position: relative;
        background: rgba(15, 15, 25, 0.85);
        border: 1px solid rgba(0, 243, 255, 0.25);
        border-radius: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.25s ease;
        text-decoration: none;
        color: #fff;
        padding: 15px;
      }
      .tile:hover {
        transform: translateY(-5px);
        border-color: #00f3ff;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
        background: rgba(20, 25, 45, 0.95);
      }
      .tile-icon-img {
        width: 64px;
        height: 64px;
        margin-bottom: 12px;
        border-radius: 12px;
        object-fit: contain;
        background: transparent;
        pointer-events: none; 
      }
      .tile-icon-text {
        font-size: 40px;
        margin-bottom: 12px;
        color: #00ff88;
        pointer-events: none;
      }
      .tile-title {
        font-size: 14px;
        font-weight: 600;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 100%;
        color: #e0e0e0;
      }
      .tile-actions {
        position: absolute;
        top: 8px;
        right: 8px;
        display: none;
        gap: 5px;
        z-index: 10;
      }
      .tile:hover .tile-actions {
        display: flex;
      }
      .btn-act {
        background: rgba(0,0,0,0.8);
        border: 1px solid rgba(255,255,255,0.3);
        color: #fff;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
      }
      .btn-act:hover {
        background: #ff0055;
        border-color: #ff0055;
      }
      .btn-edit:hover {
        background: #00f3ff;
        border-color: #00f3ff;
        color: #000;
      }
      .tile-add {
        border: 2px dashed rgba(0, 255, 136, 0.4);
        background: rgba(0, 255, 136, 0.03);
      }
      .tile-add:hover {
        border-color: #00ff88;
        background: rgba(0, 255, 136, 0.12);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
      }
      .modal {
        display: none;
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8);
        justify-content: center;
        align-items: center;
        z-index: 100;
      }
      .modal-content {
        background: #0f0f18;
        border: 1px solid #00f3ff;
        border-radius: 12px;
        padding: 20px;
        width: 320px;
        box-shadow: 0 0 20px rgba(0,243,255,0.3);
      }
      .modal-content h3 { margin-bottom: 15px; color: #00f3ff; font-size: 16px; }
      .modal-content input {
        width: 100%;
        padding: 8px 10px;
        margin-bottom: 12px;
        background: #050508;
        border: 1px solid rgba(0,243,255,0.3);
        color: #fff;
        border-radius: 6px;
        outline: none;
      }
      .modal-content input:focus { border-color: #00f3ff; }
      .modal-btns { display: flex; justify-content: flex-end; gap: 8px; }
      .modal-btns button {
        padding: 6px 14px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-weight: bold;
      }
      .btn-save { background: #00f3ff; color: #000; }
      .btn-cancel { background: #333; color: #ccc; }
    </style>
    </head>
    <body>
      <h1>ЭКСПРЕСС-ПАНЕЛЬ</h1>
      <div class="grid-container" id="grid"></div>

      <div class="modal" id="modal">
        <div class="modal-content">
          <h3 id="modal-title">Добавить закладку</h3>
          <input type="text" id="site-name" placeholder="Название (напр. Кинопоиск)">
          <input type="text" id="site-url" placeholder="URL (напр. https://kinopoisk.ru)">
          <div class="modal-btns">
            <button class="btn-cancel" onclick="closeModal()">Отмена</button>
            <button class="btn-save" onclick="saveTile()">Сохранить</button>
          </div>
        </div>
      </div>

    <script>
      const DEFAULT_TILES = [
        { title: "Кинопоиск", url: "https://www.kinopoisk.ru" },
        { title: "Ютуб", url: "https://www.youtube.com" },
        { title: "Твич", url: "https://www.twitch.tv" },
        { title: "Kick", url: "https://kick.com" },
        { title: "ВК Live", url: "https://live.vkplay.ru" },
        { title: "TikTok", url: "https://www.tiktok.com" },
        { title: "w.tv", url: "https://w.tv" }
      ];

      let editIdx = -1;

      function getDomain(urlStr) {
        try {
            return new URL(urlStr).hostname;
        } catch(e) {
            return urlStr;
        }
      }

      function loadTiles() {
        let stored = localStorage.getItem('neuro_speed_dial_v3');
        if (!stored) {
          localStorage.setItem('neuro_speed_dial_v3', JSON.stringify(DEFAULT_TILES));
          return DEFAULT_TILES;
        }
        try {
          return JSON.parse(stored);
        } catch(e) {
          return DEFAULT_TILES;
        }
      }

      function renderTiles() {
        const tiles = loadTiles();
        const grid = document.getElementById('grid');
        grid.innerHTML = '';

        tiles.forEach((t, idx) => {
          const el = document.createElement('div');
          el.className = 'tile';
          el.onclick = (e) => {
            if (e.target.classList.contains('btn-act')) return;
            window.location.href = t.url;
          };

          const domain = getDomain(t.url);
          // Использование Google Favicon API для получения официальных брендовых иконок 128x128px
          const iconSrc = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;

          el.innerHTML = `
            <div class="tile-actions">
              <div class="btn-act btn-edit" onclick="openModal(${idx})">✎</div>
              <div class="btn-act" onclick="deleteTile(${idx})">✕</div>
            </div>
            <img class="tile-icon-img" src="${iconSrc}" alt="Icon" onerror="this.style.display='none'">
            <div class="tile-title">${t.title}</div>
          `;
          grid.appendChild(el);
        });

        const addCard = document.createElement('div');
        addCard.className = 'tile tile-add';
        addCard.onclick = () => openModal(-1);
        addCard.innerHTML = `
          <div class="tile-icon-text">+</div>
          <div class="tile-title">Добавить</div>
        `;
        grid.appendChild(addCard);
      }

      function deleteTile(idx) {
        let tiles = loadTiles();
        tiles.splice(idx, 1);
        localStorage.setItem('neuro_speed_dial_v3', JSON.stringify(tiles));
        renderTiles();
      }

      function openModal(idx) {
        editIdx = idx;
        const modal = document.getElementById('modal');
        const nameIn = document.getElementById('site-name');
        const urlIn = document.getElementById('site-url');
        const title = document.getElementById('modal-title');

        if (idx >= 0) {
          const tiles = loadTiles();
          nameIn.value = tiles[idx].title;
          urlIn.value = tiles[idx].url;
          title.innerText = "Изменить закладку";
        } else {
          nameIn.value = "";
          urlIn.value = "";
          title.innerText = "Добавить закладку";
        }
        modal.style.display = "flex";
      }

      function closeModal() {
        document.getElementById('modal').style.display = "none";
      }

      function saveTile() {
        const name = document.getElementById('site-name').value.trim();
        let url = document.getElementById('site-url').value.trim();
        if (!name || !url) return;

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
          url = 'https://' + url;
        }

        let tiles = loadTiles();
        if (editIdx >= 0) {
          tiles[editIdx].title = name;
          tiles[editIdx].url = url;
        } else {
          tiles.push({ title: name, url: url });
        }
        localStorage.setItem('neuro_speed_dial_v3', JSON.stringify(tiles));
        closeModal();
        renderTiles();
      }

      renderTiles();
    </script>
    </body>
    </html>
    """

def get_app_icon():
    """ Генерация иконки браузера """
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen_cyan = QPen(QColor(0, 243, 255), 8)
    painter.setPen(pen_cyan)
    painter.setBrush(QBrush(QColor(5, 5, 8)))
    painter.drawEllipse(16, 16, 224, 224)

    pen_purple = QPen(QColor(188, 19, 254), 5)
    painter.setPen(pen_purple)
    painter.drawEllipse(64, 16, 128, 224)

    pen_thin = QPen(QColor(0, 243, 255, 180), 3)
    painter.setPen(pen_thin)
    painter.drawEllipse(100, 16, 56, 224)
    painter.drawLine(16, 128, 240, 128)
    painter.drawEllipse(16, 64, 224, 128)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 255, 136)))
    painter.drawEllipse(116, 116, 24, 24)
    painter.end()
    
    pixmap.save(os.path.join(os.getcwd(), "icon.png"), "PNG")
    return QIcon(pixmap)

def smart_parse_url(input_text: str) -> QUrl:
    text = input_text.strip()
    if not text or text in ["about:home", "neuro:home", "about:blank"]:
        return QUrl("https://neuro.home")
    if text.startswith(("http://", "https://", "file://", "chrome://", "about:")):
        return QUrl(text)
    domain_pattern = re.compile(
        r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/.*)?$'
        r'|^localhost(?::\d+)?(?:/.*)?$'
        r'|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?(?:/.*)?$'
    )
    if " " not in text and domain_pattern.match(text):
        return QUrl("https://" + text)
    return QUrl(f"https://www.google.com/search?q={quote_plus(text)}")

NEURO_STYLESHEET = """
QMainWindow {
    background-color: #050508;
}
QFrame#sidebar, QFrame#header {
    background-color: rgba(10, 10, 15, 0.95);
    border: 1px solid rgba(0, 243, 255, 0.2);
}
QLabel {
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
QLineEdit#urlInput {
    background-color: rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(0, 243, 255, 0.4);
    border-radius: 6px;
    padding: 6px 12px;
    color: #00f3ff;
    font-size: 14px;
    selection-background-color: #bc13fe;
}
QLineEdit#urlInput:focus {
    border: 1px solid #00f3ff;
}
QPushButton {
    background-color: rgba(0, 243, 255, 0.1);
    border: 1px solid rgba(0, 243, 255, 0.4);
    border-radius: 5px;
    color: #00f3ff;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: rgba(0, 243, 255, 0.25);
    border: 1px solid #00f3ff;
}
QPushButton#navBtn {
    background-color: rgba(0, 243, 255, 0.08);
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 5px;
    color: #00f3ff;
    font-size: 12px;
    padding: 6px 14px;
}
QPushButton#navBtn:hover {
    background-color: rgba(0, 243, 255, 0.3);
    border: 1px solid #00f3ff;
    color: #ffffff;
}
QPushButton#btnAdd {
    background-color: rgba(0, 255, 136, 0.12);
    border: 1px solid #00ff88;
    border-radius: 6px;
    color: #00ff88;
    font-size: 18px;
    font-weight: bold;
    padding: 0px;
}
QPushButton#btnAdd:hover {
    background-color: rgba(0, 255, 136, 0.35);
    border: 1px solid #00ff88;
    color: #ffffff;
}
QPushButton#btnDonate {
    background-color: rgba(255, 20, 147, 0.15);
    border: 1px solid rgba(255, 20, 147, 0.6);
    border-radius: 5px;
    color: #ff69b4;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton#btnDonate:hover {
    background-color: rgba(255, 20, 147, 0.35);
    border: 1px solid #ff1493;
    color: #ffffff;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 4px;
    color: #cccccc;
}
QListWidget::item:selected {
    background-color: rgba(0, 243, 255, 0.15);
    border: 1px solid #00f3ff;
    color: #00f3ff;
}
QListWidget::item:hover {
    background-color: rgba(0, 243, 255, 0.08);
}
QTabWidget::pane {
    border: none;
    border-top: 1px solid rgba(0, 243, 255, 0.2);
    background-color: #050508;
}
QTabBar::tab {
    background: rgba(15, 15, 22, 0.9);
    border: 1px solid rgba(0, 243, 255, 0.2);
    border-bottom: none;
    color: #8888aa;
    padding: 6px 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: rgba(0, 243, 255, 0.15);
    border-color: #00f3ff;
    color: #ffffff;
    font-weight: bold;
}
QTabBar::tab:hover {
    background: rgba(0, 243, 255, 0.08);
    color: #ffffff;
}
"""

class SessionListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.parent_window:
                self.parent_window.delete_session()
        else:
            super().keyPressEvent(event)

class SessionInstance:
    def __init__(self, session_id, parent_window, ad_interceptor, saved_urls=None):
        self.session_id = session_id
        self.name = f"Session [{str(session_id).zfill(2)}]"
        self.parent_window = parent_window

        profile_path = os.path.abspath(os.path.join(os.getcwd(), "profiles", f"profile_{session_id}"))
        os.makedirs(profile_path, exist_ok=True)

        self.profile = QWebEngineProfile(f"NeuroProfile_{session_id}", parent_window)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(os.path.join(profile_path, "cache"))
        
        # Юзер-агент современного браузера Chrome
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        
        # Полные настройки WebEngine для максимальной совместимости с видеоплеерами
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)

        self.profile.setUrlRequestInterceptor(ad_interceptor)

        script_kp = QWebEngineScript()
        script_kp.setSourceCode(get_kinopoisk_js())
        script_kp.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script_kp.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script_kp.setRunsOnSubFrames(False)
        self.profile.scripts().insert(script_kp)

        self.tabs_widget = QTabWidget()
        self.tabs_widget.setTabsClosable(True)
        self.tabs_widget.setMovable(True)
        self.tabs_widget.tabCloseRequested.connect(self.close_tab)
        self.tabs_widget.currentChanged.connect(self.on_tab_changed)
        self.tabs_widget.tabBarClicked.connect(self.on_tab_bar_clicked)

        # Добавление постоянно закрепленной '+' вкладки справа
        dummy_widget = QWidget()
        self.tabs_widget.addTab(dummy_widget, "+")
        self.clean_plus_tab()

        if saved_urls and len(saved_urls) > 0:
            for url in saved_urls:
                self.add_tab(url)
        else:
            self.add_tab("about:home")

        self.card = QFrame()
        self.card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.card.setStyleSheet("QFrame { background-color: #0f0f15; border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 8px; }")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(4, 4, 4, 4)
        self.card_layout.setSpacing(4)

        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)
        self.title_label = QLabel(self.name)
        self.title_label.setStyleSheet("color: #00f3ff; font-weight: bold; font-size: 11px; border: none;")
        header.addWidget(self.title_label)
        header.addStretch()

        self.card_layout.addLayout(header)

    def clean_plus_tab(self):
        """ Убираем иконку крестика с вкладки '+' """
        last_idx = self.tabs_widget.count() - 1
        if last_idx >= 0 and self.tabs_widget.tabText(last_idx) == "+":
            self.tabs_widget.tabBar().setTabButton(last_idx, QTabBar.ButtonPosition.RightSide, None)
            self.tabs_widget.tabBar().setTabButton(last_idx, QTabBar.ButtonPosition.LeftSide, None)

    def handle_fullscreen(self, request):
        """ Поддержка полноэкранного режима плеера """
        request.accept()
        if request.toggleOn():
            self.parent_window.showFullScreen()
        else:
            self.parent_window.showNormal()

    def add_tab(self, url_str="about:home") -> QWebEngineView:
        page = QWebEnginePage(self.profile, self.parent_window)
        page.fullScreenRequested.connect(self.handle_fullscreen)

        view = QWebEngineView()
        view.setPage(page)

        view.urlChanged.connect(lambda url, v=view: self.on_view_url_changed(url, v))
        view.titleChanged.connect(lambda title, v=view: self.on_view_title_changed(title, v))

        # Вставляем перед закрепленной '+' вкладкой
        insert_idx = self.tabs_widget.count() - 1 if self.tabs_widget.count() > 0 else 0
        idx = self.tabs_widget.insertTab(insert_idx, view, "Новая вкладка")
        self.tabs_widget.setCurrentIndex(idx)

        self.load_url_in_view(view, url_str)
        self.clean_plus_tab()
        self.parent_window.save_state()
        return view

    def load_url_in_view(self, view: QWebEngineView, url_str: str):
        if not url_str or url_str in ["about:home", "about:blank", "neuro:home", "https://neuro.home"]:
            view.setHtml(get_home_page_html(), QUrl("https://neuro.home"))
        else:
            view.setUrl(smart_parse_url(url_str))

    def on_tab_bar_clicked(self, index):
        if index == self.tabs_widget.count() - 1 and self.tabs_widget.tabText(index) == "+":
            self.add_tab("about:home")

    def close_tab(self, index):
        # Не разрешаем закрывать плюс
        if index == self.tabs_widget.count() - 1 and self.tabs_widget.tabText(index) == "+":
            return

        real_count = self.tabs_widget.count() - 1
        if real_count > 1:
            widget = self.tabs_widget.widget(index)
            self.tabs_widget.removeTab(index)
            widget.deleteLater()
            self.clean_plus_tab()
            self.parent_window.save_state()
        elif real_count == 1:
            view = self.tabs_widget.widget(0)
            if isinstance(view, QWebEngineView):
                self.load_url_in_view(view, "about:home")

    def get_current_view(self) -> QWebEngineView:
        widget = self.tabs_widget.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def on_tab_changed(self, index):
        view = self.get_current_view()
        if view and self.parent_window.get_active_session() == self:
            curr_url = view.url().toString()
            if "neuro.home" in curr_url:
                self.parent_window.url_input.setText("about:home")
            else:
                self.parent_window.url_input.setText(curr_url)

    def on_view_url_changed(self, url: QUrl, view: QWebEngineView):
        if self.get_current_view() == view and self.parent_window.get_active_session() == self:
            curr_url = url.toString()
            if "neuro.home" in curr_url:
                self.parent_window.url_input.setText("about:home")
            else:
                self.parent_window.url_input.setText(curr_url)
        self.parent_window.save_state()

    def on_view_title_changed(self, title: str, view: QWebEngineView):
        idx = self.tabs_widget.indexOf(view)
        if idx != -1:
            if "neuro.home" in view.url().toString() or title == "Домашняя страница":
                display_title = "Домашняя"
            else:
                display_title = title[:16] + "..." if len(title) > 16 else title
            self.tabs_widget.setTabText(idx, display_title or "Вкладка")

    def update_name(self, new_name):
        self.name = new_name
        self.title_label.setText(new_name)

    def get_all_urls(self):
        urls = []
        for i in range(self.tabs_widget.count() - 1):
            v = self.tabs_widget.widget(i)
            if isinstance(v, QWebEngineView) and v.url().toString():
                urls.append(v.url().toString())
        return urls

class NeuroBrowserApp(QMainWindow):
    def __init__(self, app_icon):
        super().__init__()
        self.setWindowTitle("NeuroBrowser - Multi-Account Neural Suite")
        self.resize(1400, 850)
        self.setStyleSheet(NEURO_STYLESHEET)
        self.setWindowIcon(app_icon)

        self.ad_interceptor = AdBlockUrlInterceptor(self)
        self.sessions = []
        self.active_session_index = 0
        self.is_grid_mode = False
        self.anim_step = 0

        self.init_ui()
        self.load_state()
        self.update_view_mode()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_hardware_stats)
        self.stats_timer.start(1500)
        self.update_hardware_stats()

        # Потоковый таймер плавного переливания RGB
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_brand_title)
        self.anim_timer.start(30)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        self.brand_label = QLabel()
        self.brand_label.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(self.brand_label)
        header_layout.addSpacing(10)

        self.casper_link = QLabel('<a href="https://t.me/WZ_Casper" style="color: #bc13fe; text-decoration: none; font-weight: bold; font-size: 14px;">亗 Casper</a>')
        self.casper_link.setOpenExternalLinks(True)
        header_layout.addWidget(self.casper_link)
        header_layout.addSpacing(15)

        self.btn_back = QPushButton("◄ НАЗАД")
        self.btn_back.setObjectName("navBtn")
        self.btn_back.clicked.connect(self.navigate_back)
        
        self.btn_reload = QPushButton("↻ ОБНОВИТЬ")
        self.btn_reload.setObjectName("navBtn")
        self.btn_reload.clicked.connect(self.navigate_reload)

        header_layout.addWidget(self.btn_back)
        header_layout.addWidget(self.btn_reload)
        header_layout.addSpacing(10)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.setPlaceholderText("Введите адрес или поисковый запрос...")
        self.url_input.returnPressed.connect(self.navigate_active_url)
        header_layout.addWidget(self.url_input, stretch=1)
        header_layout.addSpacing(15)

        self.lbl_cpu = QLabel("CPU: 0%")
        self.lbl_cpu.setStyleSheet("color: #00f3ff; font-family: monospace; font-weight: bold;")
        self.lbl_ram = QLabel("RAM: 0.0 GB")
        self.lbl_ram.setStyleSheet("color: #bc13fe; font-family: monospace; font-weight: bold;")

        header_layout.addWidget(self.lbl_cpu)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.lbl_ram)
        header_layout.addSpacing(15)

        self.btn_donate = QPushButton("Donate")
        self.btn_donate.setObjectName("btnDonate")
        self.btn_donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.donationalerts.com/r/wz_casper")))
        header_layout.addWidget(self.btn_donate)

        main_layout.addWidget(header)

        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

        sidebar_top = QHBoxLayout()
        lbl_sessions = QLabel("ACTIVE LINKS")
        lbl_sessions.setStyleSheet("color: #888; font-size: 11px; font-weight: bold;")

        btn_add = QPushButton("+")
        btn_add.setObjectName("btnAdd")
        btn_add.setFixedSize(30, 30)
        btn_add.clicked.connect(lambda: self.add_new_session())

        sidebar_top.addWidget(lbl_sessions)
        sidebar_top.addStretch()
        sidebar_top.addWidget(btn_add)
        sidebar_layout.addLayout(sidebar_top)

        self.session_list_widget = SessionListWidget(self)
        self.session_list_widget.currentRowChanged.connect(self.on_session_selected)
        self.session_list_widget.itemDoubleClicked.connect(self.rename_session_item)
        sidebar_layout.addWidget(self.session_list_widget)

        btn_layout = QHBoxLayout()
        self.btn_single_view = QPushButton("SINGLE")
        self.btn_grid_view = QPushButton("GRID MATRIX")
        self.btn_single_view.clicked.connect(lambda: self.set_grid_mode(False))
        self.btn_grid_view.clicked.connect(lambda: self.set_grid_mode(True))
        btn_layout.addWidget(self.btn_single_view)
        btn_layout.addWidget(self.btn_grid_view)
        sidebar_layout.addLayout(btn_layout)

        body_splitter.addWidget(sidebar)

        self.viewport_stack = QStackedWidget()
        self.single_widget = QWidget()
        self.single_layout = QVBoxLayout(self.single_widget)
        self.single_layout.setContentsMargins(0, 0, 0, 0)
        self.single_layout.setSpacing(0)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(6, 6, 6, 6)
        self.grid_layout.setSpacing(6)

        self.viewport_stack.addWidget(self.single_widget)
        self.viewport_stack.addWidget(self.grid_container)

        body_splitter.addWidget(self.viewport_stack)
        main_layout.addWidget(body_splitter)

    def navigate_back(self):
        session = self.get_active_session()
        if session and session.get_current_view():
            session.get_current_view().back()

    def navigate_reload(self):
        session = self.get_active_session()
        if session and session.get_current_view():
            session.get_current_view().reload()

    def get_active_session(self) -> SessionInstance:
        if self.sessions and 0 <= self.active_session_index < len(self.sessions):
            return self.sessions[self.active_session_index]
        return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and not self.url_input.hasFocus():
            self.delete_session()
        else:
            super().keyPressEvent(event)

    def animate_brand_title(self):
        """ Плавная бесконечная RGB-анимация без глюков и мерцаний """
        self.anim_step = (self.anim_step + 1) % 360
        color1 = QColor.fromHsv(self.anim_step, 230, 255).name()
        color2 = QColor.fromHsv((self.anim_step + 80) % 360, 230, 255).name()
        
        self.brand_label.setText(
            f"🌐 <span style='color:{color1}; font-weight:bold; font-size:16px;'>NEURO</span>"
            f"<span style='color:{color2}; font-weight:bold; font-size:16px;'>BROWSER</span>"
        )

    def add_new_session(self, saved_name=None, saved_urls=None):
        session_id = len(self.sessions) + 1
        session = SessionInstance(session_id, self, self.ad_interceptor, saved_urls)

        if saved_name:
            session.update_name(saved_name)

        self.sessions.append(session)
        item = QListWidgetItem(f"🔴 {session.name}")
        self.session_list_widget.addItem(item)

        if len(self.sessions) == 1:
            self.session_list_widget.setCurrentRow(0)

        self.update_view_mode()
        self.save_state()

    def delete_session(self, index=None):
        if not self.sessions: return
        if index is None: index = self.session_list_widget.currentRow()

        if 0 <= index < len(self.sessions):
            session_to_delete = self.sessions.pop(index)
            item = self.session_list_widget.takeItem(index)
            del item

            session_to_delete.tabs_widget.hide()
            session_to_delete.tabs_widget.setParent(None)
            session_to_delete.tabs_widget.deleteLater()
            session_to_delete.card.setParent(None)
            session_to_delete.card.deleteLater()

            if len(self.sessions) == 0:
                self.active_session_index = -1
                self.url_input.clear()
            else:
                new_index = max(0, min(index, len(self.sessions) - 1))
                self.session_list_widget.setCurrentRow(new_index)
                self.active_session_index = new_index

            self.update_view_mode()
            self.save_state()

    def rename_session_item(self, item):
        index = self.session_list_widget.row(item)
        if 0 <= index < len(self.sessions):
            session = self.sessions[index]
            text, ok = QInputDialog.getText(self, "Переименовать", "Новое имя сессии:", QLineEdit.EchoMode.Normal, session.name)
            if ok and text.strip():
                session.update_name(text.strip())
                item.setText(f"🔴 {text.strip()}")
                self.save_state()

    def on_session_selected(self, index):
        if 0 <= index < len(self.sessions):
            self.active_session_index = index
            view = self.sessions[index].get_current_view()
            if view:
                curr = view.url().toString()
                if "neuro.home" in curr:
                    self.url_input.setText("about:home")
                else:
                    self.url_input.setText(curr)
            if not self.is_grid_mode:
                self.update_view_mode()

    def navigate_active_url(self):
        input_txt = self.url_input.text().strip()
        session = self.get_active_session()
        if session and session.get_current_view():
            view = session.get_current_view()
            session.load_url_in_view(view, input_txt)

    def set_grid_mode(self, enabled):
        self.is_grid_mode = enabled
        self.update_view_mode()

    def update_view_mode(self):
        if not self.sessions: return

        for i in reversed(range(self.single_layout.count())):
            item = self.single_layout.takeAt(i)
            if item and item.widget(): item.widget().hide()

        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            if item and item.widget(): item.widget().hide()

        if self.is_grid_mode:
            self.viewport_stack.setCurrentIndex(1)
            total = len(self.sessions)
            cols = math.ceil(math.sqrt(total))
            rows = math.ceil(total / cols) if cols > 0 else 1

            for r in range(10): self.grid_layout.setRowStretch(r, 1 if r < rows else 0)
            for c in range(10): self.grid_layout.setColumnStretch(c, 1 if c < cols else 0)

            for idx, session in enumerate(self.sessions):
                if session.card_layout.indexOf(session.tabs_widget) == -1:
                    session.card_layout.addWidget(session.tabs_widget, 1)
                session.tabs_widget.show()
                self.grid_layout.addWidget(session.card, idx // cols, idx % cols)
                session.card.show()

            self.btn_grid_view.setStyleSheet("background-color: rgba(188, 19, 254, 0.4); border: 1px solid #bc13fe;")
            self.btn_single_view.setStyleSheet("")
        else:
            self.viewport_stack.setCurrentIndex(0)
            session = self.get_active_session()
            if session:
                self.single_layout.addWidget(session.tabs_widget, 1)
                session.tabs_widget.show()

            self.btn_single_view.setStyleSheet("background-color: rgba(0, 243, 255, 0.4); border: 1px solid #00f3ff;")
            self.btn_grid_view.setStyleSheet("")

    def save_state(self):
        state = [{"id": s.session_id, "name": s.name, "urls": s.get_all_urls()} for s in self.sessions]
        try:
            with open(os.path.join(os.getcwd(), "sessions_config.json"), "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения состояния: {e}")

    def load_state(self):
        state_path = os.path.join(os.getcwd(), "sessions_config.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                if state and isinstance(state, list):
                    for item in state:
                        self.add_new_session(saved_name=item.get("name"), saved_urls=item.get("urls"))
                    return
            except Exception as e:
                print(f"Ошибка загрузки состояния: {e}")
        
        for _ in range(3):
            self.add_new_session()

    def update_hardware_stats(self):
        try:
            cpu_usage = psutil.cpu_percent()
            ram_used_gb = psutil.virtual_memory().used / (1024 ** 3)
            self.lbl_cpu.setText(f"CPU: {cpu_usage:.1f}%")
            self.lbl_ram.setText(f"RAM: {ram_used_gb:.1f} GB")
            self.lbl_cpu.setStyleSheet(f"color: {'#ff4444' if cpu_usage > 85 else '#ffbb33' if cpu_usage > 60 else '#00f3ff'}; font-family: monospace; font-weight: bold;")
        except Exception:
            pass

    def closeEvent(self, event):
        self.save_state()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    sys_icon = get_app_icon()
    app.setWindowIcon(sys_icon)

    window = NeuroBrowserApp(sys_icon)
    window.show()
    sys.exit(app.exec())