# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import re
import time
import datetime

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        # set title
        self.master.title('Mesh GUI Test')
        # set window variable
        self.master.resizable(width=True, height=True)
        # common panel
        common_panel = tk.LabelFrame(self, text='common')
        common_panel.grid(row=0, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.com = ttk.Combobox(common_panel)
        self.com.grid(row=0, column=0, columnspan=2, padx=1, pady=3, sticky=tk.NSEW)
        self.mySerial = None
        self.mySerFlag = None
        tk.Button(common_panel, text='refresh', width=10, command=self.refresh_serial).grid(row=0, column=2, padx=1,
                pady=3, sticky=tk.NSEW)
        self.refresh_serial()
        self.mybaudrqate = ttk.Combobox(common_panel, width=10)
        self.mybaudrqate.grid(row=1, column=0, padx=1, pady=3, sticky=tk.NSEW)
        self.mybaudrqate['value'] = [50, 75, 110, 134, 150, 200, 300, 1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600,
                115200, 230400, 460800, 500000, 921600]
        self.mybaudrqate.current(15)
        tk.Button(common_panel, text='open', width=10, command=self.mesh_serial_open).grid(row=1, column=1, padx=1,
                pady=3, sticky=tk.NSEW)
        tk.Button(common_panel, text='close', width=10, command=self.mesh_serial_close).grid(row=1, column=2, padx=1,
                pady=3, sticky=tk.NSEW)
        # operate panel
        tk.Label(common_panel, relief='solid', text='Data Len').grid(row=2, column=0, padx=3, pady=0, sticky=tk.NSEW)
        tk.Label(common_panel, relief='solid', text='Count').grid(row=2, column=1, padx=3, pady=0, sticky=tk.NSEW)
        tk.Button(common_panel, text='Msg Send', command=self.msg_send).grid(row=2, column=2, padx=1, pady=1,
                sticky=tk.NSEW)
        self.len_entry = tk.Entry(common_panel, width=10, relief='groove')
        self.len_entry.grid(row=3, column=0, padx=3, pady=0, sticky=tk.NSEW)
        self.len_entry.insert(tk.END, '8')
        self.send_count_label = tk.StringVar()
        tk.Label(common_panel, relief='groove', textvariable=self.send_count_label).grid(row=3, column=1, padx=3, pady=0,
                sticky=tk.NSEW)
        tk.Button(common_panel, text='Auto Test', command=self.auto_test).grid(row=3, column=2, padx=1, pady=1,
                sticky=tk.NSEW)
        # valiable
        self.send_count = 0
        self.panel_row = 0
        self.panel_column = 0
        self.total_column = 1
        self.server_dict = dict()
        self.log_window = None
        # status bar
        self.status = tk.StringVar()
        self.status.set('COM Closed')
        tk.Label(self, textvariable=self.status, anchor='e').grid(row=20, column=0, columnspan=20, sticky=tk.NSEW)

    def refresh_serial(self):
        current_com = self.com.get()
        # refresh serial
        ser_list = list(serial.tools.list_ports.comports())
        ser_list.sort()
        current_index = 0
        if current_com:
            for index in range(len(ser_list)):
                if current_com.split()[0] == ser_list[index].device:
                    current_index = index
                    break
        self.com['value'] = ser_list
        if len(ser_list):
            self.com.current(current_index)

    def mesh_serial_open(self):
        ser_name = self.com.get().split()[0]
        if self.mySerial:
            self.mySerial.close()

        self.mySerial = serial.Serial(ser_name, int(self.mybaudrqate.get()))
        if self.mySerial.isOpen():
            # add log windows
            new_log_win = tk.Toplevel(self)
            new_log_win.title(self.mySerial)
            frm = tk.LabelFrame(new_log_win)
            frm.grid(row=0, column=1, columnspan=6, padx=1, pady=3, sticky=tk.NSEW)
            self.log_window = tk.Text(frm, bg='white', height=60)
            self.log_window.pack(side=tk.LEFT, fill=tk.Y)
            scroll = tk.Scrollbar(frm)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            scroll.config(command=self.log_window.yview)
            self.log_window.config(yscrollcommand=scroll.set)
            tk.Button(new_log_win, text='Clear', command=lambda: self.log_window.delete(1.0, tk.END)).grid(row=1,
                        column=5, padx=1, pady=3, sticky=tk.NSEW)
            self.mySerFlag = True
            self.status.set('%s Open' % ser_name)
            th = threading.Thread(target=self.rcv_data)
            th.start()

    def mesh_serial_close(self):
        if self.mySerial:
            self.mySerFlag = False
            self.mySerial.close()
            self.status.set('%s Closed' % self.mySerial.name)

    def rcv_data(self):
        while self.mySerFlag:
            com_data = self.mySerial.readline()
            if com_data:
                self.log_window.insert(tk.END, com_data.decode('utf-8', 'ignore'))
                self.log_window.see(tk.END)
                if self.log_window.count(1.0, tk.END, 'lines') == 30000:
                    data_save = self.log_window.get(1.0, tk.END)
                    self.log_window.delete(1.0, tk.END)
                    def dump_file(data_save):
                        timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                        file_name = 'Log_%s.txt' % timestamp
                        f = open(file_name, 'a')
                        f.write(data_save)
                        f.close()
                    threading.Thread(target=dump_file, args=(data_save,)).start()
                strCom = com_data.decode()
                strCom = re.sub(r',', ' ', strCom)
                strRcv = strCom.split()
                if len(strRcv) == 12:
                    update_data = dict()
                    update_data['addr'] = strRcv[1]
                    update_data['len'] = strRcv[3]
                    update_data['diff'] = strRcv[5]
                    update_data['count'] = strRcv[7]
                    update_data['ttl1'] = strRcv[9]
                    update_data['ttl2'] = strRcv[11]
                    if self.server_dict.get(update_data['addr'], 'no') == 'no':
                        threading.Thread(target=self.add_panel, args=(update_data,)).start()
                    else:
                        threading.Thread(target=self.update_panel_data, args=(update_data,)).start()

    def add_panel(self, update_data):
        server_panel = tk.LabelFrame(self, text='server')
        lock = threading.Lock()
        lock.acquire()
        if self.panel_row == 3:
            self.panel_row = 1
            self.panel_column += 1
        else:
            self.panel_row += 1
        server_panel.grid(row=self.panel_row, column=self.panel_column, sticky=tk.NSEW)
        lock.release()
        # line 1
        tk.Label(server_panel, relief='solid', text='Address', width=8).grid(row=0, column=0, padx=1, pady=1,
                sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='Rcv Count', width=8).grid(row=0, column=1, padx=1, pady=1,
                sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='Lost Rate', width=8).grid(row=0, column=2, padx=1, pady=1,
                sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='Time Use', width=8).grid(row=0, column=3, padx=1, pady=1, sticky=tk.NSEW)
        tk.Label(server_panel, relief='groove', text=update_data['addr'], width=8, bg='yellow').grid(row=1, column=0, padx=1, pady=1,
                sticky=tk.NSEW)
        rcv_count_var = tk.Label(server_panel, relief='groove')
        lost_rate_var = tk.Label(server_panel, relief='groove')
        time_use_var = tk.Label(server_panel, relief='groove')
        rcv_count_var.grid(row=1, column=1, padx=1, pady=1, sticky=tk.NSEW)
        lost_rate_var.grid(row=1, column=2, padx=1, pady=1, sticky=tk.NSEW)
        time_use_var.grid(row=1, column=3, padx=1, pady=1, sticky=tk.NSEW)

        tk.Label(server_panel, relief='solid', text='HopCome', width=8).grid(row=2, column=0, padx=1, pady=1,
                sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='HopBack', width=8).grid(row=2, column=1, padx=1, pady=1,
                sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='Min').grid(row=2, column=2, padx=1, pady=1, sticky=tk.NSEW)
        tk.Label(server_panel, relief='solid', text='Avg').grid(row=2, column=3, padx=1, pady=1, sticky=tk.NSEW)
        relay1_var = tk.Label(server_panel, relief='groove')
        relay2_var = tk.Label(server_panel, relief='groove')
        min_var = tk.Label(server_panel, relief='groove')
        avg_var = tk.Label(server_panel, relief='groove')
        relay1_var.grid(row=3, column=0, padx=1, pady=1, sticky=tk.NSEW)
        relay2_var.grid(row=3, column=1, padx=1, pady=1, sticky=tk.NSEW)
        min_var.grid(row=3, column=2, padx=1, pady=1, sticky=tk.NSEW)
        avg_var.grid(row=3, column=3, padx=1, pady=1, sticky=tk.NSEW)

        server_data = dict()
        server_data['rcv_count_var'] = rcv_count_var
        server_data['lost_rate_var'] = lost_rate_var
        server_data['time_use_var'] = time_use_var
        server_data['relay1_var'] = relay1_var
        server_data['relay2_var'] = relay2_var
        server_data['min_var'] = min_var
        server_data['avg_var'] = avg_var
        server_data['count'] = 0
        server_data['min'] = 0xFFFF
        server_data['avg'] = 0
        self.server_dict[update_data['addr']] = server_data
        self.update_panel_data(update_data)

    def update_panel_data(self, update_data):
        server_data = self.server_dict[update_data['addr']]
        server_data['count'] += 1
        cur_time = int(update_data['diff'])
        cur_len = int(update_data['len'])
        cur_ttl1 = 11-int(update_data['ttl1'])
        cur_ttl2 = 11-int(update_data['ttl2'])
        if server_data['min'] > cur_time:
            server_data['min'] = cur_time
        server_data['avg'] = (server_data['avg'] * (server_data['count']-1) + cur_time) / server_data['count']
        self.update_label(server_data['rcv_count_var'], server_data['count'])
        lost_rate_value = '%.2f %%' % ((self.send_count - server_data['count']) / self.send_count * 100)
        self.update_label(server_data['lost_rate_var'], lost_rate_value)

        self.update_label(server_data['relay1_var'], cur_ttl1)
        self.update_label(server_data['relay2_var'], cur_ttl2)
        self.update_label(server_data['time_use_var'], cur_time)

        self.update_label(server_data['min_var'], server_data['min'])
        self.update_label(server_data['avg_var'], '%.2f' % server_data['avg'])
        name_hop = 'hop_%d' % (cur_ttl1+cur_ttl2)
        name_len = 'len_%d' % cur_len
        if self.server_dict.get(name_len, 'no') == 'no':
            total_panel = tk.LabelFrame(self, text=name_len)
            lock = threading.Lock()
            lock.acquire()
            total_panel.grid(row=0, column=self.total_column, sticky=tk.NSEW)
            self.total_column += 1
            lock.release()
            total_data = dict()
            total_data['raw_data'] = []
            total_data['stat_data'] = [0]*30
            total_data['row'] = 1
            total_data['panel'] = total_panel
            tk.Label(total_panel, relief='solid', text='Hop', width=8).grid(row=0, column=0, padx=1, pady=1,
                    sticky=tk.NSEW)
            tk.Label(total_panel, relief='solid', text='Max', width=8).grid(row=0, column=1, padx=1, pady=1,
                    sticky=tk.NSEW)
            tk.Label(total_panel, relief='solid', text='Min', width=8).grid(row=0, column=2, padx=1, pady=1,
                    sticky=tk.NSEW)
            tk.Label(total_panel, relief='solid', text='Avg', width=8).grid(row=0, column=3, padx=1, pady=1,
                                                                                 sticky=tk.NSEW)


            self.server_dict[name_len] = total_data
            self.update_total_panel(name_len, name_hop, cur_time)
        else:
            self.update_total_panel(name_len, name_hop, cur_time)

    def update_total_panel(self, name_len, name_hop, time_use):
        total_data = self.server_dict[name_len]
        lock = threading.Lock()
        def update_panel_data():
            hop_data = total_data[name_hop]
            stat_index = time_use // 10
            if stat_index > 29:
                stat_index = 29
            lock.acquire()
            #total_data['raw_data'].append(time_use)
            #if len(total_data['raw_data']) == 101:
            #    pass
            total_data['stat_data'][stat_index] += 1
            hop_data['count'] += 1
            if hop_data['max'] < time_use:
                hop_data['max'] = time_use
            if hop_data['min'] > time_use:
                hop_data['min'] = time_use
            hop_data['avg'] = (hop_data['avg'] * (hop_data['count'] - 1) + time_use) / hop_data['count']
            self.update_label(hop_data['max_var'], hop_data['max'])
            self.update_label(hop_data['min_var'], hop_data['min'])
            self.update_label(hop_data['avg_var'], '%.2f' % hop_data['avg'])
            lock.release()

        if total_data.get(name_hop, 'no') == 'no':
            lock.acquire()
            cur_row = total_data['row']
            total_data['row'] += 1
            lock.release()
            tk.Label(total_data['panel'] , relief='groove', text=name_hop).grid(row=cur_row, column=0, padx=1,
                                                                                pady=1, sticky=tk.NSEW)
            max_var = tk.Label(total_data['panel'] , relief='groove')
            min_var = tk.Label(total_data['panel'] , relief='groove')
            avg_var = tk.Label(total_data['panel'] , relief='groove')
            max_var.grid(row=cur_row, column=1, padx=1, pady=1, sticky=tk.NSEW)
            min_var.grid(row=cur_row, column=2, padx=1, pady=1, sticky=tk.NSEW)
            avg_var.grid(row=cur_row, column=3, padx=1, pady=1, sticky=tk.NSEW)
            total_data[name_hop] = {'max_var': max_var, 'min_var': min_var, 'avg_var': avg_var,
                                    'count': 0, 'max': 0, 'min': 0xFFFF, 'avg': 0}
            update_panel_data()
        else:
            update_panel_data()

    def msg_send(self):
        if not self.mySerial:
            return
        if not self.mySerial.isOpen():
            return
        self.send_count += 1
        if self.send_count % 5000 == 0:
            self.len_entry.delete(0, tk.END)
            self.len_entry.insert(tk.END, (self.send_count // 5000 + 1) * 8)
            for server_data in self.server_dict.values():
                server_data['max'] = 0
                server_data['min'] = 0xFFFF
                server_data['avg'] = 0
        self.send_count_label.set(self.send_count)
        order_out = [0xAA, int(self.len_entry.get())]
        self.mySerial.write(bytearray(order_out))

    def auto_test(self):
        self.msg_send()
        len = int(self.len_entry.get())
        threading.Timer(len // 4, self.auto_test).start()

    def update_label(self, mylabel, value):
        changeColor = 'white'
        if mylabel['text'] > str(value):
            changeColor = 'green'
        if mylabel['text'] < str(value):
            changeColor = 'red'
        mylabel.configure(bg=changeColor)
        mylabel.config(text=str(value))


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)

    def destroy_handle():
        if app.mySerial:
            app.mySerFlag = False
            app.mySerial.close()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", destroy_handle)
    app.mainloop()



