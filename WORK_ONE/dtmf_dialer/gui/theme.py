"""Dark-theme QSS stylesheet for the DTMF Dialer desktop app.

Palette (engineering/DSP-tool tone — dark slate base, cool blue accent):
    Background   #1e1f26   Surface  #262832   Border  #33353f
    Text primary #e5e7eb   Text muted #9ca3af
    Accent (Generate) #5b8cff   Success/Play #34d399   Error #f87171
"""

STYLESHEET = """
QWidget {
    background-color: #1e1f26;
    color: #e5e7eb;
    font-family: "Segoe UI", sans-serif;
    font-size: 10.5pt;
}

QMainWindow {
    background-color: #1e1f26;
}

#HeaderLabel {
    font-size: 16pt;
    font-weight: 600;
    color: #f3f4f6;
    padding: 4px 0;
}

#SubHeaderLabel {
    color: #9ca3af;
    font-size: 9.5pt;
    padding-bottom: 8px;
}

QFrame#Panel {
    background-color: #262832;
    border: 1px solid #33353f;
    border-radius: 10px;
}

QLabel#SectionTitle {
    color: #9ca3af;
    font-size: 9pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding-bottom: 4px;
}

QLineEdit {
    background-color: #1a1b21;
    border: 1px solid #33353f;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13pt;
    color: #f3f4f6;
    selection-background-color: #5b8cff;
}

QLineEdit:focus {
    border: 1px solid #5b8cff;
}

QLineEdit:disabled {
    color: #6b7280;
}

QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1a1b21;
    border: 1px solid #33353f;
    border-radius: 6px;
    padding: 5px 8px;
    color: #e5e7eb;
}

QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #5b8cff;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #262832;
    border: 1px solid #33353f;
    selection-background-color: #5b8cff;
    color: #e5e7eb;
}

QPushButton {
    background-color: #33353f;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
    color: #e5e7eb;
}

QPushButton:hover {
    background-color: #3d3f4a;
}

QPushButton:pressed {
    background-color: #2a2c34;
}

QPushButton:disabled {
    background-color: #26272e;
    color: #5a5c66;
}

QPushButton#GenerateButton {
    background-color: #5b8cff;
    color: #0b0d12;
}

QPushButton#GenerateButton:hover {
    background-color: #7aa0ff;
}

QPushButton#GenerateButton:pressed {
    background-color: #4a76e0;
}

QPushButton#GenerateButton:disabled {
    background-color: #33385c;
    color: #7d8494;
}

QPushButton#PlayButton {
    background-color: #34d399;
    color: #0b0d12;
}

QPushButton#PlayButton:hover {
    background-color: #52dda9;
}

QPushButton#PlayButton:pressed {
    background-color: #26b884;
}

QPushButton#PlayButton:disabled {
    background-color: #24382f;
    color: #6c8078;
}

QToolButton#AdvancedToggle {
    background-color: transparent;
    color: #9ca3af;
    border: none;
    font-size: 9pt;
    text-align: left;
    padding: 4px 0;
}

QToolButton#AdvancedToggle:hover {
    color: #e5e7eb;
}

QListWidget {
    background-color: #1a1b21;
    border: 1px solid #33353f;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
    color: #e5e7eb;
}

QListWidget::item:selected {
    background-color: #2f3550;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #262832;
}

QProgressBar {
    background-color: #1a1b21;
    border: none;
    border-radius: 3px;
    height: 6px;
}

QProgressBar::chunk {
    background-color: #5b8cff;
    border-radius: 3px;
}

QLabel#StatusLabel {
    padding: 6px 2px;
    font-size: 9.5pt;
}

QLabel#StatusLabel[state="idle"] {
    color: #9ca3af;
}

QLabel#StatusLabel[state="loading"] {
    color: #5b8cff;
}

QLabel#StatusLabel[state="success"] {
    color: #34d399;
}

QLabel#StatusLabel[state="error"] {
    color: #f87171;
}

QScrollBar:vertical {
    background: #1e1f26;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #33353f;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #3d3f4a;
}

QToolTip {
    background-color: #262832;
    color: #e5e7eb;
    border: 1px solid #33353f;
    padding: 4px 6px;
}
"""
