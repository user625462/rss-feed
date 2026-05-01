import os
import requests
from datetime import datetime
import pytz
from feedgen.feed import FeedGenerator

# Tüm API linklerimiz
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

def is_valid_image(url):
    if not url or not isinstance(url, str):
        return False
    return any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])

def get_full_content(item_id, item_type):
    """Her bir içeriğin detay sayfasına (GetById) gidip tam metni çeker."""
    try:
        if item_type == 'haber':
            url = f"https://gateway-api.mku.edu.tr/website/api/Haber/GetById?Id={item_id}"
        else:
            url = f"https://gateway-api.mku.edu.tr/website/api/Duyuru/GetById?Id={item_id}"
            
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            return data.get(f'{item_type}Icerik')
    except Exception:
        pass
    return None

def generate_rss():
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
            response = requests.get(info['url'], timeout=10)
            response.raise_for_status()
            data = response.json().get('data', [])

            for item in data:
                fe = fg.add_entry()
                
                # Dinamik Değişken Atamaları (Haber mi Duyuru mu?)
                item_type = info['type']
                item_id = item.get(f'{item_type}Id', '')
                title = item.get(f'{item_type}Baslik', 'Başlıksız')
                ozet = item.get(f'{item_type}Ozet')
                date_str = item.get(f'{item_type}Tarih')
                
                # Kapak resmi URL'si
                raw_image = item.get(f'{item_type}StandartImageUrl') or item.get(f'{item_type}ThumbImageUrl')
                if not raw_image and item_type == 'duyuru':
                    raw_image = item.get('duyuruDosyaUrl') or item.get('kucukResim')
                    
                link = f"https://mku.edu.tr/{'news' if item_type == 'haber' else 'announcements'}/{item_id}"

                # 1. Adım: Tam metni GetById API'si ile ÖZEL olarak çek!
                full_icerik = get_full_content(item_id, item_type)
                
                # 2. Adım: Hangi metni kullanacağımıza karar ver
                if full_icerik and len(str(full_icerik).strip()) > 0:
                    main_text = str(full_icerik)
                elif item.get(f'{item_type}Icerik'):
                    main_text = str(item.get(f'{item_type}Icerik'))
                elif ozet:
                    main_text = str(ozet)
                else:
                    main_text = str(title)

                fe.id(str(item_id))
                fe.title(str(title))
                fe.link(href=link)

                # 3. Adım: Resim URL Düzeltmesi (Kırık Resim Çözümü)
                image_tag = ""
                if is_valid_image(raw_image):
                    clean_image = str(raw_image).strip()
                    if not clean_image.startswith('http'):
                        # Eğer admin klasöründeyse doğrudan mku.edu.tr'yi kullan
                        if clean_image.startswith('admin/'):
                            clean_image = 'https://mku.edu.tr/' + clean_image
                        else:
                            clean_image = 'https://files.mku.edu.tr/' + clean_image.lstrip('/')
                    
                    image_tag = f'<img src="{clean_image}" alt="{title}" style="max-width:100%; border-radius:8px; margin-bottom:15px;"/><br><br>'
                    fe.enclosure(clean_image, 0, 'image/jpeg')

                # Her şeyi birleştirip RSS'e bas
                full_html = f"<div>{image_tag}{main_text}</div>"
                fe.description(full_html)

                # Tarih İşleme
                if date_str:
                    try:
                        dt = datetime.strptime(str(date_str).split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        dt = TIMEZONE.localize(dt)
                        fe.pubDate(dt)
                    except Exception:
                        pass

            # XML dosyasını oluştur
            fg.rss_file(f"feeds/{feed_id}.xml")
        except Exception as e:
            print(f"HATA ({info['title']}): {e}")

if __name__ == "__main__":
    generate_rss()
