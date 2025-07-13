from github import Github
import base64
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import time
from PIL import Image
import io

# بيانات المستخدم
access_token = "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" # استبدل برمز GitHub الخاص بك
repo_name = "abdo12249/1" # استبدل باسم المستودع الخاص بك

g = Github(access_token)
repo = g.get_repo(repo_name)

# الأنماط الموحدة
label_style = {"bg": "#111827", "fg": "#ffffff", "font": ("Arial", 11, "bold")}
btn_style = {"bg": "#ef4444", "fg": "#ffffff", "activebackground": "#1f2937", "activeforeground": "#ffffff", "font": ("Arial", 11, "bold"), "bd": 0, "relief": "flat", "cursor": "hand2", "padx": 10, "pady": 6}
entry_style = {"bg": "#1f2937", "fg": "#ffffff", "insertbackground": "#ffffff", "readonlybackground": "#1f2937", "font": ("Arial", 10)}
listbox_style = {"bg": "#1f2937", "fg": "#9ca3af", "selectbackground": "#ef4444", "selectforeground": "#ffffff", "font": ("Arial", 10), "bd": 0, "highlightthickness": 0, "relief": "flat"}

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("رفع الملفات إلى GitHub")
        self.geometry("650x510")
        self.configure(bg="#111827")
        self.resizable(True, True)

        # أزرار تبديل الصفحات
        top_frame = tk.Frame(self, bg="#111827")
        top_frame.pack(fill="x", pady=10)

        self.btn_edit = tk.Button(top_frame, text="تعديل ملف في GitHub", command=self.show_edit, **btn_style)
        self.btn_edit.pack(side="left", padx=10)
        self.btn_manage = tk.Button(top_frame, text="إدارة مجلد في GitHub", command=self.show_manage, **btn_style)
        self.btn_manage.pack(side="left", padx=10)

        # إطار المحتوى المتغير (صفحتان دائمتان)
        self.content_frame = tk.Frame(self, bg="#111827")
        self.content_frame.pack(fill="both", expand=True)

        self.edit_frame = EditGithubFile(self.content_frame)
        self.manage_frame = ManageGithubFolder(self.content_frame)

        self.edit_frame.frame.pack(fill="both", expand=True)
        self.manage_frame.frame.pack_forget()

        self.show_edit()

    def show_edit(self):
        self.set_active_btn("edit")
        self.manage_frame.frame.pack_forget()
        self.edit_frame.frame.pack(fill="both", expand=True)

    def show_manage(self):
        self.set_active_btn("manage")
        self.edit_frame.frame.pack_forget()
        self.manage_frame.frame.pack(fill="both", expand=True)

    def set_active_btn(self, active):
        active_style = {"bg": "#991b1b", "fg": "#fff"}
        normal_style = {"bg": "#ef4444", "fg": "#fff"}
        if active == "edit":
            self.btn_edit.config(**active_style)
            self.btn_manage.config(**normal_style)
        else:
            self.btn_manage.config(**active_style)
            self.btn_edit.config(**normal_style)

class EditGithubFile:
    def __init__(self, parent):
        self.frame = parent # Use parent frame for scheduling UI updates
        self.main_frame = tk.Frame(parent, bg="#111827") # Create a sub-frame for content
        self.main_frame.pack(fill="both", expand=True)

        tk.Label(self.main_frame, text="اختر ملف JSON من مجلد test1/episodes أو animes.json:", **label_style).pack(pady=7)

        self.episode_files = []
        self.episode_files_display = []
        try:
            contents = repo.get_contents("test1/episodes", ref="main")
            for content in contents:
                if content.type == "file" and content.name.lower().endswith(".json"):
                    self.episode_files.append(f"test1/episodes/{content.name}")
                    self.episode_files_display.append(content.name)
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر جلب الملفات: {e}")

        self.anime_file = "test1/animes.json"
        self.anime_file_display = "animes.json"
        
        self.selected_remote_var = tk.StringVar(value=self.episode_files[0] if self.episode_files else self.anime_file)

        # شريط البحث
        tk.Label(self.main_frame, text="ابحث عن ملف:", **label_style).pack(pady=2) # إضافة تسمية لشريط البحث
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.main_frame, textvariable=self.search_var, width=50, **entry_style)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_files) # ربط حدث الكتابة

        btn_frame = tk.Frame(self.main_frame, bg="#111827")
        btn_frame.pack(pady=3)
        self.files_listbox = tk.Listbox(self.main_frame, height=10, width=55, **listbox_style)
        self.files_listbox.pack(pady=5)

        def show_episodes_internal():
            self.current_files_data = {"type": "episodes", "files": self.episode_files, "display": self.episode_files_display}
            self.filter_files()
            self.btn_episodes.config(bg="#991b1b", fg="#fff")
            self.btn_anime.config(bg="#ef4444", fg="#fff")

        def show_anime_internal():
            self.current_files_data = {"type": "anime", "files": [self.anime_file], "display": [self.anime_file_display]}
            self.filter_files()
            self.btn_anime.config(bg="#991b1b", fg="#fff")
            self.btn_episodes.config(bg="#ef4444", fg="#fff")

        self.btn_episodes = tk.Button(btn_frame, text="عرض ملفات الحلقات", command=show_episodes_internal, **btn_style)
        self.btn_episodes.pack(side="left", padx=5)
        self.btn_anime = tk.Button(btn_frame, text="عرض ملف تعريف الأنمي", command=show_anime_internal, **btn_style)
        self.btn_anime.pack(side="left", padx=5)

        # تهيئة القائمة الأولية
        self.current_files_data = {"type": "episodes", "files": self.episode_files, "display": self.episode_files_display}
        self.filter_files() # استدعاء filter_files لملء القائمة عند البدء
        if self.episode_files:
            self.files_listbox.selection_set(0)
        self.btn_episodes.config(bg="#991b1b", fg="#fff") # جعل زر الحلقات نشطًا عند البدء

        def on_select(evt):
            sel = self.files_listbox.curselection()
            if sel:
                idx = sel[0]
                # التأكد من أن الفهرس ضمن النطاق
                if idx < len(self.current_files_data["files"]):
                    self.selected_remote_var.set(self.current_files_data["files"][idx])
                else:
                    self.files_listbox.selection_clear(idx) # مسح التحديد إذا كان الفهرس خارج النطاق
        self.files_listbox.bind('<<ListboxSelect>>', on_select)

        tk.Label(self.main_frame, text="اختر ملف JSON من جهازك لدمجه مع الملف المختار:", **label_style).pack(pady=7)
        selected_file_var = tk.StringVar()
        entry = tk.Entry(self.main_frame, textvariable=selected_file_var, width=50, state='readonly', **entry_style)
        entry.pack(pady=3)

        def choose_file():
            # السماح باختيار ملفات متعددة
            file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
            if file_paths:
                selected_file_var.set(";".join(file_paths))

        def merge_and_upload():
            local_paths = selected_file_var.get().split(";")
            remote_path = self.selected_remote_var.get()
            if not remote_path:
                messagebox.showerror("خطأ", "يرجى اختيار ملف من GitHub أولاً!")
                return
            if not local_paths or not local_paths[0]:
                messagebox.showerror("خطأ", "يرجى اختيار ملف/ملفات JSON من جهازك أولاً!")
                return
            
            # تحميل محتوى الملف البعيد
            try:
                file_content = repo.get_contents(remote_path, ref="main")
                remote_json = json.loads(base64.b64decode(file_content.content).decode(errors="replace"))
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر تحميل الملف من GitHub: {e}")
                return

            merged_data = None

            # معالجة ملفات JSON المحلية
            for local_path in local_paths:
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        local_json = json.load(f)
                except Exception as e:
                    messagebox.showerror("خطأ", f"تعذر قراءة الملف المحلي: {local_path}\n{e}")
                    return

                # التحقق الجديد: منع دمج ملف حلقة مع ملف تعريف الأنمي
                if remote_path.endswith("animes.json") and "episodes" in local_json and isinstance(local_json["episodes"], list):
                    messagebox.showerror("خطأ", "لا يمكن دمج ملف حلقة أنمي مع ملف تعريف الأنمي (animes.json). يرجى اختيار ملف حلقة أنمي من GitHub لدمج الحلقات.")
                    return

                if remote_path.endswith("animes.json"):
                    if not isinstance(remote_json, dict):
                        messagebox.showerror("خطأ", "الملف البعيد animes.json ليس قاموسًا صالحًا.")
                        return
                    if not isinstance(local_json, dict):
                        messagebox.showerror("خطأ", "الملف المحلي لـ animes.json يجب أن يكون قاموسًا.")
                        return
                    
                    merged_data = remote_json.copy() if merged_data is None else merged_data
                    for anime_key, anime_data in local_json.items():
                        if anime_key in merged_data:
                            messagebox.showerror("خطأ", f"مفتاح الأنمي '{anime_key}' مكرر بالفعل في animes.json. يرجى إزالة المفتاح المكرر من ملفك المحلي أو تعديل المفتاح.")
                            return
                        
                        # تعيين مسار الصورة تلقائيًا بناءً على anime_key
                        image_url = f"images/{anime_key}.webp" # المسار الصحيح لـ GitHub
                        
                        # تعيين حقل 'image' الفردي
                        anime_data["image"] = image_url
                        
                        # التأكد من إزالة حقل 'images' إذا كان موجودًا (من المنطق السابق)
                        if "images" in anime_data:
                            del anime_data["images"]

                        merged_data[anime_key] = anime_data

                elif remote_path.startswith("test1/episodes/") and remote_path.endswith(".json"):
                    # بالنسبة لملفات الحلقات، من المتوقع أن تكون ملفات JSON البعيدة والمحلية عبارة عن قواميس
                    # تحتوي على مفتاح 'episodes' الذي يحتوي على قائمة.
                    if not isinstance(remote_json, dict) or "episodes" not in remote_json or not isinstance(remote_json["episodes"], list):
                        messagebox.showerror("خطأ", "الملف البعيد للحلقات ليس قاموسًا صالحًا يحتوي على قائمة 'episodes'.")
                        return
                    if not isinstance(local_json, dict) or "episodes" not in local_json or not isinstance(local_json["episodes"], list):
                        messagebox.showerror("خطأ", "الملف المحلي للحلقات ليس قاموسًا صالحًا يحتوي على قائمة 'episodes'.")
                        return
                    
                    # تهيئة merged_data إذا كان هذا هو الملف المحلي الأول، وإلا استخدم merged_data الموجود
                    merged_data = remote_json.copy() if merged_data is None else merged_data
                    
                    # الحصول على عنوان الأنمي من الملف البعيد للتحقق
                    remote_anime_title = remote_json.get("animeTitle")
                    if not remote_anime_title:
                        messagebox.showerror("خطأ", "الملف البعيد للحلقات لا يحتوي على 'animeTitle'.")
                        return

                    # الحصول على عنوان الأنمي من الملف المحلي للتحقق
                    local_anime_title = local_json.get("animeTitle")
                    if not local_anime_title:
                        messagebox.showerror("خطأ", "ملف الحلقة المحلي لا يحتوي على مفتاح 'animeTitle'. يرجى التأكد من وجوده.")
                        return
                        
                    # التحقق من تطابق animeTitle
                    if local_anime_title != remote_anime_title:
                        messagebox.showerror("خطأ", f"عنوان الأنمي للحلقة الجديدة '{local_anime_title}' لا يتطابق مع عنوان الأنمي في الملف البعيد '{remote_anime_title}'.")
                        return

                    # إنشاء مجموعة من روابط الحلقات وأرقامها الموجودة للتحقق الفعال من التكرارات
                    existing_episode_links = {ep.get("link") for ep in merged_data["episodes"] if "link" in ep}
                    existing_episode_numbers = {ep.get("number") for ep in merged_data["episodes"] if "number" in ep}


                    for new_episode in local_json["episodes"]:
                        # التحقق من تكرار رقم الحلقة
                        if "number" in new_episode and new_episode["number"] in existing_episode_numbers:
                            messagebox.showerror("خطأ", f"رقم الحلقة '{new_episode['number']}' مكرر بالفعل في الملف البعيد. يرجى إزالة الحلقة المكررة من ملفك المحلي أو تعديل رقمها.")
                            return
                        
                        if "link" in new_episode and new_episode["link"] not in existing_episode_links:
                            merged_data["episodes"].append(new_episode)
                            existing_episode_links.add(new_episode["link"]) # إضافة إلى المجموعة لمنع التكرارات المستقبلية
                            if "number" in new_episode:
                                existing_episode_numbers.add(new_episode["number"]) # إضافة رقم الحلقة إلى المجموعة
                        elif "link" not in new_episode:
                            # إذا لم يكن هناك رابط، فقط قم بالإلحاق (أو أضف فحصًا أكثر قوة للتكرارات إذا لزم الأمر)
                            merged_data["episodes"].append(new_episode)
                            if "number" in new_episode:
                                existing_episode_numbers.add(new_episode["number"]) # إضافة رقم الحلقة إلى المجموعة

                else:
                    messagebox.showerror("خطأ", "صيغة الملف غير مدعومة في هذا الوضع! يجب أن يكون ملف animes.json أو ملف حلقة JSON.")
                    return

            if merged_data is None:
                messagebox.showerror("خطأ", "لم يتم دمج أي بيانات. تحقق من تنسيق الملفات.")
                return

            try:
                new_content = json.dumps(merged_data, ensure_ascii=False, indent=2)
                repo.update_file(remote_path, "دمج تلقائي من عدة ملفات محلية عبر البرنامج", new_content, file_content.sha, branch="main")
                messagebox.showinfo("تم", "تم دمج ورفع البيانات بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر رفع التعديلات: {e}")

        # دالة لرفع صور متعددة
        def upload_multiple_images():
            image_paths = filedialog.askopenfilenames(
                title="اختر صورًا لرفعها",
                filetypes=[
                    ("جميع الصور", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg;*.jpeg"),
                    ("BMP", "*.bmp"),
                    ("GIF", "*.gif"),
                    ("WebP", "*.webp"),
                    ("كل الملفات", "*.*")
                ]
            )
            
            if not image_paths:
                messagebox.showwarning("تحذير", "لم يتم اختيار أي صور.")
                return

            uploaded_count = 0
            failed_uploads = []

            for image_path in image_paths:
                original_filename = os.path.basename(image_path)
                image_filename_webp = os.path.splitext(original_filename)[0] + ".webp"
                github_path = f"images/{image_filename_webp}"

                try:
                    with Image.open(image_path) as img:
                        img_io = io.BytesIO()
                        img.save(img_io, format="WEBP")
                        img_content = img_io.getvalue()
                    
                    try:
                        existing_file = repo.get_contents(github_path, ref="main")
                        repo.update_file(github_path, f"تحديث الصورة {image_filename_webp}", img_content, existing_file.sha, branch="main")
                        uploaded_count += 1
                    except Exception as e:
                        repo.create_file(github_path, f"إضافة الصورة {image_filename_webp}", img_content, branch="main")
                        uploaded_count += 1
                except Exception as e:
                    failed_uploads.append(f"{original_filename}: {e}")
            
            summary_message = f"تم رفع/تحديث {uploaded_count} صورة بنجاح."
            if failed_uploads:
                summary_message += "\nفشل رفع الصور التالية:\n" + "\n".join(failed_uploads)
            
            messagebox.showinfo("تقرير رفع الصور", summary_message)

        # دالة جديدة لرفع ملفات حلقات أنمي متعددة (تنفذ في مسار منفصل)
        def _upload_multiple_episode_files_threaded(file_paths):
            uploaded_files_summary = []
            skipped_files_summary = []
            failed_files_summary = []

            remote_episode_files_data = {}
            try:
                contents = repo.get_contents("test1/episodes", ref="main")
                for content in contents:
                    if content.type == "file" and content.name.lower().endswith(".json"):
                        try:
                            file_content = repo.get_contents(content.path, ref="main")
                            remote_json = json.loads(base64.b64decode(file_content.content).decode(errors="replace"))
                            if "animeTitle" in remote_json:
                                remote_episode_files_data[remote_json["animeTitle"]] = {
                                    "path": content.path,
                                    "sha": file_content.sha,
                                    "data": remote_json
                                }
                            else:
                                skipped_files_summary.append(f"الملف البعيد '{content.name}': لا يحتوي على 'animeTitle'. تم تخطيه.")
                        except Exception as e:
                            failed_files_summary.append(f"تعذر تحميل أو تحليل الملف البعيد '{content.name}': {e}")
            except Exception as e:
                failed_files_summary.append(f"تعذر جلب قائمة ملفات الحلقات من GitHub: {e}")

            for local_path in file_paths:
                filename = os.path.basename(local_path)
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        local_json = json.load(f)

                    if "animeTitle" not in local_json:
                        failed_files_summary.append(f"الملف {filename}: لا يحتوي على مفتاح 'animeTitle'.")
                        continue
                    
                    if "episodes" not in local_json or not isinstance(local_json["episodes"], list):
                        failed_files_summary.append(f"الملف {filename}: ليس ملف حلقة أنمي صالح (لا يحتوي على قائمة 'episodes').")
                        continue

                    local_anime_title = local_json["animeTitle"]
                    
                    if local_anime_title in remote_episode_files_data:
                        remote_file_info = remote_episode_files_data[local_anime_title]
                        remote_path_for_update = remote_file_info["path"]
                        remote_sha_for_update = remote_file_info["sha"]
                        remote_json_for_update = remote_file_info["data"].copy()

                        existing_episode_links = {ep.get("link") for ep in remote_json_for_update.get("episodes", []) if "link" in ep}
                        existing_episode_numbers = {ep.get("number") for ep in remote_json_for_update.get("episodes", []) if "number" in ep}
                        
                        episodes_added_count = 0
                        for new_episode in local_json["episodes"]:
                            if "number" not in new_episode:
                                skipped_files_summary.append(f"الملف {filename}: حلقة بدون رقم. تم تخطيها.")
                                continue
                            if "link" not in new_episode:
                                skipped_files_summary.append(f"الملف {filename}: حلقة بدون رابط. تم تخطيها.")
                                continue

                            if new_episode["number"] in existing_episode_numbers:
                                skipped_files_summary.append(f"الملف {filename}: رقم الحلقة '{new_episode['number']}' مكرر. تم تخطيها.")
                                continue
                            
                            if new_episode["link"] in existing_episode_links:
                                skipped_files_summary.append(f"الملف {filename}: رابط الحلقة '{new_episode['link']}' مكرر. تم تخطيها.")
                                continue
                            
                            remote_json_for_update["episodes"].append(new_episode)
                            existing_episode_numbers.add(new_episode["number"])
                            existing_episode_links.add(new_episode["link"])
                            episodes_added_count += 1
                        
                        if episodes_added_count > 0:
                            try:
                                new_content = json.dumps(remote_json_for_update, ensure_ascii=False, indent=2)
                                repo.update_file(remote_path_for_update, f"دمج حلقات من {filename} عبر البرنامج", new_content, remote_sha_for_update, branch="main")
                                uploaded_files_summary.append(f"تم تحديث ملف '{remote_path_for_update}' بنجاح بإضافة {episodes_added_count} حلقة من '{filename}'.")
                            except Exception as e:
                                failed_files_summary.append(f"تعذر رفع التعديلات للملف '{remote_path_for_update}' من '{filename}': {e}")
                        else:
                            skipped_files_summary.append(f"الملف {filename}: لم يتم العثور على حلقات جديدة لدمجها أو جميعها مكررة.")

                    else:
                        failed_files_summary.append(f"الملف {filename}: لم يتم العثور على ملف أنمي مطابق في GitHub لـ '{local_anime_title}'.")

                except Exception as e:
                    failed_files_summary.append(f"تعذر معالجة الملف {filename}: {e}")
            
            # عرض ملخص العملية في المسار الرئيسي لـ Tkinter
            final_summary_message = []
            if uploaded_files_summary:
                final_summary_message.append("الملفات التي تم تحديثها بنجاح:\n" + "\n".join(uploaded_files_summary))
            if skipped_files_summary:
                final_summary_message.append("الملفات/الحلقات التي تم تخطيها:\n" + "\n".join(skipped_files_summary))
            if failed_files_summary:
                final_summary_message.append("الملفات التي فشلت المعالجة:\n" + "\n".join(failed_files_summary))

            if final_summary_message:
                self.frame.after(0, lambda: messagebox.showinfo("تقرير رفع الحلقات المتعددة", "\n\n".join(final_summary_message)))
            else:
                self.frame.after(0, lambda: messagebox.showinfo("تقرير رفع الحلقات المتعددة", "لم يتم معالجة أي ملفات حلقات."))

        # دالة لبدء عملية الرفع في مسار منفصل
        def start_upload_multiple_episode_files():
            file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
            if not file_paths:
                messagebox.showwarning("تحذير", "لم يتم اختيار أي ملفات حلقات.")
                return
            
            # بدء المسار المنفصل
            threading.Thread(target=_upload_multiple_episode_files_threaded, args=(file_paths,)).start()


        btn_frame2 = tk.Frame(self.main_frame, bg="#111827")
        btn_frame2.pack(pady=15)
        tk.Button(btn_frame2, text="اختر ملف JSON", command=choose_file, **btn_style).pack(side="left", padx=5)
        tk.Button(btn_frame2, text="دمج ورفع", command=merge_and_upload, **btn_style).pack(side="left", padx=5)
        # تم التعديل: زر لرفع صور متعددة
        tk.Button(btn_frame2, text="رفع صور متعددة", command=upload_multiple_images, **btn_style).pack(side="left", padx=5)
        # زر جديد لرفع ملفات حلقات أنمي متعددة
        tk.Button(btn_frame2, text="رفع ملفات حلقات متعددة", command=start_upload_multiple_episode_files, **btn_style).pack(side="left", padx=5)


    def filter_files(self, event=None):
        """
        تقوم بتصفية قائمة الملفات المعروضة بناءً على نص البحث.
        """
        search_term = self.search_var.get().lower()
        self.files_listbox.delete(0, tk.END)
        
        filtered_display_files = []
        filtered_actual_files = []

        if self.current_files_data["type"] == "episodes":
            for i, filename in enumerate(self.episode_files_display):
                if search_term in filename.lower():
                    filtered_display_files.append(filename)
                    filtered_actual_files.append(self.episode_files[i])
        elif self.current_files_data["type"] == "anime":
            if search_term in self.anime_file_display.lower():
                filtered_display_files.append(self.anime_file_display)
                filtered_actual_files.append(self.anime_file)

        for name in filtered_display_files:
            self.files_listbox.insert(tk.END, name)
        
        # تحديث قائمة الملفات الفعلية المعروضة
        self.current_files_data["files"] = filtered_actual_files
        self.current_files_data["display"] = filtered_display_files

        if filtered_actual_files:
            self.files_listbox.selection_set(0)
            self.selected_remote_var.set(filtered_actual_files[0])
        else:
            self.selected_remote_var.set("") # مسح المتغير إذا لم يكن هناك ملفات مطابقة


class ManageGithubFolder:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#111827")
        self.frame.pack(fill="both", expand=True)

        tk.Label(self.frame, text="مجلد GitHub: test1/episodes", **label_style).pack(pady=5)
        self.files_listbox = tk.Listbox(self.frame, width=60, height=12, **listbox_style)
        self.files_listbox.pack(pady=10)

        def load_files():
            self.files_listbox.delete(0, tk.END)
            try:
                contents = repo.get_contents("test1/episodes", ref="main")
                for content in contents:
                    if content.type == "file":
                        self.files_listbox.insert(tk.END, content.name)
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر جلب الملفات: {e}")

        def add_json_file():
            # السماح باختيار ملفات متعددة
            file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
            if not file_paths:
                return

            uploaded_files = []
            skipped_files = []
            failed_files = []
            
            for file_path in file_paths: # التكرار على كل ملف محدد
                filename = os.path.basename(file_path)
                remote_episode_path = f"test1/episodes/{filename}".replace("\\", "/")
                remote_json_path = "الجديد.json"
                full_url = f"https://abdo12249.github.io/1/test1/episodes/{filename}"

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # رفع ملف الحلقة
                    try:
                        repo.get_contents(remote_episode_path, ref="main")
                        skipped_files.append(f"الملف {filename} موجود بالفعل.")
                        continue # تخطي هذا الملف والانتقال إلى التالي
                    except:
                        repo.create_file(remote_episode_path, f"إضافة ملف {filename} عبر البرنامج", content, branch="main")
                        uploaded_files.append(f"تم رفع الملف {filename} بنجاح.")

                    # تعديل ملف 1/الجديد.json
                    try:
                        file = repo.get_contents(remote_json_path, ref="main")
                        json_data = json.loads(base64.b64decode(file.content).decode("utf-8"))

                        if "animes" not in json_data or not isinstance(json_data["animes"], list):
                            json_data["animes"] = []

                        if full_url not in json_data["animes"]:
                            json_data["animes"].append(full_url)

                            new_json = json.dumps(json_data, ensure_ascii=False, indent=2)
                            repo.update_file(
                                remote_json_path,
                                f"تحديث الجديد.json بعد إضافة {filename}",
                                new_json,
                                file.sha,
                                branch="main"
                            )
                            uploaded_files.append(f"تم تحديث ملف الجديد.json بنجاح بعد إضافة {filename}.")
                        else:
                            skipped_files.append(f"الرابط لـ {filename} موجود مسبقًا في الجديد.json.")

                    except Exception as e:
                        failed_files.append(f"تعذر تعديل الجديد.json للملف {filename}: {e}")

                except Exception as e:
                    failed_files.append(f"تعذر معالجة الملف {filename}: {e}")

            # عرض رسالة ملخص بعد معالجة جميع الملفات
            summary_message = []
            if uploaded_files:
                summary_message.append("الملفات التي تم رفعها وتحديثها بنجاح:\n" + "\n".join(uploaded_files))
            if skipped_files:
                summary_message.append("الملفات التي تم تخطيها (موجودة بالفعل أو روابط مكررة):\n" + "\n".join(skipped_files))
            if failed_files:
                summary_message.append("الملفات التي فشلت المعالجة:\n" + "\n".join(failed_files))

            if summary_message:
                messagebox.showinfo("تقرير الرفع", "\n\n".join(summary_message))
            else:
                messagebox.showinfo("تقرير الرفع", "لم يتم معالجة أي ملفات.")

            load_files() # إعادة تحميل قائمة الملفات بعد معالجة جميع الملفات المحددة

        btn_frame = tk.Frame(self.frame, bg="#111827")
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="عرض الملفات", command=load_files, **btn_style).pack(side="left", padx=5)
        tk.Button(btn_frame, text="إضافة ملف JSON", command=add_json_file, **btn_style).pack(side="left", padx=5)

        load_files()

if __name__ == "__main__":
    MainApp().mainloop()
