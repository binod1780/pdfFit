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
        self.geometry("1100x750")

        self.selected_pdf_path = None
        self.preview_images = []  # Keep references to prevent garbage collection

        # --- MAIN LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # LEFT SIDE: TOOLS
        self.tool_frame = ctk.CTkFrame(self)
        self.tool_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview = ctk.CTkTabview(self.tool_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_compress = self.tabview.add("Fit (Compress)")
        self.tab_convert = self.tabview.add("Image to PDF")
        self.tab_merge = self.tabview.add("Merge PDFs")

        # RIGHT SIDE: SCROLLABLE PREVIEW
        self.preview_frame = ctk.CTkFrame(self, width=400)
        self.preview_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.preview_title = ctk.CTkLabel(self.preview_frame, text="Document Preview", font=("Arial", 16, "bold"))
        self.preview_title.pack(pady=10)

        # The Scrollable Container for pages
        self.scroll_preview = ctk.CTkScrollableFrame(self.preview_frame, width=350, label_text="Pages")
        self.scroll_preview.pack(expand=True, fill="both", padx=10, pady=10)

        # BOTTOM: STATUS BAR (Fixed .grid call)
        self.status_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))

        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=300)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=10)

        self.setup_compress_tab()
        self.setup_convert_tab()
        self.setup_merge_tab()

    def update_preview(self, pdf_path):
        """Renders all pages into the scrollable preview frame."""
        # Clear existing preview
        for widget in self.scroll_preview.winfo_children():
            widget.destroy()
        self.preview_images = []

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            self.preview_title.configure(text=f"Preview: {page_count} Pages ({file_size:.2f} MB)")

            # Render each page
            for i in range(page_count):
                page = doc.load_page(i)
                # Low resolution (72 DPI) for the preview to keep it fast
                pix = page.get_pixmap(matrix=fitz.Matrix(72 / 72, 72 / 72))
                img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Resize for width of the scroll area
                aspect = pix.width / pix.height
                w = 300
                h = int(w / aspect)

                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(w, h))
                self.preview_images.append(ctk_img)  # Protect from GC

                page_label = ctk.CTkLabel(self.scroll_preview, image=ctk_img, text=f"Page {i + 1}", compound="bottom",
                                          pady=10)
                page_label.pack(pady=5)

            doc.close()
        except Exception as e:
            error_lbl = ctk.CTkLabel(self.scroll_preview, text=f"Error Loading Preview:\n{e}")
            error_lbl.pack(pady=20)

    def setup_compress_tab(self):
        ctk.CTkLabel(self.tab_compress, text="Smart Compression", font=("Arial", 20, "bold")).pack(pady=15)
        self.sel_btn = ctk.CTkButton(self.tab_compress, text="1. Select PDF File", command=self.select_pdf_action)
        self.sel_btn.pack(pady=10)

        slider_frame = ctk.CTkFrame(self.tab_compress, fg_color="transparent")
        slider_frame.pack(pady=20, fill="x", padx=40)
        ctk.CTkLabel(slider_frame, text="High Comp", font=("Arial", 10), text_color="#ff7675").grid(row=0, column=0)
        self.slider = ctk.CTkSlider(slider_frame, from_=10, to=90, number_of_steps=8)
        self.slider.set(40)
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)
        slider_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(slider_frame, text="Low Comp", font=("Arial", 10), text_color="#55efc4").grid(row=0, column=2)

        self.val_label = ctk.CTkLabel(self.tab_compress, text="Current Quality: 40%", text_color="cyan")
        self.val_label.pack()
        self.slider.configure(command=lambda v: self.val_label.configure(text=f"Current Quality: {int(v)}%"))

        self.comp_btn = ctk.CTkButton(self.tab_compress, text="2. Fit & Save PDF",
                                      command=self.compress_logic, state="disabled", height=40)
        self.comp_btn.pack(pady=30)

    def select_pdf_action(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.selected_pdf_path = path
            self.update_preview(path)
            self.comp_btn.configure(state="normal")
            self.status_label.configure(text=f"Selected: {os.path.basename(path)}")

    def compress_logic(self):
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not output_path: return
        try:
            quality = int(self.slider.get())
            self.status_label.configure(text="Status: Compressing...", text_color="yellow")
            doc = fitz.open(self.selected_pdf_path)
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
            new_doc.close();
            doc.close()
            messagebox.showinfo("Success", "File compressed!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.set(0)

    def setup_convert_tab(self):
        ctk.CTkLabel(self.tab_convert, text="Images to PDF", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkButton(self.tab_convert, text="Select Images & Save", command=self.convert_logic, height=40).pack(
            pady=20)

    def convert_logic(self):
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not files: return
        save_p = filedialog.asksaveasfilename(defaultextension=".pdf")
        if save_p:
            with open(save_p, "wb") as f: f.write(img2pdf.convert(files))
            messagebox.showinfo("Done", "PDF created.")

    def setup_merge_tab(self):
        ctk.CTkLabel(self.tab_merge, text="Merge Documents", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkButton(self.tab_merge, text="Select PDFs & Merge", command=self.merge_logic, height=40,
                      fg_color="#27ae60").pack(pady=20)

    def merge_logic(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if len(files) < 2: return
        save_p = filedialog.asksaveasfilename(defaultextension=".pdf")
        if save_p:
            res = fitz.open()
            for f in files:
                with fitz.open(f) as m: res.insert_pdf(m)
            res.save(save_p)
            messagebox.showinfo("Done", "Files merged.")


if __name__ == "__main__":
    app = PDFFitApp()
    app.mainloop()