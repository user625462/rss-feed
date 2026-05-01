import os
import requests
from datetime import datetime
import pytz
from feedgen.feed import FeedGenerator

# Tüm API linklerimiz ve ayarları
FEEDS = {
    "mku_genel_duyurular": {
        "title": "MKÜ Genel Duyurular",
        "url": "https://gateway-api.mku.edu.tr/website/api/Duyuru/GetPagedList?start=0&length=15&duyuruDilId=1&orderByName[propertyName]=duyuruTarih&orderByName[isAscending]=false&duyuruAktif=true&anasayfadaGoster=true",
        "type": "duyuru"
    },
    "mku_genel_haberler": {
        "title": "MKÜ Genel Haberler",
        "url": "https://gateway-api.mku.edu.tr/website/api/Haber/GetPagedList?icerikLength=20&start=0&length=15&haberDilId=1&orderByName[propertyName]=haberTarih&orderByName[isAscending]=false&haberAktif=true&birimId=4&anasayfadaGoster=true",
        "type": "haber"
    },
    "egitim_fakultesi_haberler": {
        "title": "Eğitim Fakültesi Haberler",
        "url": "https://gateway-api.mku.edu.tr/website/api/Haber/GetPagedList?start=0&length=15&haberDilId=1&orderByName[propertyName]=haberTarih&orderByName[isAscending]=false&filtre=&haberAktif=true&birimId=8",
        "type": "haber"
    },
    "egitim_fakultesi_duyurular": {
        "title": "Eğitim Fakültesi Duyurular",
        "url": "https://gateway-api.mku.edu.tr/website/api/Duyuru/GetPagedList?start=0&length=15&duyuruAktif=true&duyuruDilId=1&orderByName[propertyName]=duyuruTarih&orderByName[isAscending]=false&birimId=8",
        "type": "duyuru"
    },
    "turkce_sosyal_egitimi_haberler": {
        "title": "Türkçe ve Sosyal Bilimler Eğitimi Haberler",
        "url": "https://gateway-api.mku.edu.tr/website/api/Haber/GetPagedList?start=0&length=15&haberDilId=1&orderByName[propertyName]=haberTarih&orderByName[isAscending]=false&filtre=&haberAktif=true&birimId=121",
        "type": "haber"
    },
    "turkce_sosyal_egitimi_duyurular": {
        "title": "Türkçe ve Sosyal Bilimler Eğitimi Duyurular",
        "url": "https://gateway-api.mku.edu.tr/website/api/Duyuru/GetPagedList?start=0&length=15&duyuruAktif=true&duyuruDilId=1&orderByName[propertyName]=duyuruTarih&orderByName[isAscending]=false&birimId=121",
        "type": "duyuru"
    },
    "turkce_ogretmenligi_haberler": {
        "title": "Türkçe Öğretmenliği Haberler",
        "url": "https://gateway-api.mku.edu.tr/website/api/Haber/GetPagedList?start=0&length=15&haberDilId=1&orderByName[propertyName]=haberTarih&orderByName[isAscending]=false&filtre=&haberAktif=true&birimId=1488",
        "type": "haber"
    },
    "turkce_ogretmenligi_duyurular": {
        "title": "Türkçe Öğretmenliği Duyurular",
        "url": "https://gateway-api.mku.edu.tr/website/api/Duyuru/GetPagedList?start=0&length=15&duyuruAktif=true&duyuruDilId=1&orderByName[propertyName]=duyuruTarih&orderByName[isAscending]=false&birimId=1488",
        "type": "duyuru"
    }
}

TIMEZONE = pytz.timezone('Europe/Istanbul')

def generate_rss():
    # Klasör yoksa oluştur
    if not os.path.exists('feeds'):
        os.makedirs('feeds')

    for feed_id, info in FEEDS.items():
        print(f"İşleniyor: {info['title']}...")
        
        fg = FeedGenerator()
        fg.title(info['title'])
        fg.link(href='https://mku.edu.tr', rel='alternate')
        fg.description(info['title'] + ' Otomatik RSS Akışı')
        fg.language('tr')

        try:
            # API'den veriyi çek
            response = requests.get(info['url'], timeout=10)
            response.raise_for_status()
            data = response.json().get('data', [])

            for item in data:
                fe = fg.add_entry()
                
                if info['type'] == 'haber':
                    item_id = item.get('haberId', '')
                    title = item.get('haberBaslik', 'Başlıksız Haber')
                    desc = item.get('haberOzet') or item.get('haberIcerik', '')
                    date_str = item.get('haberTarih')
                    image_url = item.get('haberDosyaUrl') or item.get('kucukResim')
                    link = f"https://mku.edu.tr/news/{item_id}"
                else: # duyuru
                    item_id = item.get('duyuruId', '')
                    title = item.get('duyuruBaslik', 'Başlıksız Duyuru')
                    desc = item.get('duyuruOzet') or item.get('duyuruIcerik', '')
                    date_str = item.get('duyuruTarih')
                    image_url = item.get('duyuruDosyaUrl') or item.get('kucukResim')
                    link = f"https://mku.edu.tr/announcements/{item_id}"

                fe.id(str(item_id))
                fe.title(title)
                fe.link(href=link)

                # Resim varsa açıklamaya (HTML olarak) ekle
                html_desc = desc
                if image_url:
                    # Gelen URL eksikse site kök dizinini ekle
                    if not str(image_url).startswith('http'):
                        image_url = 'https://mku.edu.tr' + str(image_url) if str(image_url).startswith('/') else 'https://mku.edu.tr/' + str(image_url)
                    html_desc = f'<img src="{image_url}" alt="{title}" style="max-width:100%;"/><br><br>{desc}'
                    # İsteğe bağlı olarak enclosure (RSS standart resim etiketi) ekleyebiliriz
                    fe.enclosure(image_url, 0, 'image/jpeg')

                fe.description(html_desc)

                # Tarih Formatlama
                if date_str:
                    try:
                        # 2026-04-28T13:49:38.933 gibi bir formatı parse et
                        dt = datetime.strptime(date_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        dt = TIMEZONE.localize(dt)
                        fe.pubDate(dt)
                    except Exception as e:
                        print(f"Tarih hatası ({date_str}): {e}")

            # Dosyayı kaydet
            file_path = f"feeds/{feed_id}.xml"
            fg.rss_file(file_path)
            print(f"Başarılı: {file_path}")

        except Exception as e:
            print(f"HATA ({info['title']}): {e}")

if __name__ == "__main__":
    generate_rss()
