from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import concurrent.futures
import json
import time

# ===== إعداد المتصفح الأساسي =====
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    # 🚫 منع الصور لتسريع التصفح
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(), options=chrome_options)

# ===== جمع كل روابط الأنميات من الموسم =====
def collect_anime_links(start_url):
    driver = create_driver()
    anime_links = []
    page_number = 1

    driver.get(start_url)
    time.sleep(2)

    while True:
        print(f"📄 جاري استخراج الصفحة رقم {page_number}...")

        divs = driver.find_elements(By.XPATH, '/html/body/div[5]/div//div[contains(@class, "anime-card-container")]')
        for div in divs:
            try:
                link = div.find_element(By.XPATH, './/h3/a').get_attribute("href").strip()
                if link not in anime_links:
                    anime_links.append(link)
            except:
                continue

        try:
            next_button = driver.find_element(By.XPATH, '//ul[@class="pagination"]//a[span[text()="»"]]')
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            page_number += 1
        except:
            print("❌ لا توجد صفحة تالية.")
            break

    driver.quit()
    return anime_links

# ===== استخراج أول حلقة من رابط أنمي واحد =====
def extract_first_episode(anime_url):
    try:
        driver = create_driver()
        driver.get(anime_url)
        time.sleep(1)

        first_ep = driver.find_element(By.XPATH, '//*[@id="DivEpisodesList"]/div/div/div/div/a')
        link = first_ep.get_attribute("href").strip()
        print(f"✅ {link}")
        driver.quit()
        return link

    except Exception as e:
        print(f"⚠️ مشكلة في {anime_url}: {e}")
        return None

# ===== البرنامج الرئيسي =====
if __name__ == "__main__":
    start_url = "https://4t.dvhnar.shop/anime-season/%d8%b5%d9%8a%d9%81-2025/"

    print("🚀 جاري جمع روابط الأنميات...")
    anime_links = collect_anime_links(start_url)
    print(f"✅ تم العثور على {len(anime_links)} أنمي.\n")

    print("🧵 جاري استخراج أول حلقة من كل أنمي باستخدام الـ Threads...")

    first_episode_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(extract_first_episode, anime_links))

    # تصفية النتائج الناجحة فقط
    first_episode_links = [r for r in results if r]

    # حفظ النتائج
    with open("first_episodes_only.json", "w", encoding="utf-8") as f:
        json.dump(first_episode_links, f, ensure_ascii=False, indent=2)

    print(f"\n📁 تم استخراج أول حلقة من {len(first_episode_links)} أنمي وحفظها في first_episodes_only.json")
