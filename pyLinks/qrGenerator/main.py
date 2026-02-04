import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import qrcode
from PIL import Image, ImageTk
import pyperclip
import io

class QRGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Generator")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        self.qr_image = None  # przechowuje wygenerowany QR
        self.setup_ui()
    
    def setup_ui(self):
        # Frame główny
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Link input
        ttk.Label(main_frame, text="Link:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.link_entry = ttk.Entry(main_frame, width=50)
        self.link_entry.grid(row=0, column=1, columnspan=2, pady=5, padx=5)
        
        # Kolor QR
        ttk.Label(main_frame, text="Kolor QR:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.color_var = tk.StringVar(value="black")
        color_frame = ttk.Frame(main_frame)
        color_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        colors = ["black", "blue", "red", "green", "purple"]
        self.color_combo = ttk.Combobox(color_frame, textvariable=self.color_var, 
                                        values=colors, state="readonly", width=15)
        self.color_combo.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(color_frame, text="Custom...", 
                  command=self.choose_custom_color).grid(row=0, column=1)
        
        # Styl modułów
        ttk.Label(main_frame, text="Styl:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.style_var = tk.StringVar(value="square")
        styles = ["square", "rounded", "gapped"]
        self.style_combo = ttk.Combobox(main_frame, textvariable=self.style_var,
                                       values=styles, state="readonly", width=15)
        self.style_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Ramka
        self.frame_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Dodaj ramkę", 
                       variable=self.frame_var).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.frame_color_var = tk.StringVar(value="black")
        frame_color_combo = ttk.Combobox(main_frame, textvariable=self.frame_color_var,
                                        values=colors, state="readonly", width=15)
        frame_color_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Generuj button
        ttk.Button(main_frame, text="Generuj QR", 
                  command=self.generate_qr).grid(row=4, column=1, pady=15)
        
        # Preview
        ttk.Label(main_frame, text="Preview:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.preview_label = ttk.Label(main_frame, text="Wygeneruj QR żeby zobaczyć preview")
        self.preview_label.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Export buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Export PNG", 
                  command=self.export_png).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Kopiuj do schowka", 
                  command=self.copy_to_clipboard).grid(row=0, column=1, padx=5)
    
    def choose_custom_color(self):
        # otwiera color picker
        color = colorchooser.askcolor(title="Wybierz kolor")
        if color[1]:  # color[1] to hex
            self.color_var.set(color[1])
    
    def generate_qr(self):
        link = self.link_entry.get().strip()
        if not link:
            self.preview_label.config(text="Wpisz link!")
            return
        
        # Tworzymy QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4 if self.frame_var.get() else 2,
        )
        qr.add_data(link)
        qr.make(fit=True)
        
        # Pobieramy kolor
        fill_color = self.color_var.get()
        back_color = "white"
        
        # Generujemy obrazek
        if self.style_var.get() == "square":
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
        elif self.style_var.get() == "rounded":
            # rounded corners na modułach
            img = qr.make_image(fill_color=fill_color, back_color=back_color,
                               module_drawer=qrcode.image.styles.moduledrawers.RoundedModuleDrawer())
        else:  # gapped
            img = qr.make_image(fill_color=fill_color, back_color=back_color,
                               module_drawer=qrcode.image.styles.moduledrawers.GappedSquareModuleDrawer())
        
        # Ramka
        if self.frame_var.get():
            from PIL import ImageDraw
            img_with_frame = Image.new('RGB', 
                                       (img.size[0] + 20, img.size[1] + 20), 
                                       self.frame_color_var.get())
            img_with_frame.paste(img, (10, 10))
            img = img_with_frame
        
        self.qr_image = img
        
        # Preview
        # Resize do 300x300 dla GUI
        preview_img = img.copy()
        preview_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview_img)
        
        self.preview_label.config(image=photo, text="")
        self.preview_label.image = photo  # keep reference

    
    def export_png(self):
        # TODO: implement
        pass
    
    def copy_to_clipboard(self):
        # TODO: implement
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = QRGeneratorApp(root)
    root.mainloop()
