import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from ftplib import FTP
import time
import os
import csv

global entry_barcode
global label_result
global barcode_var
global table
global total_price_var

db_path = "database.db"
ftp_host = "ftp.example.com"
ftp_username = "username"
ftp_password = "password"
ftp_backup_dir = "/path/path/database.db"

scanned_products = {}

def fetch_data_from_database(barcode):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT Stok_Adı,SATIŞ_FİYATI FROM URUN WHERE Barkodu=?", (barcode,))
    result = cursor.fetchone()
    conn.close()
    
    return result

def show_product_info(barcode):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        result = fetch_data_from_database(barcode)
        
        if result:
            product_name, price = result
            if barcode in scanned_products:
                scanned_products[barcode][0] += 1
            else:
                scanned_products[barcode] = [1, product_name, price]

            quantity, product_name, price = scanned_products[barcode]
            label_result.config(text=f"Ürün Adı: {product_name}\nFiyat: {price} TL\nOkutulan Adet: {quantity}")

            update_existing_row(barcode, product_name, price, quantity)
            update_total_price(price)
            
            save_to_csv(product_name, barcode, price, quantity)
            
        else:
            label_result.config(text="Bu ürün bulunamadı.")
        
        conn.close()
    except sqlite3.Error as e:
        label_result.config(text="Veritabanı bağlantı hatası.")

def update_existing_row(barcode, product_name, price, quantity):
    updated = False
    for item in table.get_children():
        if table.item(item, "values")[0] == barcode:
            table.item(item, values=(barcode, product_name, price, quantity, time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S")))
            updated = True
            break
    
    if not updated:
        table.insert("", "end", values=(barcode, product_name, price, quantity, time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S")))

def clear_table():
    for item in table.get_children():
        table.delete(item)
    total_price_var.set("Toplam: 0 TL")


def update_total_price(price):
    current_total = total_price_var.get()
    if current_total:
        current_total = float(current_total.split(" ")[1])
        new_total = current_total + float(price)
        total_price_var.set(f"Toplam: {new_total:.2f} TL")
    else:
        total_price_var.set(f"Toplam: {float(price):.2f} TL")
        
def is_valid_ean8(barcode):
    if len(barcode) != 8:
        return False
    
    try:
        total = 0
        for i in range(7):
            digit = int(barcode[i])
            if i % 2 == 0:
                total += digit
            else:
                total += digit * 3
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(barcode[7])
    except ValueError:
        return False

def on_barcode_change(*args):
    global barcode_var
    barcode = barcode_var.get()

    if len(barcode) == 8:
        if is_valid_ean8(barcode):
            show_product_info(barcode)
            barcode_var.set("")
        else:
            label_result.config(text="Ürün Bilgisi Bulunamadı.")
    elif len(barcode) == 13:
        show_product_info(barcode)
        barcode_var.set("")



def clear_all(event=None):
    clear_table()
    barcode_var.set("")
    label_result.config(text="")

def save_to_csv(product_name, barcode, price, quantity):
    today = time.strftime("%Y-%m-%d")
    csv_filename = "barkod_kayit_" + today + ".csv"
    
    if not os.path.exists(csv_filename):
        with open(csv_filename, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Ürün Adı", "Barkod", "Fiyat", "Adet", "Tarih", "Saat"])
    
    with open(csv_filename, "a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([product_name, barcode, price, quantity, time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S")])
def show_previous_records():
    try:
        today = time.strftime("%Y-%m-%d")
        csv_filename = "barkod_kayit_" + today + ".csv"
        
        if os.path.exists(csv_filename):
            with open(csv_filename, "r", newline="") as csv_file:
                csv_reader = csv.reader(csv_file)
                header = next(csv_reader)
                if header == ["Ürün Adı", "Barkod", "Fiyat", "Adet", "Tarih", "Saat"]:
                    clear_table()
                    for row in csv_reader:
                        product_name, barcode, price, quantity, date, _time = row
                        table.insert("", "end", values=(barcode, product_name, price, quantity, date, _time))
        else:
            messagebox.showinfo("Uyarı", "Önce en az bir kayıt oluşturmalısınız.")
    
    except Exception as e:
        messagebox.showerror("Hata", "Kayıtları okuma sırasında bir hata oluştu:\n" + str(e))


def backup_database():
    conn = sqlite3.connect(db_path)
    backup_path = "yedek_" + time.strftime("%d%m%Y%H%M%S") + ".db"
    conn_backup = sqlite3.connect(backup_path)
    conn.backup(conn_backup)
    conn_backup.close()
    conn.close()

    ftp = FTP(ftp_host)
    ftp.login(ftp_username, ftp_password)
    with open(backup_path, "rb") as file:
        ftp.cwd(ftp_backup_dir)
        ftp.storbinary("STOR " + backup_path, file)
    ftp.quit()

    os.remove(backup_path)
    print("Veritabanı yedekleme tamamlandı.")

def main():
    global entry_barcode
    global label_result
    global barcode_var
    global table
    global total_price_var

    root = tk.Tk()
    root.title("Ajax Barkod Sistemi V0.0.0.1")
    root.geometry("800x600")

    main_menu = tk.Menu(root)
    root.config(menu=main_menu)

    file_menu = tk.Menu(main_menu, tearoff=0)
    main_menu.add_cascade(label="Dosya", menu=file_menu)
    file_menu.add_command(label="Çıkış", command=root.quit)

    tools_menu = tk.Menu(main_menu, tearoff=0)
    main_menu.add_cascade(label="Araçlar", menu=tools_menu)
    tools_menu.add_command(label="Yedekleme Sihirbazı", command=backup_database)
    tools_menu.add_command(label="Eski Kayıtlar", command=show_previous_records)

    label_instruction = tk.Label(root, text="Barkod Numarasını Girin:")
    label_instruction.pack(pady=10)

    barcode_var = tk.StringVar()
    entry_barcode = tk.Entry(root, textvariable=barcode_var)
    entry_barcode.pack()

    barcode_var.trace("w", on_barcode_change)

    label_result = tk.Label(root, text="", font=("Helvetica", 12))
    label_result.pack()

    table = ttk.Treeview(root, columns=("Barkot", "Ürün Adı", "Fiyat", "Adet", "Tarih", "Saat"), show="headings")
    table.heading("Barkot", text="Barkot")
    table.heading("Ürün Adı", text="Ürün Adı")
    table.heading("Fiyat", text="Fiyat")
    table.heading("Adet", text="Adet")
    table.heading("Tarih", text="Tarih")
    table.heading("Saat", text="Saat")
    table.pack(pady=20)

    total_price_var = tk.StringVar()
    total_price_label = tk.Label(root, textvariable=total_price_var, font=("Helvetica", 14))
    total_price_label.pack()

    clear_button = tk.Button(root, text="Tabloyu Temizle", command=clear_all)
    clear_button.pack()

    root.bind("<Escape>", clear_all)

    root.mainloop()

if __name__ == "__main__":
    main()
