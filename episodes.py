import tkinter as tk
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime
import re
import time
import os
import threading
import subprocess

anime_links_from_file = []

def scrape_single_anime(base_url, total_episodes, start_number, skip_list, all_mode=False):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    service = Service()
    service.creationflags = subprocess.CREATE_NO_WINDOW  # ✅ منع كونسول DevTools
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(base_url)
        time.sleep(2)

        episode_elements = driver.find_elements(By.XPATH, '//*[@id="mCSB_1_container"]/li/a')
        episode_links = [e.get_attribute("href") for e in episode_elements]

        if all_mode:
            selected_links = episode_links
        else:
            selected_links = episode_links[start_number - 1:start_number - 1 + total_episodes]

        all_episodes = []
        anime_title = "?"

        for idx, link in enumerate(selected_links, start=1):
            if idx in skip_list:
                print(f"⏭️ تم تخطي الحلقة رقم {idx}")
                continue

            try:
                driver.get(link)
                wait = WebDriverWait(driver, 10)

                try:
                    episode_title_raw = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/h3"))).text.strip()
                except:
                    print(f"⚠️ الحلقة {idx} غير موجودة أو لم تُحمّل بشكل صحيح")
                    continue

                if anime_title == "?":
                    anime_title = re.sub(r"الحلقة\s+\d+", "", episode_title_raw).strip()

                match = re.search(r"الحلقة\s+\d+", episode_title_raw)
                episode_title = match.group(0) if match else episode_title_raw
                episode_number = int(''.join(filter(str.isdigit, episode_title)))

                server_list = driver.find_elements(By.XPATH, '//*[@id="episode-servers"]/li')
                servers = []

                for li in server_list:
                    try:
                        a_tag = li.find_element(By.TAG_NAME, "a")
                        server_name = a_tag.get_attribute("innerText").strip()
                        href = a_tag.get_attribute("data-ep-url") or a_tag.get_attribute("href")

                        if href:
                            url = href.strip()
                            if url.startswith("//"):
                                url = "https:" + url
                            servers.append({
                                "serverName": server_name,
                                "url": url
                            })
                    except:
                        continue
                clean_title = re.sub(r'[\\/:*?"<>|]', "", anime_title).replace(" ", "-").lower()

                ep_data = {
                    "number": episode_number,
                    "title": episode_title,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "link" : f"https://abdo12249.github.io/1/test1/episodes/المشاهده.html?id={anime_title.replace(':', '').replace(' ', '-').lower()}&episode={episode_number}",
                    "image": f"https://abdo12249.github.io/1/images/{clean_title}.webp",
                    "servers": servers
                }

                all_episodes.append(ep_data)

            except Exception as e:
                print(f"❌ مشكلة في الرابط: {link}\n{e}")
                continue

        result = {
            "animeTitle": anime_title,
            "episodes": all_episodes
        }

        safe_title = re.sub(r'[\\/*:?"<>|]', "", anime_title).replace(" ", "-").lower()
        filename = f"{safe_title}.json"
        os.makedirs("episodes", exist_ok=True)
        full_path = os.path.join("episodes", filename)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✅ تم حفظ الحلقات في: {full_path}")

    finally:
        driver.quit()


def set_buttons_state(state):
    for btn in [btn_extract, btn_extract_all, btn_import_file]:
        btn.config(state=state)

def start_scraping(all_mode=False):
    def run_scraping():
        set_buttons_state("disabled")

        global anime_links_from_file

        skip_input = skip_entry.get().strip()
        skip_list = [int(x.strip()) for x in skip_input.split(",") if x.strip().isdigit()]

        try:
            total_episodes = int(episodes_entry.get())
            start_number = int(start_entry.get())
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة")
            set_buttons_state("normal")
            return

        try:
            if anime_links_from_file:
                for url in anime_links_from_file:
                    print(f"🔄 جاري معالجة: {url}")
                    scrape_single_anime(
                        base_url=url,
                        total_episodes=total_episodes,
                        start_number=start_number,
                        skip_list=skip_list,
                        all_mode=all_mode
                    )
                messagebox.showinfo("تم", "✅ تم استخراج كل الروابط من الملف بنجاح!")
            else:
                base_url = url_entry.get().strip()
                if not base_url:
                    messagebox.showerror("خطأ", "يرجى إدخال رابط أو رفع ملف JSON")
                    set_buttons_state("normal")
                    return

                scrape_single_anime(
                    base_url=base_url,
                    total_episodes=total_episodes,
                    start_number=start_number,
                    skip_list=skip_list,
                    all_mode=all_mode
                )
                messagebox.showinfo("تم", "✅ تم استخراج الحلقات من الرابط!")

        finally:
            set_buttons_state("normal")

    threading.Thread(target=run_scraping).start()


def import_json_file():
    global anime_links_from_file

    file_path = filedialog.askopenfilename(title="اختر ملف JSON", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            anime_links = json.load(f)

        if not isinstance(anime_links, list):
            messagebox.showerror("خطأ", "يجب أن يحتوي الملف على قائمة من الروابط.")
            return

        anime_links_from_file = anime_links
        messagebox.showinfo("تم", "✅ تم تحميل الروابط بنجاح! اضغط الآن على أحد أزرار الاستخراج.")

    except Exception as e:
        messagebox.showerror("خطأ في قراءة الملف", str(e))


# واجهة المستخدم
root = tk.Tk()
root.title("أداة استخراج الحلقات")
root.geometry("400x400")

tk.Label(root, text="رابط صفحة الأنمي:").pack()
url_entry = tk.Entry(root, width=50)
url_entry.pack()

tk.Label(root, text="عدد الحلقات:").pack()
episodes_entry = tk.Entry(root, width=20)
episodes_entry.insert(0, "1")
episodes_entry.pack()

tk.Label(root, text="يبدأ من رقم الحلقة:").pack()
start_entry = tk.Entry(root, width=20)
start_entry.insert(0, "1")
start_entry.pack()

tk.Label(root, text="تخطي حلقات (مثال: 2,5):").pack()
skip_entry = tk.Entry(root, width=30)
skip_entry.insert(0, "")
skip_entry.pack()

btn_extract = tk.Button(root, text="📥 استخراج الحلقات المحددة", command=lambda: start_scraping(all_mode=False), bg="green", fg="white")
btn_extract.pack(pady=5)

btn_extract_all = tk.Button(root, text="📥 جمع كل الحلقات من الصفحة", command=lambda: start_scraping(all_mode=True), bg="blue", fg="white")
btn_extract_all.pack(pady=5)

btn_import_file = tk.Button(root, text="📂 رفع ملف JSON (يُستخدم بعدين)", command=import_json_file, bg="orange", fg="black")
btn_import_file.pack(pady=10)

root.mainloop()
