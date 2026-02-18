import customtkinter as ctk
from tkinter import filedialog, messagebox
import img2pdf
import fitz  # PyMuPDF
from PIL import Image
import io
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PDFFitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF Fit - Professional PDF Utility")
        self.geometry("600x650")

        # --- UI LAYOUT ---
        self.tabview = ctk.CTkTabview(self, width=550, height=480)
        self.tabview.pack(pady=20, padx=20)

        self.tab_compress = self.tabview.add("Fit (Compress)")
        self.tab_convert = self.tabview.add("Image to PDF")
        self.tab_merge = self.tabview.add("Merge PDFs")

        self.setup_compress_tab()
        self.setup_convert_tab()
        self.setup_merge_tab()

        # Status Bar
        self.status_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.status_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=200)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=10)

    # --- NEW: MERGE TAB ---
    def setup_merge_tab(self):
        label = ctk.CTkLabel(self.tab_merge, text="Merge Multiple PDFs", font=("Arial", 20, "bold"))
        label.pack(pady=15)

        info = ctk.CTkLabel(self.tab_merge,
                            text="Select two or more PDF files to combine them\ninto a single document.")
        info.pack(pady=10)

        btn = ctk.CTkButton(self.tab_merge, text="Select PDFs & Merge",
                            command=lambda: self.merge_logic(), height=40, fg_color="#27ae60")
        btn.pack(pady=30)

    # --- COMPRESS TAB ---
    def setup_compress_tab(self):
        label = ctk.CTkLabel(self.tab_compress, text="Smart Compression", font=("Arial", 20, "bold"))
        label.pack(pady=15)

        slider_frame = ctk.CTkFrame(self.tab_compress, fg_color="transparent")
        slider_frame.pack(pady=10, fill="x", padx=40)

        ctk.CTkLabel(slider_frame, text="High Compression\n(Smallest)", font=("Arial", 10), text_color="#ff7675").grid(
            row=0, column=0)
        self.slider = ctk.CTkSlider(slider_frame, from_=10, to=90, number_of_steps=8)
        self.slider.set(40)
        self.slider.grid(row=0, column=1, sticky="ew")
        slider_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(slider_frame, text="Low Compression\n(Best Quality)", font=("Arial", 10),
                     text_color="#55efc4").grid(row=0, column=2)

        self.val_label = ctk.CTkLabel(self.tab_compress, text="Current Quality: 40%", text_color="cyan")
        self.val_label.pack()
        self.slider.configure(command=lambda v: self.val_label.configure(text=f"Current Quality: {int(v)}%"))

        btn = ctk.CTkButton(self.tab_compress, text="Fit to Size (Compress)", command=self.compress_logic, height=40)
        btn.pack(pady=30)

    # --- CONVERT TAB ---
    def setup_convert_tab(self):
        label = ctk.CTkLabel(self.tab_convert, text="Images to PDF", font=("Arial", 20, "bold"))
        label.pack(pady=15)
        btn = ctk.CTkButton(self.tab_convert, text="Select JPEGs/PNGs", command=self.convert_logic, height=40)
        btn.pack(pady=30)

    # --- LOGIC: MERGE ---
    def merge_logic(self):
        files = filedialog.askopenfilenames(title="Select PDFs to Merge", filetypes=[("PDF", "*.pdf")])
        if len(files) < 2:
            messagebox.showwarning("Warning", "Please select at least 2 PDF files to merge.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not save_path: return

        try:
            self.status_label.configure(text="Status: Merging...", text_color="yellow")
            result_doc = fitz.open()

            for i, f in enumerate(files):
                with fitz.open(f) as m_doc:
                    result_doc.insert_pdf(m_doc)
                self.progress_bar.set((i + 1) / len(files))
                self.update()

            result_doc.save(save_path)
            result_doc.close()

            self.status_label.configure(text="Status: Merged!", text_color="green")
            messagebox.showinfo("Success", "Files merged successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.set(0)

    # --- LOGIC: COMPRESS ---
    def compress_logic(self):
        input_path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF", "*.pdf")])
        if not input_path: return
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not output_path: return

        try:
            quality = int(self.slider.get())
            self.status_label.configure(text="Status: Fitting...", text_color="yellow")
            doc = fitz.open(input_path)
            new_doc = fitz.open()

            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72), colorspace=fitz.csRGB)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG", quality=quality, optimize=True, subsampling=2)

                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, stream=img_byte_arr.getvalue())
                self.progress_bar.set((i + 1) / len(doc))
                self.update()

            new_doc.save(output_path, garbage=4, deflate=True, clean=True)
            new_doc.close()
            doc.close()
            self.status_label.configure(text="Status: Success!", text_color="green")
            messagebox.showinfo("Success", "PDF compressed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.set(0)

    # --- LOGIC: CONVERT ---
    def convert_logic(self):
        files = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not files: return
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not save_path: return

        try:
            self.status_label.configure(text="Status: Converting...", text_color="yellow")
            self.update()
            with open(save_path, "wb") as f:
                f.write(img2pdf.convert(files))
            self.status_label.configure(text="Status: Done!", text_color="green")
            messagebox.showinfo("Success", "PDF created!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = PDFFitApp()
    app.mainloop()