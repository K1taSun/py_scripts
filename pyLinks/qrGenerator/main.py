import io
import re
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox

import tempfile
import os
import sys

import qrcode
from PIL import Image, ImageTk, ImageDraw
try:
    from PIL import Image
    # Fallback dla starszych wersji Pillow
    RESAMPLE_MODE = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
except ImportError:
    RESAMPLE_MODE = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS


class QRGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Generator")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        self.qr_image = None  # przechowuje wygenerowany QR
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        # Frame główny
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Link input
        ttk.Label(main_frame, text="Link:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.link_entry = ttk.Entry(main_frame, width=50)
        self.link_entry.grid(row=0, column=1, columnspan=2, pady=5, padx=5)
        self.link_entry.bind('<KeyRelease>', lambda e: self.auto_preview())
        
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
        
        ttk.Button(btn_frame, text="Export PNG (⌘S)", 
                  command=self.export_png).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Kopiuj do schowka", 
                  command=self.copy_to_clipboard).grid(row=0, column=1, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Wpisz link żeby rozpocząć")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def setup_bindings(self):
        # Keyboard shortcuts
        self.root.bind('<Command-s>', lambda e: self.export_png())
        self.root.bind('<Control-s>', lambda e: self.export_png())
    
    def validate_url(self, url):
        # Basic URL validation
        if not url:
            return False, "Pusty link"
        
        # Sprawdź czy to URL
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if url_pattern.match(url):
            return True, "URL poprawny"
        
        # Jeśli nie zaczyna się od http, może to być zwykły tekst - też ok dla QR
        if len(url) > 0:
            return True, "Tekst OK (nie URL)"
        
        return False, "Niepoprawny format"
    
    def set_status(self, message, type="info"):

        self.status_var.set(message)
        # TODO: można dodać kolory dla różnych typów
    
    def auto_preview(self):
        # Auto-generuje po wpisaniu (z małym debounce)
        if hasattr(self, '_preview_timer'):
            self.root.after_cancel(self._preview_timer)
        self._preview_timer = self.root.after(500, self.generate_qr_silent)
    
    def generate_qr_silent(self):
        # Generuje bez pokazywania błędów (dla auto-preview)
        link = self.link_entry.get().strip()
        if not link:
            return
        try:
            self._generate_qr_internal(link)
        except:
            pass  # ignoruj błędy w auto-preview
    
    def choose_custom_color(self):
        # otwiera color picker
        color = colorchooser.askcolor(title="Wybierz kolor")
        if color[1]:  # color[1] to hex
            self.color_var.set(color[1])
            self.auto_preview()  # regeneruj po zmianie koloru
    
    def generate_qr(self):
        link = self.link_entry.get().strip()
        if not link:
            self.set_status("Wpisz link!", "error")
            self.preview_label.config(text="Wpisz link żeby wygenerować QR")
            return
        
        try:
            self._generate_qr_internal(link)
            self.set_status("QR wygenerowany ✓", "success")
        except Exception as e:
            self.set_status(f"Błąd: {str(e)}", "error")
            messagebox.showerror("Błąd", f"Nie udało się wygenerować QR:\n{str(e)}")
    
    def _generate_qr_internal(self, link):
        # Walidacja (opcjonalna - QR może zawierać dowolny tekst)
        is_valid, msg = self.validate_url(link)
        if not is_valid:
            self.set_status(f"Uwaga: {msg}", "warning")
        
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
        try:
            if self.style_var.get() == "square":
                img = qr.make_image(fill_color=fill_color, back_color=back_color)
            elif self.style_var.get() == "rounded":
                try:
                    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
                    img = qr.make_image(fill_color=fill_color, back_color=back_color,
                                       module_drawer=RoundedModuleDrawer())
                except ImportError:
                     self.set_status("Styl Rounded niedostępny (update qrcode)", "warning")
                     img = qr.make_image(fill_color=fill_color, back_color=back_color)
            else:  # gapped
                try:
                    from qrcode.image.styles.moduledrawers import GappedSquareModuleDrawer
                    img = qr.make_image(fill_color=fill_color, back_color=back_color,
                                       module_drawer=GappedSquareModuleDrawer())
                except ImportError:
                     self.set_status("Styl Gapped niedostępny (update qrcode)", "warning")
                     img = qr.make_image(fill_color=fill_color, back_color=back_color)
        except ValueError as e:
            # Błąd koloru - użyj domyślnego
            img = qr.make_image(fill_color="black", back_color="white")
            self.set_status("Użyto czarno-białego (błąd koloru)", "warning")
        
        # Ramka
        if self.frame_var.get():
            try:
                img_with_frame = Image.new('RGB', 
                                           (img.size[0] + 20, img.size[1] + 20), 
                                           self.frame_color_var.get())
                img_with_frame.paste(img, (10, 10))
                img = img_with_frame
            except:
                # Jeśli ramka nie działa, zostaw bez
                pass
        
        self.qr_image = img
        
        # Preview
        preview_img = img.copy()
        preview_img.thumbnail((300, 300), RESAMPLE_MODE)
        photo = ImageTk.PhotoImage(preview_img)
        
        self.preview_label.config(image=photo, text="")
        self.preview_label.image = photo

    
    def export_png(self):
        if not self.qr_image:
            self.set_status("Najpierw wygeneruj QR!", "error")
            messagebox.showwarning("Brak QR", "Najpierw wygeneruj kod QR")
            return
        
        try:
            # File dialog do wyboru gdzie zapisać
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile="qr_code.png"
            )
            
            if filepath:
                self.qr_image.save(filepath)
                self.set_status(f"Zapisano: {filepath}", "success")
                messagebox.showinfo("Sukces", f"QR zapisany:\n{filepath}")
        except Exception as e:
            self.set_status(f"Błąd zapisu: {str(e)}", "error")
            messagebox.showerror("Błąd", f"Nie udało się zapisać:\n{str(e)}")
    
    def copy_to_clipboard(self):
        if sys.platform != 'darwin':
            self.set_status("Kopiowanie tylko na macOS", "error")
            messagebox.showinfo("Info", "Funkcja kopiowania obrazu działa obecnie tylko na macOS.")
            return

        if not self.qr_image:
            self.set_status("Najpierw wygeneruj QR!", "error")
            messagebox.showwarning("Brak QR", "Najpierw wygeneruj kod QR")
            return
        
        try:
            # Zapisujemy temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                temp_path = tf.name
                self.qr_image.save(temp_path)
            
            # AppleScript do kopiowania obrazu (macOS)
            # Używamy '\xAB' i '\xBB' dla class specifiers
            script = f'set the clipboard to (read (POSIX file "{temp_path}") as \xABclass PNGf\xBB)'
            
            result = subprocess.run(['osascript', '-e', script], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                self.set_status("Skopiowano do schowka ✓", "success")
            else:
                raise Exception(result.stderr)
            
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            self.set_status(f"Błąd kopiowania: {str(e)}", "error")
            messagebox.showerror("Błąd", f"Nie udało się skopiować:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QRGeneratorApp(root)
    root.mainloop()
