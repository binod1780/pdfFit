import customtkinter as ctk
from tkinter import filedialog, messagebox
import img2pdf
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PDFFitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF Fit - Professional PDF Utility")
        self.geometry("1200x850")

        self.selected_pdf_path = None
        self.selected_images = []
        self.merge_list = []
        self.preview_images = []

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
        self.tab_split = self.tabview.add("Split PDF")

        # RIGHT SIDE: SCROLLABLE PREVIEW
        self.preview_frame = ctk.CTkFrame(self, width=400)
        self.preview_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.preview_title = ctk.CTkLabel(self.preview_frame, text="Selection Preview", font=("Arial", 16, "bold"))
        self.preview_title.pack(pady=10)

        self.scroll_preview = ctk.CTkScrollableFrame(self.preview_frame, width=350, label_text="Items")
        self.scroll_preview.pack(expand=True, fill="both", padx=10, pady=10)

        # BOTTOM: STATUS BAR
        self.status_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready")
        self.status_label.pack(side="left")
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=300)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=10)

        self.setup_compress_tab()
        self.setup_convert_tab()
        self.setup_merge_tab()
        self.setup_split_tab()

    # --- SHARED PREVIEW ENGINE ---
    def clear_preview(self):
        for widget in self.scroll_preview.winfo_children(): widget.destroy()
        self.preview_images = []

    def update_pdf_preview(self, pdf_path):
        self.clear_preview()
        try:
            doc = fitz.open(pdf_path)
            self.preview_title.configure(text=f"Previewing: {os.path.basename(pdf_path)}")
            pages_to_show = min(len(doc), 15)
            for i in range(pages_to_show):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.6, 0.6))
                self.add_to_preview(pix.samples, pix.width, pix.height, f"Page {i + 1}")
            doc.close()
        except:
            pass

    def update_image_preview(self, image_paths):
        self.clear_preview()
        self.preview_title.configure(text=f"Image Preview: {len(image_paths)} Files")
        for path in image_paths:
            try:
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    img.thumbnail((300, 400))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.preview_images.append(ctk_img)
                    lbl = ctk.CTkLabel(self.scroll_preview, image=ctk_img, text=os.path.basename(path),
                                       compound="bottom", pady=10)
                    lbl.pack(pady=5)
            except:
                continue

    def add_to_preview(self, samples, w_orig, h_orig, label_text):
        img_data = Image.frombytes("RGB", [w_orig, h_orig], samples)
        aspect = w_orig / h_orig
        w_disp, h_disp = 300, int(300 / aspect)
        ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(w_disp, h_disp))
        self.preview_images.append(ctk_img)
        lbl = ctk.CTkLabel(self.scroll_preview, image=ctk_img, text=label_text, compound="bottom", pady=10)
        lbl.pack(pady=5)

    # --- COMPRESS TAB ---
    def setup_compress_tab(self):
        ctk.CTkLabel(self.tab_compress, text="Compress PDF", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_compress, text="Select PDF", command=self.select_pdf_for_compress).pack(pady=10)
        sf = ctk.CTkFrame(self.tab_compress, fg_color="transparent");
        sf.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(sf, text="Small File", font=("Arial", 10)).grid(row=0, column=0)
        self.slider = ctk.CTkSlider(sf, from_=10, to=90, number_of_steps=8);
        self.slider.set(40);
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)
        sf.grid_columnconfigure(1, weight=1)
        self.comp_btn = ctk.CTkButton(self.tab_compress, text="Fit & Save", command=self.compress_logic,
                                      state="disabled")
        self.comp_btn.pack(pady=20)

    def select_pdf_for_compress(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path: self.selected_pdf_path = path; self.update_pdf_preview(path); self.comp_btn.configure(state="normal")

    def compress_logic(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not out: return
        doc, new = fitz.open(self.selected_pdf_path), fitz.open()
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO();
            img.save(buf, format="JPEG", quality=int(self.slider.get()), optimize=True)
            new_page = new.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=buf.getvalue())
            self.progress_bar.set((i + 1) / len(doc));
            self.update()
        new.save(out, garbage=4, deflate=True);
        new.close();
        doc.close();
        self.progress_bar.set(0)
        messagebox.showinfo("Success", "Compressed!")

    # --- CONVERT TAB ---
    def setup_convert_tab(self):
        ctk.CTkLabel(self.tab_convert, text="Images to A4 PDF", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_convert, text="1. Select Images", command=self.select_images_action).pack(pady=10)
        self.orient_var = ctk.StringVar(value="Portrait")
        ctk.CTkSegmentedButton(self.tab_convert, values=["Portrait", "Landscape"], variable=self.orient_var).pack(
            pady=10)
        self.save_img_btn = ctk.CTkButton(self.tab_convert, text="2. Save PDF", command=self.convert_logic,
                                          state="disabled")
        self.save_img_btn.pack(pady=10)

    def select_images_action(self):
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if paths: self.selected_images = list(paths); self.update_image_preview(
            self.selected_images); self.save_img_btn.configure(state="normal")

    def convert_logic(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            w, h = (210, 297) if self.orient_var.get() == "Portrait" else (297, 210)
            layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(w), img2pdf.mm_to_pt(h)))
            with open(out, "wb") as f: f.write(img2pdf.convert(self.selected_images, layout_fun=layout))
            messagebox.showinfo("Success", "Images converted!")

    # --- MERGE TAB ---
    def setup_merge_tab(self):
        ctk.CTkLabel(self.tab_merge, text="Merge & Reorder", font=("Arial", 20, "bold")).pack(pady=10)
        f = ctk.CTkFrame(self.tab_merge, fg_color="transparent");
        f.pack(pady=5)
        ctk.CTkButton(f, text="Add Files", command=self.add_to_merge, width=100).pack(side="left", padx=5)
        ctk.CTkButton(f, text="Clear", command=self.clear_merge, width=100, fg_color="#c0392b").pack(side="left",
                                                                                                     padx=5)
        self.order_frame = ctk.CTkScrollableFrame(self.tab_merge, height=300);
        self.order_frame.pack(fill="both", expand=True, padx=20, pady=5)
        self.merge_btn = ctk.CTkButton(self.tab_merge, text="Merge PDF", command=self.merge_logic, state="disabled",
                                       fg_color="#27ae60");
        self.merge_btn.pack(pady=15)

    def add_to_merge(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files: self.merge_list.extend(list(files)); self.refresh_merge_ui()

    def clear_merge(self):
        self.merge_list = []; self.refresh_merge_ui(); self.clear_preview()

    def refresh_merge_ui(self):
        for w in self.order_frame.winfo_children(): w.destroy()
        for i, p in enumerate(self.merge_list):
            it = ctk.CTkFrame(self.order_frame);
            it.pack(fill="x", pady=2)
            ctk.CTkButton(it, text=os.path.basename(p), fg_color="transparent", anchor="w",
                          command=lambda x=p: self.update_pdf_preview(x)).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(it, text="▲", width=30, command=lambda x=i: self.move_merge(x, -1)).pack(side="right", padx=2)
            ctk.CTkButton(it, text="▼", width=30, command=lambda x=i: self.move_merge(x, 1)).pack(side="right", padx=2)
        self.merge_btn.configure(state="normal" if len(self.merge_list) > 1 else "disabled")

    def move_merge(self, idx, d):
        ni = idx + d
        if 0 <= ni < len(self.merge_list): self.merge_list[idx], self.merge_list[ni] = self.merge_list[ni], \
                                                                                       self.merge_list[
                                                                                           idx]; self.refresh_merge_ui()

    def merge_logic(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            res = fitz.open()
            for f in self.merge_list:
                with fitz.open(f) as m: res.insert_pdf(m)
            res.save(out);
            res.close();
            messagebox.showinfo("Success", "Merged!")

    # --- SPLIT TAB (NEW FEATURE) ---
    def setup_split_tab(self):
        ctk.CTkLabel(self.tab_split, text="Split PDF Pages", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_split, text="1. Select PDF to Split", command=self.select_pdf_for_split).pack(pady=10)

        self.split_mode = ctk.StringVar(value="range")
        ctk.CTkRadioButton(self.tab_split, text="Extract Specific Range", variable=self.split_mode, value="range").pack(
            pady=5)
        self.range_entry = ctk.CTkEntry(self.tab_split, placeholder_text="e.g. 1-3, 5, 8-10", width=250)
        self.range_entry.pack(pady=5)

        ctk.CTkRadioButton(self.tab_split, text="Split All Pages (Individual Files)", variable=self.split_mode,
                           value="all").pack(pady=10)

        self.split_btn = ctk.CTkButton(self.tab_split, text="2. Split & Save", command=self.split_logic,
                                       state="disabled", fg_color="#e67e22")
        self.split_btn.pack(pady=20)

    def select_pdf_for_split(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.split_pdf_path = path
            self.update_pdf_preview(path)
            self.split_btn.configure(state="normal")

    def split_logic(self):
        if not hasattr(self, 'split_pdf_path'): return

        doc = fitz.open(self.split_pdf_path)
        total_pages = len(doc)

        if self.split_mode.get() == "all":
            folder = filedialog.askdirectory(title="Select Folder to Save Split Pages")
            if not folder: return
            for i in range(total_pages):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                new_doc.save(os.path.join(folder, f"Page_{i + 1}.pdf"))
                new_doc.close()
            messagebox.showinfo("Success", f"Split {total_pages} pages into {folder}")

        else:
            range_text = self.range_entry.get()
            if not range_text:
                messagebox.showerror("Error", "Please enter a range (e.g., 1-5)")
                return

            out = filedialog.asksaveasfilename(defaultextension=".pdf")
            if not out: return

            try:
                pages_to_extract = self.parse_range(range_text, total_pages)
                new_doc = fitz.open()
                for p in pages_to_extract:
                    new_doc.insert_pdf(doc, from_page=p, to_page=p)
                new_doc.save(out)
                new_doc.close()
                messagebox.showinfo("Success", "Selected pages extracted!")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid range: {e}")
        doc.close()

    def parse_range(self, text, max_p):
        pages = []
        for part in text.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start - 1, end))
            else:
                pages.append(int(part) - 1)
        return [p for p in pages if 0 <= p < max_p]


if __name__ == "__main__":
    app = PDFFitApp()
    app.mainloop()