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
        self.geometry("1400x900")

        # Variables
        self.selected_pdf_path = None
        self.selected_images = []
        self.merge_list = []
        self.watermark_image_path = None

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.tool_frame = ctk.CTkFrame(self)
        self.tool_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview = ctk.CTkTabview(self.tool_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_compress = self.tabview.add("Compress")
        self.tab_convert = self.tabview.add("Img to PDF")
        self.tab_merge = self.tabview.add("Merge")
        self.tab_split = self.tabview.add("Split")
        self.tab_watermark = self.tabview.add("Watermark")

        # Preview Sidebar
        self.preview_container = ctk.CTkFrame(self, width=420)
        self.preview_container.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.info_panel = ctk.CTkFrame(self.preview_container, height=100, fg_color="#1e1e1e")
        self.info_panel.pack(fill="x", padx=10, pady=10)

        self.stat_label = ctk.CTkLabel(self.info_panel, text="No Selection", font=("Arial", 14, "bold"),
                                       text_color="#3498db")
        self.stat_label.pack(pady=10)

        self.size_label = ctk.CTkLabel(self.info_panel, text="Items: 0", font=("Arial", 12))
        self.size_label.pack(pady=(0, 10))

        self.scroll_preview = ctk.CTkScrollableFrame(self.preview_container, width=380, label_text="Selection Preview")
        self.scroll_preview.pack(expand=True, fill="both", padx=10, pady=(0, 10))

        self.setup_compress_tab()
        self.setup_convert_tab()
        self.setup_merge_tab()
        self.setup_split_tab()
        self.setup_watermark_tab()

    # --- SHARED PREVIEW ENGINE ---
    def clear_preview(self):
        for widget in self.scroll_preview.winfo_children(): widget.destroy()

    def update_pdf_preview(self, pdf_path):
        self.clear_preview()
        try:
            doc = fitz.open(pdf_path)
            self.stat_label.configure(text=f"PDF: {os.path.basename(pdf_path)[:15]}...")
            self.size_label.configure(
                text=f"Pages: {len(doc)} | Size: {os.path.getsize(pdf_path) / (1024 * 1024):.2f} MB")
            for i in range(len(doc)):
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(0.3, 0.3))
                img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data,
                                       size=(320, int(320 * (pix.height / pix.width))))
                ctk.CTkLabel(self.scroll_preview, text=f"Page {i + 1}", font=("Arial", 10, "italic")).pack()
                ctk.CTkLabel(self.scroll_preview, image=ctk_img, text="").pack(pady=10)
                if i % 2 == 0: self.update_idletasks()
            doc.close()
        except:
            pass

    # --- COMPRESS TAB (RESTORED) ---
    def setup_compress_tab(self):
        ctk.CTkLabel(self.tab_compress, text="Compress PDF", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_compress, text="Select PDF", command=self.select_pdf_for_compress).pack(pady=5)
        self.file_info_label = ctk.CTkLabel(self.tab_compress, text="No file selected", font=("Arial", 11, "italic"),
                                            text_color="gray");
        self.file_info_label.pack(pady=5)

        sf = ctk.CTkFrame(self.tab_compress, fg_color="transparent");
        sf.pack(pady=20, fill="x", padx=40)
        ctk.CTkLabel(sf, text="Low Compress\n(High Quality)", font=("Arial", 11)).grid(row=0, column=0, padx=10)
        self.comp_slider = ctk.CTkSlider(sf, from_=10, to=95, command=lambda v: self.int_lbl.configure(
            text=f"Compression Intensity: {int(v)}%"))
        self.comp_slider.set(30);
        self.comp_slider.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(sf, text="High Compress\n(Low Quality)", font=("Arial", 11)).grid(row=0, column=2, padx=10)
        sf.grid_columnconfigure(1, weight=1)

        self.int_lbl = ctk.CTkLabel(self.tab_compress, text="Compression Intensity: 30%", font=("Arial", 12));
        self.int_lbl.pack(pady=5)
        self.prog = ctk.CTkProgressBar(self.tab_compress, width=400);
        self.prog.set(0);
        self.prog.pack(pady=10)
        self.comp_btn = ctk.CTkButton(self.tab_compress, text="Compress & Save", command=self.compress_logic,
                                      state="disabled", height=40);
        self.comp_btn.pack(pady=20)

    def select_pdf_for_compress(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path: self.selected_pdf_path = path; self.file_info_label.configure(
            text=f"Selected: {os.path.basename(path)}", text_color="#3498db"); self.update_pdf_preview(
            path); self.comp_btn.configure(state="normal")

    def compress_logic(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not out: return
        doc, new = fitz.open(self.selected_pdf_path), fitz.open()
        for i, page in enumerate(doc):
            self.prog.set((i + 1) / len(doc));
            self.update_idletasks()
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO();
            img.save(buf, format="JPEG", quality=int(100 - self.comp_slider.get()))
            new_page = new.new_page(width=page.rect.width, height=page.rect.height);
            new_page.insert_image(new_page.rect, stream=buf.getvalue())
        new.save(out);
        new.close();
        doc.close();
        self.prog.set(0);
        messagebox.showinfo("Done", "PDF Compressed!")

    # --- IMG TO PDF TAB (WITH SIZE OPTIONS) ---
    def setup_convert_tab(self):
        ctk.CTkLabel(self.tab_convert, text="Images to PDF", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_convert, text="Select Images", command=self.select_images_action).pack(pady=10)

        # New Layout Option Frame
        self.layout_var = ctk.StringVar(value="Original")
        lay_frame = ctk.CTkFrame(self.tab_convert, fg_color="transparent");
        lay_frame.pack(pady=10)
        ctk.CTkRadioButton(lay_frame, text="Original Size", variable=self.layout_var, value="Original").grid(row=0,
                                                                                                             column=0,
                                                                                                             padx=15)
        ctk.CTkRadioButton(lay_frame, text="A4 Paper Size", variable=self.layout_var, value="A4").grid(row=0, column=1,
                                                                                                       padx=15)

        self.save_img_btn = ctk.CTkButton(self.tab_convert, text="Save PDF", command=self.convert_logic,
                                          state="disabled", height=40);
        self.save_img_btn.pack(pady=10)

    def select_images_action(self):
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if paths:
            self.selected_images = list(paths)
            self.save_img_btn.configure(state="normal")
            self.clear_preview()
            for i, p in enumerate(self.selected_images):
                img = Image.open(p);
                w, h = img.size
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(320, int(320 * (h / w))))
                ctk.CTkLabel(self.scroll_preview, text=f"Img {i + 1}").pack();
                ctk.CTkLabel(self.scroll_preview, image=ctk_img, text="").pack(pady=10)
                self.update_idletasks()

    def convert_logic(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not out: return
        try:
            if self.layout_var.get() == "A4":
                # A4 size in points
                a4_size = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
                layout = img2pdf.get_layout_fun(a4_size)
                with open(out, "wb") as f:
                    f.write(img2pdf.convert(self.selected_images, layout_fun=layout))
            else:
                with open(out, "wb") as f:
                    f.write(img2pdf.convert(self.selected_images))
            messagebox.showinfo("Success", "Images Converted to PDF!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- MERGE TAB (RESTORED) ---
    def setup_merge_tab(self):
        ctk.CTkLabel(self.tab_merge, text="Merge PDFs", font=("Arial", 20, "bold")).pack(pady=10)
        b_frame = ctk.CTkFrame(self.tab_merge, fg_color="transparent");
        b_frame.pack(pady=5)
        ctk.CTkButton(b_frame, text="Add PDF Files", command=self.add_to_merge, width=140).grid(row=0, column=0, padx=5)
        ctk.CTkButton(b_frame, text="Clear All", command=self.clear_merge_list, width=140, fg_color="#c0392b").grid(
            row=0, column=1, padx=5)
        self.order_frame = ctk.CTkScrollableFrame(self.tab_merge, height=400);
        self.order_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.merge_btn = ctk.CTkButton(self.tab_merge, text="Merge PDF", command=self.merge_logic, state="disabled",
                                       height=45);
        self.merge_btn.pack(pady=10)

    def add_to_merge(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files: self.merge_list.extend(list(files)); self.refresh_merge_ui()

    def clear_merge_list(self):
        self.merge_list = [];
        self.refresh_merge_ui();
        self.clear_preview()

    def refresh_merge_ui(self):
        for w in self.order_frame.winfo_children(): w.destroy()
        for i, p in enumerate(self.merge_list):
            it = ctk.CTkFrame(self.order_frame);
            it.pack(fill="x", pady=2)
            lbl = ctk.CTkLabel(it, text=f"{i + 1}. {os.path.basename(p)}", cursor="hand2");
            lbl.pack(side="left", padx=10, fill="x", expand=True)
            lbl.bind("<Button-1>", lambda e, path=p: self.update_pdf_preview(path))
            ctk.CTkButton(it, text="▲", width=30, command=lambda idx=i: self.move_merge_item(idx, -1)).pack(
                side="right", padx=2)
            ctk.CTkButton(it, text="▼", width=30, command=lambda idx=i: self.move_merge_item(idx, 1)).pack(side="right",
                                                                                                           padx=2)
        self.merge_btn.configure(state="normal" if len(self.merge_list) > 1 else "disabled")

    def move_merge_item(self, idx, d):
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

    # --- SPLIT TAB (RESTORED) ---
    def setup_split_tab(self):
        ctk.CTkLabel(self.tab_split, text="Split PDF", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkButton(self.tab_split, text="Select PDF to Split", command=self.select_pdf_for_split).pack(pady=10)
        self.range_entry = ctk.CTkEntry(self.tab_split, width=300, placeholder_text="Range (e.g. 1, 3, 5-10)");
        self.range_entry.pack(pady=5)
        self.split_btn = ctk.CTkButton(self.tab_split, text="Split & Save", command=self.split_logic, state="disabled",
                                       height=45, fg_color="#27ae60");
        self.split_btn.pack(pady=10)

    def select_pdf_for_split(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path: self.selected_pdf_path = path; self.update_pdf_preview(path); self.split_btn.configure(state="normal")

    def split_logic(self):
        doc = fitz.open(self.selected_pdf_path);
        range_str = self.range_entry.get().strip()
        try:
            if range_str:
                pages = []
                for part in range_str.split(','):
                    if '-' in part:
                        s, e = map(int, part.split('-'));
                        pages.extend(range(s - 1, e))
                    else:
                        pages.append(int(part) - 1)
                out = filedialog.asksaveasfilename(defaultextension=".pdf")
                if out:
                    new = fitz.open()
                    for p in pages:
                        if 0 <= p < len(doc): new.insert_pdf(doc, from_page=p, to_page=p)
                    new.save(out);
                    new.close();
                    messagebox.showinfo("Success", "Extracted!")
            else:
                folder = filedialog.askdirectory()
                if folder:
                    for i in range(len(doc)):
                        new = fitz.open();
                        new.insert_pdf(doc, from_page=i, to_page=i);
                        new.save(os.path.join(folder, f"Page_{i + 1}.pdf"));
                        new.close()
                    messagebox.showinfo("Success", "Split All!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        doc.close()

    # --- WATERMARK TAB (RESTORED DROPDOWN ROTATION) ---
    def setup_watermark_tab(self):
        ctk.CTkLabel(self.tab_watermark, text="Add Watermark", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkButton(self.tab_watermark, text="1. Select PDF", command=self.select_pdf_for_wm).pack(pady=5)

        opt = ctk.CTkFrame(self.tab_watermark);
        opt.pack(fill="both", expand=True, padx=20, pady=10)
        self.wm_type = ctk.StringVar(value="text")
        ctk.CTkSegmentedButton(opt, values=["text", "image"], variable=self.wm_type).pack(pady=10)

        self.wm_text_entry = ctk.CTkEntry(opt, placeholder_text="Enter Watermark Text", width=300);
        self.wm_text_entry.pack(pady=5)
        ctk.CTkButton(opt, text="2. Select Watermark Image", command=self.select_wm_image, fg_color="#2c3e50").pack(
            pady=5)

        set_f = ctk.CTkFrame(opt, fg_color="transparent");
        set_f.pack(pady=10)
        pos_frame = ctk.CTkFrame(set_f, fg_color="transparent");
        pos_frame.grid(row=0, column=0, padx=20)
        self.pos_var = ctk.StringVar(value="Center")
        positions = [("Top-Left", 0, 0), ("Top-Center", 0, 1), ("Top-Right", 0, 2),
                     ("Mid-Left", 1, 0), ("Center", 1, 1), ("Mid-Right", 1, 2),
                     ("Bot-Left", 2, 0), ("Bot-Center", 2, 1), ("Bot-Right", 2, 2)]
        for text, r, c in positions:
            ctk.CTkRadioButton(pos_frame, text="", variable=self.pos_var, value=text, width=20).grid(row=r, column=c,
                                                                                                     padx=5, pady=2)

        sl_frame = ctk.CTkFrame(set_f, fg_color="transparent");
        sl_frame.grid(row=0, column=1, padx=20)
        ctk.CTkLabel(sl_frame, text="Opacity").pack()
        self.wm_opacity = ctk.CTkSlider(sl_frame, from_=0.1, to=1.0);
        self.wm_opacity.set(0.4);
        self.wm_opacity.pack()

        ctk.CTkLabel(sl_frame, text="Rotation (Degrees)").pack(pady=(10, 0))
        self.wm_rotate_box = ctk.CTkComboBox(sl_frame, values=["0", "45", "90", "135", "180", "225", "270", "315"])
        self.wm_rotate_box.set("0");
        self.wm_rotate_box.pack()

        self.wm_apply_btn = ctk.CTkButton(self.tab_watermark, text="Apply Watermark", command=self.apply_watermark,
                                          fg_color="#e74c3c", height=45)
        self.wm_apply_btn.pack(pady=20)

    def select_pdf_for_wm(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path: self.selected_pdf_path = path; self.update_pdf_preview(path)

    def select_wm_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path: self.watermark_image_path = path

    def apply_watermark(self):
        if not self.selected_pdf_path: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not out: return
        doc = fitz.open(self.selected_pdf_path)
        op, rot = self.wm_opacity.get(), int(self.wm_rotate_box.get())

        img_bytes = None
        if self.wm_type.get() == "image" and self.watermark_image_path:
            img = Image.open(self.watermark_image_path).convert("RGBA")
            alpha = img.getchannel('A').point(lambda i: i * op);
            img.putalpha(alpha)
            buf = io.BytesIO();
            img.save(buf, format="PNG");
            img_bytes = buf.getvalue()

        for page in doc:
            wm_w, wm_h = (200, 200) if self.wm_type.get() == "image" else (350, 100)
            pw, ph, m = page.rect.width, page.rect.height, 50
            coords = {"Top-Left": (m, m), "Top-Center": ((pw - wm_w) / 2, m), "Top-Right": (pw - wm_w - m, m),
                      "Mid-Left": (m, (ph - wm_h) / 2), "Center": ((pw - wm_w) / 2, (ph - wm_h) / 2),
                      "Mid-Right": (pw - wm_w - m, (ph - wm_h) / 2),
                      "Bot-Left": (m, ph - wm_h - m), "Bot-Center": ((pw - wm_w) / 2, ph - wm_h - m),
                      "Bot-Right": (pw - wm_w - m, ph - wm_h - m)}
            x, y = coords.get(self.pos_var.get(), (m, m));
            rect = fitz.Rect(x, y, x + wm_w, y + wm_h)

            if self.wm_type.get() == "text":
                txt = self.wm_text_entry.get() or "WATERMARK";
                pivot = rect.tl + (rect.br - rect.tl) * 0.5
                page.insert_textbox(rect, txt, fontsize=40, color=(0.7, 0.7, 0.7), align=fitz.TEXT_ALIGN_CENTER,
                                    fill_opacity=op, morph=(pivot, fitz.Matrix(rot)))
            elif img_bytes:
                page.insert_image(rect, stream=img_bytes, rotate=rot)
        doc.save(out);
        doc.close();
        messagebox.showinfo("Success", "Watermark applied!")


if __name__ == "__main__":
    app = PDFFitApp()
    app.mainloop()