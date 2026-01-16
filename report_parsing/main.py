from ui.mainframe import MainFrame
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = MainFrame()
    app.mainloop()