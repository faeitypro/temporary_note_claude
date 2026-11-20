import logging

from view import MainWindow

logging.basicConfig(filename="mvvm_app.log", level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    MainWindow().mainloop()
