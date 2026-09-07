GREEN = "#25A55A"
GREEN_DARK = "#1F7A46"
GREEN_LIGHT = "#EAF7EF"

ORANGE = "#F28C28"
ORANGE_LIGHT = "#FFF3E8"

WHITE = "#FFFFFF"
BACKGROUND = "#F5F7F6"

TEXT = "#24312A"
TEXT_MUTED = "#68746D"
BORDER = "#DDE5E0"


APP_STYLE = """
QMainWindow {
    background-color: #F5F7F6;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 14px;
    color: #24312A;
}

/* Sidebar */

QFrame#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #DDE5E0;
}

QLabel#brandTitle {
    color: #25A55A;
    font-size: 23px;
    font-weight: 700;
}

QLabel#brandSubtitle {
    color: #68746D;
    font-size: 12px;
}

QLabel#sidebarLabel {
    color: #68746D;
    font-size: 12px;
    font-weight: 600;
}

QPushButton[nav="true"] {
    background: transparent;
    color: #445149;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    text-align: left;
}

QPushButton[nav="true"]:hover {
    background-color: #EAF7EF;
    color: #1F7A46;
}

QPushButton[nav="true"][selected="true"] {
    background-color: #EAF7EF;
    color: #1F7A46;
    font-weight: 700;
    border-left: 4px solid #25A55A;
}

/* Page */

QLabel#pageTitle {
    font-size: 28px;
    font-weight: 700;
    color: #24312A;
}

QLabel#pageDescription {
    color: #68746D;
    font-size: 14px;
}

/* Cards */

QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #DDE5E0;
    border-radius: 12px;
}

QLabel#cardTitle {
    font-size: 16px;
    font-weight: 700;
}

QLabel#cardDescription {
    color: #68746D;
}

QLabel#phaseNumber {
    color: #25A55A;
    font-size: 13px;
    font-weight: 700;
}

QLabel#statusPending {
    background-color: #FFF3E8;
    color: #A85B13;
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 600;
}

QLabel#metricValue {
    color: #1F7A46;
    font-size: 26px;
    font-weight: 700;
}

QLabel#safeInfo {
    background-color: #EAF7EF;
    border: 1px solid #B7DFC6;
    border-radius: 8px;
    padding: 10px;
    color: #1F7A46;
}

QLabel#warningBox {
    background-color: #FFF3E8;
    border: 1px solid #F28C28;
    border-radius: 8px;
    padding: 12px;
    color: #8A4A10;
}

/* Controls */

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CDD8D1;
    border-radius: 7px;
    padding: 8px 10px;
    min-height: 22px;
}

QComboBox:focus {
    border: 1px solid #25A55A;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CDD8D1;
    border-radius: 7px;
    padding: 8px 10px;
    min-height: 22px;
}

QLineEdit:focus {
    border: 1px solid #25A55A;
}

QPushButton#primaryButton {
    background-color: #25A55A;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 11px 18px;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background-color: #1F7A46;
}

QPushButton#primaryButton:disabled {
    background-color: #A9B9B0;
}

QPushButton#secondaryButton {
    background-color: #FFFFFF;
    color: #1F7A46;
    border: 1px solid #25A55A;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton#secondaryButton:hover {
    background-color: #EAF7EF;
}

QProgressBar {
    background-color: #E8ECE9;
    border: none;
    border-radius: 4px;
    min-height: 8px;
    max-height: 8px;
}

QProgressBar::chunk {
    background-color: #F28C28;
    border-radius: 4px;
}
"""
