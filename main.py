import sys
import os
import logging
from typing import Optional

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QMessageBox, QFileDialog,
                             QLineEdit, QFormLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QMouseEvent

import audio_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DropLabel(QLabel):
    """A QLabel that accepts file drops and clicks."""
    
    fileDropped = pyqtSignal(str)

    def __init__(self, title: str, allowed_extensions: list[str]):
        super().__init__()
        self.setText(title)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        
        # Style
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 10px;
                background-color: #f0f0f0;
                font-size: 14px;
                color: #555;
            }
            QLabel:hover {
                background-color: #e0e0e0;
                border-color: #888;
            }
        """)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Set cursor to point to indicate it's clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.original_pixmap: Optional[QPixmap] = None

    def clear(self) -> None:
        """Clears the label content and resets the original pixmap."""
        self.original_pixmap = None
        super().clear()

    def setPixmap(self, pixmap: QPixmap) -> None:
        self.original_pixmap = pixmap
        self.update_scaled_pixmap()

    def resizeEvent(self, event) -> None:
        if self.original_pixmap:
            self.update_scaled_pixmap()
        super().resizeEvent(event)

    def update_scaled_pixmap(self) -> None:
        if not self.original_pixmap or self.original_pixmap.isNull():
            return
        # Scale to fill efficiently while keeping aspect ratio
        scaled = self.original_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        super().setPixmap(scaled)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_file_dialog()
        super().mousePressEvent(event)

    def open_file_dialog(self) -> None:
        # Create filter string like "Supported Files (*.mp3 *.jpg)"
        exts_str = " ".join([f"*{ext}" for ext in self.allowed_extensions])
        file_filter = f"Supported Files ({exts_str});;All Files (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", file_filter)
        if file_path:
            self.fileDropped.emit(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if not files:
            return

        # Take the first valid file
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.allowed_extensions:
                self.fileDropped.emit(file_path)
                return
        
        # If we got here, no valid file was found
        # (Optional: emit error or shake animation)

class MP3EditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP3 Cover Art Editor")
        self.setGeometry(100, 100, 800, 500)

        self.current_mp3_path: Optional[str] = None
        self.current_image_path: Optional[str] = None
        self.loaded_image_data: Optional[bytes] = None

        self.init_ui()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        panels_layout = QHBoxLayout()

        main_layout.addLayout(panels_layout)

        # Left Panel Container (Vertical: Drop Area + Tags)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # MP3 Drop Area
        self.mp3_panel = DropLabel("Drop MP3 File Here", ['.mp3'])
        self.mp3_panel.fileDropped.connect(self.handle_mp3_drop)
        # Fix size for MP3 panel, let Image panel take remaining space
        self.mp3_panel.setMinimumSize(300, 200)
        self.mp3_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        left_layout.addWidget(self.mp3_panel)

        # ID3 Tags Inputs
        self.tags_form = QFormLayout()
        self.title_input = QLineEdit()
        self.artist_input = QLineEdit()
        self.tags_form.addRow("Title:", self.title_input)
        self.tags_form.addRow("Artist:", self.artist_input)
        left_layout.addLayout(self.tags_form)

        panels_layout.addWidget(left_container, 1) # Stretch factor 1

        # Right Panel: Image File
        self.image_panel = DropLabel("Drop New Image Here\n(or view existing)", ['.jpg', '.jpeg', '.png'])
        self.image_panel.fileDropped.connect(self.handle_image_drop)
        panels_layout.addWidget(self.image_panel, 2) # Stretch factor 2 (bigger)

        # Save Button
        self.save_btn = QPushButton("Save New Cover Art")
        self.save_btn.clicked.connect(self.save_cover_art)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-size: 16px; 
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        main_layout.addWidget(self.save_btn)
        
        # Initial state
        self.update_save_params()

    def update_save_params(self) -> None:
        # Enable save if MP3 is loaded (we can stick to editing tags even without new image)
        can_save = (self.current_mp3_path is not None)
        self.save_btn.setEnabled(can_save)

    def handle_mp3_drop(self, file_path: str) -> None:
        self.current_mp3_path = file_path
        self.mp3_panel.setText(f"MP3 Loaded:\n{os.path.basename(file_path)}")
        
        # Load Metadata
        meta = audio_handler.get_metadata(file_path)
        
        # Defaults
        default_title = os.path.splitext(os.path.basename(file_path))[0]
        default_artist = "סרקאסטים: אורן וצחי" # Default artist requested by user

        # Set Inputs
        self.title_input.setText(meta['title'] if meta['title'] else default_title)
        self.artist_input.setText(meta['artist'] if meta['artist'] else default_artist)

        self.checkForExistingCover()
        self.update_save_params()

    def handle_image_drop(self, file_path: str) -> None:
        self.current_image_path = file_path
        self.display_image(file_path)
        self.update_save_params()

    def display_image(self, path: str) -> None:
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.image_panel.setPixmap(pixmap) # Uses overridden method
        else:
            self.image_panel.setText(f"Failed to load image:\n{os.path.basename(path)}")
            
    def display_image_from_data(self, data: bytes) -> None:
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.image_panel.setPixmap(pixmap) # Uses overridden method
        else:
             self.image_panel.setText("Existing cover art found,\nbut failed to display.")

    def checkForExistingCover(self) -> None:
        if not self.current_mp3_path:
            return
        
        try:
            art_data = audio_handler.extract_cover_art(self.current_mp3_path)
            if art_data:
                self.display_image_from_data(art_data)
                self.current_image_path = None # Reset pending new image since we are just viewing existing
            else:
                # Only clear if we don't have an image currently.
                if self.image_panel.original_pixmap is None:
                    self.image_panel.clear()
                    self.image_panel.setText("No existing cover art found.\nDrop a new image here.")
        except Exception as e:
            logger.error(f"Error checking cover art: {e}")
            QMessageBox.critical(self, "Error", f"Failed to read MP3: {e}")

    def update_save_params(self) -> None:
        # Enable save if MP3 is loaded (we can stick to editing tags even without new image)
        can_save = (self.current_mp3_path is not None)
        self.save_btn.setEnabled(can_save)

    def save_cover_art(self) -> None:
        if not self.current_mp3_path:
            return

        try:
            # 1. Save Metadata
            new_title = self.title_input.text()
            new_artist = self.artist_input.text()
            audio_handler.set_metadata(self.current_mp3_path, new_title, new_artist)

            # 2. Save Image (only if NEW image is provided)
            # If current_image_path is None, we keep existing or do nothing
            if self.current_image_path:
                audio_handler.embed_cover_art(self.current_mp3_path, self.current_image_path)
            
            QMessageBox.information(self, "Success", "Saved successfully!")
            
            # Refresh view
            self.checkForExistingCover()
            self.current_image_path = None # Reset pending image
            self.update_save_params()
            
        except Exception as e:
            logger.error(f"Failed to save: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MP3EditorApp()
    window.show()
    sys.exit(app.exec())
