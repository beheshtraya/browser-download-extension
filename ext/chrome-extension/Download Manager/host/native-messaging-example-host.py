import struct
import sys
import threading
import Queue
import os
import sqlite3
from KThread import KThread
from tkProgressBar import Meter, myURLOpener
from os.path import expanduser
from time import sleep

try:
    import mtTkinter as Tkinter
    import ttk
    import tkMessageBox, tkFileDialog
except ImportError:
    import tkinter

default_path = expanduser("~") + "\\Downloads"
progress_width = 1
chunk_size = 8192
exist_size = 0.00
total_size = 1.00

url = r'http://ftp.linux.org.tr/centos/6.5/isos/x86_64/CentOS-6.5-x86_64-bin-DVD1.iso'
path = r'C:\Users\beheshtray\Downloads\CentOS-6.5-x86_64-bin-DVD1.iso'


# Thread that reads messages from the webApp.
def read_thread_func(queue):
    message_number = 0
    while 1:
        # Read the message type (first 4 bytes).
        text_length_bytes = sys.stdin.read(4)

        if len(text_length_bytes) == 0:
            if queue:
                queue.put(None)
            sys.exit(0)

        # Read the message length (4 bytes).
        text_length = struct.unpack('i', text_length_bytes)[0]

        # Read the text (JSON object) of the message.
        text = sys.stdin.read(text_length).decode('utf-8')

        queue.put(text)


class NativeMessagingWindow(Tkinter.Frame):

    def __init__(self, queue):
        self.queue = queue
        self.t1 = None
        self.s = 1


        Tkinter.Frame.__init__(self)
        self.pack(pady=15, padx=15)

        self.master.resizable(0,0)

        self.download_start = False
        self.download_initial = False
        self.after_id = 0

        self.lbl_url = Tkinter.Label(self)
        self.lbl_url.grid(row=0, column=0, padx=2, pady=3, columnspan=1, sticky='E')
        self.lbl_url.config(text='Link:', height=1, justify='right', font=('Times', 10, 'bold'))

        self.url = ttk.Entry(self)
        self.url.grid(row=0, column=1, padx=2, pady=3, columnspan=2, sticky='W')
        self.url.config(width=100, justify='left')


        self.lbl_name = Tkinter.Label(self)
        self.lbl_name.grid(row=1, column=0, padx=2, pady=3, columnspan=1, sticky='E')
        self.lbl_name.config(text='Name:', height=1, justify='right', font=('Times', 10, 'bold'))

        self.name = ttk.Entry(self)
        self.name.grid(row=1, column=1, padx=2, pady=3, columnspan=1, sticky='W')
        self.name.config(width=95, justify='left')

        self.btn_path = ttk.Button(self)
        self.btn_path.config(width=3, text="*", command=self.choose_path)
        self.btn_path.grid(row=1, column=2, padx=2, columnspan=1, sticky='W')


        self.lbl_type = Tkinter.Label(self)
        self.lbl_type.grid(row=2, column=0, padx=2, pady=3, columnspan=1, sticky='E')
        self.lbl_type.config(text='Type:',height=1, justify='right', font=('Times', 10, 'bold'))

        self.type = Tkinter.Label(self)
        self.type.grid(row=2, column=1, padx=2, pady=3, columnspan=2, sticky='W')
        self.type.config(height=1, justify='left')



        self.lbl_size = Tkinter.Label(self)
        self.lbl_size.grid(row=3, column=0, padx=2, pady=3, columnspan=1, sticky='E')
        self.lbl_size.config(text='Size:',height=1, justify='right', font=('Times', 10, 'bold'))

        self.size = Tkinter.Label(self)
        self.size.grid(row=3, column=1, padx=2, pady=3, columnspan=2, sticky='W')
        self.size.config(height=1, justify='left')



        self.lbl_resume = Tkinter.Label(self)
        self.lbl_resume.grid(row=4, column=0, padx=2, pady=3, columnspan=1, sticky='E')
        self.lbl_resume.config(text='Resume:',height=1, justify='right' , font=('Times', 10, 'bold'))

        self.resume = Tkinter.Label(self)
        self.resume.grid(row=4, column=1, padx=2, pady=3, columnspan=2, sticky='W')
        self.resume.config(height=1, justify='left')

        self.frm_btns = ttk.Frame(self)
        self.frm_btns.grid(row=8, column=1, padx=2, pady=20, columnspan=2, sticky='W')

        self.btn_cancel = ttk.Button(self.frm_btns, text='Cancel', command=self.close)
        self.btn_cancel.pack(side='left')
        ##      grid(row=0, column=1, padx=2, pady=20, columnspan=2, sticky='W')

        self.btn_download = ttk.Button(self.frm_btns, text='Download', command=self.prepare_download)
        self.btn_download.pack(side='left')
        ##      grid(row=0, column=2, padx=2, pady=20, columnspan=1, sticky='W')

        self.btn_save = ttk.Button(self.frm_btns, text='Save', command=self.save)
        self.btn_save.pack(side='left')
        ##      grid(row=6, column=3, padx=2, pady=20, columnspan=1, sticky='W')

        self.after(100, self.processMessages)

        # global url
        # global path
        # self.url.insert(0, url)
        # self.name.insert(0, path)

    def download_core(self, webPage, outputFile):
        global exist_size
        global chunk_size

        while True:
            data = webPage.read(chunk_size)
            if not data:
                break
            outputFile.write(data)
            exist_size += len(data)

        return

    def download(self, link, path):
        global exist_size
        global total_size

        ## Define download progress bar widget for the first time
        if not self.download_initial:
            # self.m = Meter(self.frm_btns, relief='ridge', bd=1, fillcolor='green')
            # self.m.pack()
            self.m = Meter(self, relief='ridge', bd=1, fillcolor='#3AA130', width=600)
            self.m.grid(row=7, column=1, padx=2, pady=20, columnspan=2, sticky='W')
            #m.pack(fill='x')
            self.m.set(0.00, 'Starting download ...')
            self.download_initial = True

        ## Check for file exists
        if os.path.exists(path):
            outputFile = open(path,"ab")
            exist_size = os.path.getsize(path)
        else:
            outputFile = open(path,"wb")

        myUrlclass = myURLOpener()
        if exist_size != 0:
            ## If the file exists, then only download the remainder
            myUrlclass.addheader("Range", "bytes=%s-" % exist_size)

        try:
            webPage = myUrlclass.open(str(link))
            remain_size = float(webPage.headers['Content-Length'])
            total_size = remain_size + exist_size
            print("\n")
            print("File size: " + str("%.2f" % (float(total_size) / (1024 * 1024))) + " MB\n")
            print("Size already downloaded " + str("%.2f" % (float(exist_size) / (1024 * 1024))) + " MB\n")
            ## If the file exists, but we already have the whole thing, don't download again
            if total_size == exist_size:
                print("File already has been downloaded \n")

            value = exist_size / total_size
            self.m.after(10, lambda: self.progressBar(self.m, value))


        except:
            return "Error on opening link"

        try:
            print("Downloading ...\n")

            self.download_core(webPage, outputFile)
            outputFile.close()
            webPage.close()
            tkMessageBox.showinfo(title=self.name.get(), message='Download completed successfully')
            self.close()

        except:
            outputFile.close()
            return "Error"

    def progressBar(self, meter, value):
        global exist_size
        global total_size

        meter.set(value)
        if value < 1.0:
            value = exist_size / total_size
            meter.after(10, lambda: self.progressBar(meter, value))
        else:
            meter.set(value, 'Download Finished')

    def prepare_download(self):
        # global url
        # global path
        url = self.url.get()
        path = self.name.get()
        self.download_start = not self.download_start
        print self.download_start

        if self.download_start:
            self.t1 = KThread(target=self.download, args=(url, path))
            self.t1.start()
            self.btn_download.config(text='Pause')

            self.lbl_speed = Tkinter.Label(self)
            self.lbl_speed.grid(row=5, column=0, padx=2, pady=3, columnspan=1, sticky='E')
            self.lbl_speed.config(text='Speed:', height=1, justify='right', font=('Times', 10, 'bold'))

            self.speed = Tkinter.Label(self)
            self.speed.grid(row=5, column=1, padx=2, pady=3, columnspan=2, sticky='W')
            self.speed.config(height=1, justify='left')

            self.lbl_remaining_time = Tkinter.Label(self)
            self.lbl_remaining_time.grid(row=6, column=0, padx=2, pady=3, columnspan=1, sticky='E')
            self.lbl_remaining_time.config(text='Remaining time:', height=1, justify='right', font=('Times', 10, 'bold'))

            self.remaining_time = Tkinter.Label(self)
            self.remaining_time.grid(row=6, column=1, padx=2, pady=3, columnspan=2, sticky='W')
            self.remaining_time.config(height=1, justify='left')

            self.after(100, self.speed_calculate, exist_size)
            self.after(2000, self.time_calculate)
            return
        else:
            self.lbl_speed.destroy()
            self.speed.destroy()
            self.lbl_remaining_time.destroy()
            self.remaining_time.destroy()
            self.btn_download.config(text='Download')
            self.t1.kill()

    def speed_calculate(self, last):
        update_time = 3

        s = exist_size - last
        self.s = s
        s = s / update_time / 1024.0
        s = round(s, 2)
        s = str(s)
        self.speed.config(text=str(s + ' KB/s'))
        b = exist_size
        self.after(update_time * 1000, self.speed_calculate, b)

    def time_calculate(self):
        global exist_size
        global total_size

        sp = 1
        if self.s != 0:
            sp = self.s

        remaining_time = int((total_size - exist_size) / sp)

        if remaining_time < 0 or self.s == 0:
            self.remaining_time.config(text='')
            self.after(2000, self.time_calculate)

        elif remaining_time < 60:
            _sec = str(remaining_time) + ' seconds'
            self.remaining_time.config(text=_sec)
            self.after(2000, self.time_calculate)

        elif remaining_time < 3600:
            _min = int(remaining_time/60)
            self.remaining_time.config(text=str(_min) + ' minutes')
            self.after(30000, self.time_calculate)

        else:
            hour = int(remaining_time/3600)
            _min = (remaining_time - hour*3600)/60
            self.remaining_time.config(text=str(hour) + ' hours and ' + str(_min) + ' minutes')
            self.after(30000, self.time_calculate)

    def choose_path(self):
        path = tkFileDialog.asksaveasfilename(initialdir=default_path, initialfile=self.name.get())
        name = path.replace('/', '\\')
        if name != '':
            self.name.delete(0, Tkinter.END)
            self.name.insert(0, name)
        return

    def save(self):
        con = sqlite3.connect('downloads.db')
        cur = con.cursor()
        return

    def processMessages(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            if message == None:
                self.quit()
                return
            self.log(message)

        self.after(100, self.processMessages)

    def log(self, message):

        if message.__contains__('url:'):
            i = message.find(':')
            message = message[i + 1:-1]
            self.url.insert(0, message)
            #self.url.config(state=Tkinter.DISABLED)

        elif message.__contains__('name:'):
            i = message.find(':')
            name = default_path + '\\' + message[i+1:-1]
            self.name.insert(0, name)
            self.master.title(message[i+1:-1])

        elif message.__contains__('type:'):
            i = message.find(':')
            message = message[i+1:-1]
            self.type.config(text = message)

        elif message.__contains__('size:'):
            i = message.find(':')
            size = int(message[i+1:-1])
            size /= 1024
            message = str(size) + ' KB'
            self.size.config(text = message)

        elif message.__contains__('resume:'):
            i = message.find(':')
            message = message[i+1:-1]
            self.resume.config(text = message)
            if message == 'Yes':
                self.resume.config(foreground = '#3AA130')
            elif message == 'No':
                self.resume.config(foreground = 'red')

    def close(self):
        global total_size
        global exist_size

        if self.download_initial and total_size != exist_size:
            answer = tkMessageBox.askyesno('Keep file', 'Do you want to keep uncompleted file? ')
            if not answer:
                self.t1.kill()
                sleep(0.5)
                path = self.name.get()
                os.remove(path)

        self.master.destroy()


def Main():
    queue = Queue.Queue()

    main_window = NativeMessagingWindow(queue)
    main_window.master.title('beheshtraya download manager')

    thread = threading.Thread(target=read_thread_func, args=(queue,))
    thread.daemon = True
    thread.start()

    main_window.mainloop()


if __name__ == '__main__':
    Main()
    os._exit(0)
