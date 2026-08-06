"""Launch the DTMF Dialer PyQt6 desktop application."""

import sys

from PyQt6.QtWidgets import QApplication

from dtmf_dialer.gui import MainWindow


def main() -> None:
    """Create the QApplication, show the main window, and run the event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("DTMF Dialer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
