import tkinter as tk
import tmdb

class tkFilmViewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("tkFilmViewer")


if __name__ == "__main__":
    app = tkFilmViewer()
    app.mainloop()