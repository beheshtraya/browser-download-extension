'''Michael Lange <klappnase (at) freakmail (dot) de>
The Meter class provides a simple progress bar widget for Tkinter.

INITIALIZATION OPTIONS:
The widget accepts all options of a Tkinter.Frame plus the following:

    fillcolor -- the color that is used to indicate the progress of the
                 corresponding process; default is "orchid1".
    value -- a float value between 0.0 and 1.0 (corresponding to 0% - 100%)
             that represents the current status of the process; values higher
             than 1.0 (lower than 0.0) are automagically set to 1.0 (0.0); default is 0.0 .
    text -- the text that is displayed inside the widget; if set to None the widget
            displays its value as percentage; if you don't want any text, use text="";
            default is None.
    font -- the font to use for the widget's text; the default is system specific.
    textcolor -- the color to use for the widget's text; default is "black".

WIDGET METHODS:
All methods of a Tkinter.Frame can be used; additionally there are two widget specific methods:

    get() -- returns a tuple of the form (value, text)
    set(value, text) -- updates the widget's value and the displayed text;
                        if value is omitted it defaults to 0.0 , text defaults to None .
'''

import Tkinter
import os
import urllib
import threading

chunk_size = 8192
progress = 0
size = 1


class Meter(Tkinter.Frame):
    def __init__(self, master, width=300, height=20, bg='white', fillcolor='orchid1',\
                 value=0.0, text=None, font=None, textcolor='black', *args, **kw):
        Tkinter.Frame.__init__(self, master, bg=bg, width=width, height=height, *args, **kw)
        self._value = value

        self._canv = Tkinter.Canvas(self, bg=self['bg'], width=self['width'], height=self['height'],\
                                    highlightthickness=0, relief='flat', bd=0)
        self._canv.pack(fill='both', expand=1)
        self._rect = self._canv.create_rectangle(0, 0, 0, self._canv.winfo_reqheight(), fill=fillcolor,\
                                                 width=0)
        self._text = self._canv.create_text(self._canv.winfo_reqwidth()/2, self._canv.winfo_reqheight()/2,\
                                            text='', fill=textcolor)
        if font:
            self._canv.itemconfigure(self._text, font=font)

        self.set(value, text)
        self.bind('<Configure>', self._update_coords)


    def _update_coords(self, event):
        '''Updates the position of the text and rectangle inside the canvas when the size of
        the widget gets changed.'''
        # looks like we have to call update_idletasks() twice to make sure
        # to get the results we expect
        self._canv.update_idletasks()
        self._canv.coords(self._text, self._canv.winfo_width()/2, self._canv.winfo_height()/2)
        self._canv.coords(self._rect, 0, 0, self._canv.winfo_width()*self._value, self._canv.winfo_height())
        self._canv.update_idletasks()

    def get(self):
        return self._value, self._canv.itemcget(self._text, 'text')

    def set(self, value=0.0, text=None):
        #make the value failsafe:
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        self._value = value
        if text == None:
            #if no text is specified use the default percentage string:
            text = str(int(round(100 * value))) + ' %'
        self._canv.coords(self._rect, 0, 0, self._canv.winfo_width()*value, self._canv.winfo_height())
        self._canv.itemconfigure(self._text, text=text)
        self._canv.update_idletasks()


class myURLOpener(urllib.FancyURLopener):
    """Create sub-class in order to override error 206.  This error means a
       partial file is being sent,
       which is ok in this case.  Do nothing with this error.
    """
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
        pass


def download_core(link, outputFile, start_byte=0):
    global progress
    global size

    myUrlclass = myURLOpener()
    if start_byte != 0:
        #If the file exists, then only download the remainder
        myUrlclass.addheader("Range", "bytes=%s-" % start_byte)

    try:
        webPage = myUrlclass.open(str(link))
        size = int(webPage.headers['Content-Length'])
        print("\n")
        print("File size: " + str("%.2f" % (float(size) / (1024 * 1024))) + " MB\n")
        print("Size already downloaded " + str("%.2f" % (float(start_byte) / (1024 * 1024))) + " MB\n")
        #If the file exists, but we already have the whole thing, don't download again
        if size == start_byte:
            print("File already has been downloaded \n")

    except:
        return "Error on opening link"

    try:
        print("Downloading ...\n")
        numBytes = 0

        while True:
            data = webPage.read(chunk_size)
            if not data:
                break
            outputFile.write(data)
            numBytes += len(data)
            progress = numBytes

        webPage.close()

    except:
        return "Error"


def download(link, path):
    url = link
    existSize = 0
    dlFile = path
    if os.path.exists(dlFile):
        outputFile = open(dlFile,"ab")
        existSize = os.path.getsize(dlFile)
    else:
        outputFile = open(dlFile,"wb")

    result = download_core(url, outputFile, existSize)
    outputFile.close()

    return "Download finish successful"


def progressBar(meter, value):
    global progress
    global size
    print progress
    print size
    meter.set(value)
    if value < 1.0:
        value = float(progress)/float(size)
        meter.after(50, lambda: progressBar(meter, value))
    else:
        meter.set(value, 'Demo successfully finished')

# if __name__ == '__main__':


def dl(url, path):
    download_thread = threading.Thread(target=download, args=(url, path))
    download_thread.start()

    root = Tkinter.Tk(className='meter demo')
    m = Meter(root, relief='ridge', bd=3)
    m.pack(fill='x')
    m.set(0.0, 'Starting demo...')
    m.after(1000, lambda: progressBar(m, 0.0))
    root.mainloop()


