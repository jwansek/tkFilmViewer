import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox
import math as maths
import screeninfo
import threading
import platform
import database
import files
import tmdb
import os

db = database.Database()

class tkFilmViewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("tkFilmViewer")

        self.geometry("%ix%i+50+50" % (int(min([i.width for i in screeninfo.get_monitors()]) * 3/4),
            int(min([i.height for i in screeninfo.get_monitors()]) * 2/3)))

        #setup container, place where stuff goes
        self._containter = tk.Frame(self)
        self._containter.pack(fill = tk.BOTH, expand = True)
        self._containter.grid_rowconfigure(0, weight = 1)
        self._containter.grid_columnconfigure(0, weight = 1)

        #dictionary of screens
        self.screens = {}
        for S in [MainScreen, FilmScreen]:
            screen = S(self._containter, self)
            self.screens[S] = screen
            screen.grid(row = 0, column = 0, sticky = tk.NSEW)

        self.bottombar = AppStatusBar(self)
        self.bottombar.pack(side = tk.BOTTOM, fill = tk.X)

        self.show_screen(MainScreen)

        menubar = tk.Menu(self)
        self.config(menu = menubar)

        filemenu = tk.Menu(menubar, tearoff = False)
        menubar.add_cascade(label = "File", menu = filemenu)
        editmenu = tk.Menu(menubar, tearoff = False)
        menubar.add_cascade(label = "Edit", menu = editmenu)
        settingsmenu = tk.Menu(menubar, tearoff = False)
        menubar.add_cascade(label = "Settings", menu = settingsmenu)
        aboutmenu = tk.Menu(menubar, tearoff = False)
        menubar.add_cascade(label = "About", menu = aboutmenu)

        media_search(self)

    def show_screen(self, screen):
        print("changing screen to", screen)
        self.active_screen = screen
        self.screen = self.screens[screen]
        self.screen.onopen()
        self.screen.tkraise()

class AppStatusBar(tk.Frame):
    def  __init__(self, parent):
        tk.Frame.__init__(self)
        self.parent = parent

        ttk.Separator(self, orient = "horizontal").pack(side = tk.TOP, fill = tk.X, expand = True)
        bottompart = tk.Frame(self)
        bottompart.pack(fill = tk.X, expand = True)
        self.lbl_status = tk.Label(bottompart, text = "Ready")
        self.lbl_status.pack(side = tk.LEFT)
        self.bar_progress = ttk.Progressbar(bottompart, length = 200)
        self.bar_progress.pack(side = tk.RIGHT)

class MainScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller

        self.mediabook = MediaBook(self)
        self.mediabook.pack(fill = tk.BOTH, expand = True)

    def onopen(self):
        self.mediabook.draw_tabs()
        
class MediaBook(ttk.Notebook):

    _tabs = {}

    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        self.parent = parent

    def draw_tabs(self):
        #TODO: add more
        self._tabs["Films"] = MediaList(self, files.get_all_films())

        for key, value in self._tabs.items():
            self.add(value, text = key)

class MediaList(tk.Frame):
    mediadata = {}
    def __init__(self, parent, medialist):  
        tk.Frame.__init__(self)
        self.parent = parent

        self.canvas = tk.Canvas(self)
        self.frame = tk.Frame(self.canvas)
        sbar = tk.Scrollbar(self, orient = tk.VERTICAL, command = self.canvas.yview)
        self.canvas.configure(yscrollcommand = sbar.set)

        sbar.pack(side = tk.RIGHT, fill = tk.Y)
        self.canvas.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
        self.canvas.create_window((0, 0), window = self.frame, anchor = tk.NW)
        self.frame.bind("<Configure>", self._on_scroll)
        self.parent.parent.controller.bind("<MouseWheel>", self._on_mousewheel)
        self.parent.parent.controller.bind("<Button-4>", self._on_mousewheel)
        self.parent.parent.controller.bind("<Button-5>", self._on_mousewheel)
        self.bind("<Configure>", self._on_window_config)

        for media in medialist:
            self.mediadata[media] = {}

        threading.Thread(target = self._load_media, args = (medialist, )).start()
        self.parent.parent.controller.bottombar.lbl_status.config(text = "Loading local files...")

    def _load_media(self, medialist):
        for key, value in self.mediadata.items():
            # tk.Label(self.frame, text = key).pack()
            s = os.path.split(key)[-1].split("(")
            if len(s[0]) > 23:
                title = "%s\n(%s" % (s[0][:10] + "..." + s[0][-10:], s[1].split("{")[0])
            else:
                title = "%s\n(%s" % (s[0], s[1].split("{")[0])
            
            self.mediadata[key]["image"] = ImageTk.PhotoImage(files.resize(Image.open("basicimg.jpg"), width = 150))
            self.mediadata[key]["button"] = ttk.Button(
                self.frame, text = title, image = self.mediadata[key]["image"], compound = tk.TOP)

        self._place_media()

        threading.Thread(target = self._load_metadata, args = ()).start()
        self.parent.parent.controller.bottombar.lbl_status.config(text = "Loading video metadata...")

    def _load_metadata(self):
        self.parent.parent.controller.bottombar.bar_progress['value'] = 0
        tdb = database.Database()
        c = 0
        for key, value in self.mediadata.items():
            c += 1
            self.mediadata[key]["filename"] = files.find_film(key)
            imgpath = tdb.get_poster_img(os.path.join(key, self.mediadata[key]["filename"]))
            if imgpath is None:
                #we don't have metadata cached, so download it
                #TODO do this in another thread and change the status bar
                title, year = files.extract_film_name_year(key)
                data = tmdb.searchOneFilm(title, year)
                tdb.add_film(os.path.join(key, value["filename"]), data)
                imgpath = tdb.get_poster_img(os.path.join(key, self.mediadata[key]["filename"]))
            try:
                self.mediadata[key]["image"] = ImageTk.PhotoImage(files.resize(files.get_image(imgpath), width = 150))
                self.mediadata[key]["button"].config(image = self.mediadata[key]["image"])
            except AttributeError:
                pass
            self.parent.parent.controller.bottombar.bar_progress['value'] += 1

        self.parent.parent.controller.bottombar.bar_progress['value'] = 0
        self.parent.parent.controller.bottombar.lbl_status.config(text = "Ready")

    def _place_media(self):
        self.frame.grid_forget()

        width = self.parent.winfo_width() - 10
        oneachrow = maths.floor(width / 160) - 1
        row = 0
        col = 0
        for key, value in self.mediadata.items():
            try:
                value["button"].grid(row = row, column = col)
            except KeyError:
                continue
            col += 1
            if col > oneachrow:
                col = 0
                row += 1

    def _on_window_config(self, event):
        self.canvas.configure(width = self.winfo_width(), height = self.winfo_height() - 20)
        self._place_media()
        
    def _on_scroll(self, event):
        self.canvas.configure(scrollregion = self.canvas.bbox(tk.ALL), width = event.width, height = self.winfo_height() - 20)

    def _on_mousewheel(self, event):
        if self.parent.parent.controller.active_screen == MainScreen:
            if platform.system() == "Windows":
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                print("Scrolling...", event)
            elif platform.system() == "Linux":
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                self.canvas.yview_scroll(delta, "units")
            else:
                self.canvas.yview_scroll(event.delta, "units")

class FilmScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller

        tk.Label(self, text = "FilmScreen").pack()
        ttk.Button(self, text = "MainScreen", command = lambda: controller.show_screen(MainScreen)).pack()

    def onopen(self):
        pass

class MediaSearchWindow(tk.Toplevel):
    def __init__(self, parent, title = "", year = "", searchingfor = None):
        tk.Toplevel.__init__(self, parent)
        self.title("Media Search Window")

        self._ent_title = ttk.Entry(self)
        self._ent_year = ttk.Entry(self, width = 5)
        self._rbm_variable = tk.StringVar()
        self._rbn_film = ttk.Radiobutton(self, variable = self._rbm_variable, text = "Film", value = "film", command = lambda: self._ent_year.config(state = tk.NORMAL))
        self._rbn_tv = ttk.Radiobutton(self, variable = self._rbm_variable, text = "TV", value = "tv", command = self._clear_year)
        ttk.Label(self, text = "Title:").grid(row = 0, column = 0, rowspan = 2, padx = 5)
        self._ent_title.grid(row = 0, column = 1, rowspan = 2)
        ttk.Label(self, text = "Year:").grid(row = 0, column = 2, rowspan = 2, padx = 5)
        self._ent_year.grid(row = 0, column = 3, rowspan = 2)
        self._rbn_film.grid(row = 0, column = 4, padx = 10, sticky = tk.W)
        self._rbn_tv.grid(row = 1, column = 4, padx = 10, sticky = tk.W)
        ttk.Button(self, text = "Search", command = self._search).grid(row = 0, column = 5, rowspan = 2, padx = 5)

        self._ent_title.insert(0, title)
        self._ent_year.insert(0, year)
        if searchingfor == "tv":
            self._rbn_tv.invoke()
            self._rbn_film.config(state = tk.DISABLED)
            self._rbn_tv.config(state = tk.DISABLED)
        elif searchingfor == "film":
            self._rbn_film.invoke()
            self._rbn_film.config(state = tk.DISABLED)
            self._rbn_tv.config(state = tk.DISABLED)

        if searchingfor is not None:
            self._search()

    def _search(self):
        if self._rbm_variable.get() == "tv":
            print("tv")
        elif self._rbm_variable.get() == "film":
            year = int(self._ent_year.get())
            # for item in tmdb.filmSearch(self._ent_title.get(), year):
            #     print(item)
        else:
            messagebox.showwarning("Error", "You need to select if you're searching for TV or film")

    def _clear_year(self):
        self._ent_year.delete(0, tk.END)
        self._ent_year.config(state = tk.DISABLED)

def media_search(parent):
    # MediaSearchWindow(parent)
    MediaSearchWindow(parent, title = "1984", year = 1984, searchingfor="film")

def get_metadata(path):
    pass

if __name__ == "__main__":
    app = tkFilmViewer()
    app.mainloop()