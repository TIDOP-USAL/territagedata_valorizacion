from PyQt5 import QtCore
from main import run_full_analysis, API_KEY, UPDATE_NEW_REVIEWS
class Worker(QtCore.QThread):

    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(object)

    def __init__(self, place_id, output_path):
        super().__init__()
        self.place_id = place_id
        self.output_path = output_path

    def run(self):

        result = run_full_analysis(
        self.place_id,
        API_KEY,
        UPDATE_NEW_REVIEWS,
        progress_callback=self.progress.emit,
        output_path=self.output_path  
    )

        self.finished.emit(result)