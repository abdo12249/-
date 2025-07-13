import tkinter as tk
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import time
import requests
import os
import re

def extract_anime_from_url(url, driver):
    def get_text(xpath):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except:
            return ""

    def get_attr(xpath, attr):
        try:
            return driver.find_element(By.XPATH, xpath).get_attribute(attr).strip()
        except:
            return ""

    def clean_label(text, prefix):
        return text.replace(prefix, "").strip()

    driver.get(url)
    time.sleep(2)

    title = get_text("/html/body/div[2]/div/div/div[2]/div/h1")
    description = get_text("/html/body/div[2]/div/div/div[2]/div/p")
    image_url = get_attr("/html/body/div[2]/div/div/div[1]/div/img", "src")
    tags_elements = driver.find_elements(By.XPATH, "/html/body/div[2]/div/div/div[2]/div/ul/li")
    tags = [tag.text.strip() for tag in tags_elements]

    type_ = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[1]/div/a")
    status = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[3]/div/a")
    episode_count_raw = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[4]/div")
    duration_raw = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[5]/div")
    season = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[6]/div/a")
    source_raw = get_text("/html/body/div[2]/div/div/div[2]/div/div[1]/div[7]/div")

    episode_count = clean_label(episode_count_raw, "عدد الحلقات:")
    if episode_count == "غير معروف":
        episode_count = "غير متوفر"

    duration = clean_label(duration_raw, "مدة الحلقة:")
    source = clean_label(source_raw, "المصدر:")

    os.makedirs("images", exist_ok=True)
    os.makedirs("anime_data", exist_ok=True)

    anime_id = re.sub(r'[^a-zA-Z0-9\-]', '', title.lower().replace(" ", "-"))
    image_name = f"{anime_id}.webp"
    image_save_path = f"images/{image_name}"
    image_json_path = f"../images/{image_name}"

    try:
        img_data = requests.get(image_url).content
        with open(image_save_path, 'wb') as handler:
            handler.write(img_data)
    except:
        image_json_path = image_url

    anime_data = {
        "title": title,
        "description": description,
        "image": image_json_path,
        "tags": tags,
        "type": type_,
        "status": status,
        "episodeCount": episode_count,
        "duration": duration,
        "season": season,
        "source": source
    }

    with open(f"anime_data/{anime_id}.json", "w", encoding="utf-8") as f:
        json.dump({anime_id: anime_data}, f, ensure_ascii=False, indent=2)

    return anime_id

def load_json_file():
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not filepath:
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                urls = "\n".join(data)
                text_input.delete("1.0", tk.END)
                text_input.insert(tk.END, urls)
                messagebox.showinfo("تم", f"✅ تم تحميل {len(data)} رابط من الملف.")
            else:
                messagebox.showerror("خطأ", "يجب أن يكون الملف بصيغة قائمة [\"url1\", \"url2\", ...]")
    except Exception as e:
        messagebox.showerror("خطأ في قراءة الملف", str(e))

def start_extraction():
    urls = text_input.get("1.0", tk.END).strip().splitlines()
    if not urls:
        messagebox.showerror("خطأ", "يرجى تحميل أو إدخال رابط واحد على الأقل.")
        return

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    service = Service(r"D:\script\chrom\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    processed = []

    try:
        for url in urls:
            url = url.strip()
            if url:
                try:
                    anime_id = extract_anime_from_url(url, driver)
                    processed.append(anime_id)
                    print(f"✅ تم استخراج: {anime_id}")
                except Exception as e:
                    print(f"❌ خطأ في {url}: {e}")
        messagebox.showinfo("تم", f"✅ تم استخراج {len(processed)} أنمي وحفظهم في anime_data/")
    finally:
        driver.quit()

# واجهة GUI
root = tk.Tk()
root.title("استخراج بيانات عدة أنميات")
root.geometry("600x460")
root.resizable(False, False)

tk.Label(root, text="روابط صفحات الأنمي (رابط في كل سطر):", font=("Arial", 12)).pack(pady=10)
text_input = tk.Text(root, width=70, height=15, font=("Arial", 11))
text_input.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="📂 تحميل ملف JSON", font=("Arial", 11), command=load_json_file).pack(side="left", padx=10)
tk.Button(btn_frame, text="✅ ابدأ الاستخراج", font=("Arial", 11), bg="green", fg="white", command=start_extraction).pack(side="left", padx=10)

root.mainloop()
