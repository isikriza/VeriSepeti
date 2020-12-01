from django.shortcuts import render, redirect
from .models import Restoran
from .models import Semt
from .models import Menu
from .models import Yorum
from .forms import RestoranForm
from .forms import SemtForm
from .forms import MenuForm
from .forms import YorumForm
from django.contrib import messages
from django.db.models import Max

import json
from json import dumps
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd


with open('ne_yesem/sehirler.json', 'r') as f:
    sehirler = json.load(f)
with open('ne_yesem/ilceler.json', 'r') as f:
    ilceler = json.load(f)

Tr2Eng = str.maketrans("çğıöşüİĞÜÇÖŞ", "cgiosuIGUCOS")
df_yemek = pd.read_csv('res_yemek_skor.csv').sort_values(by=['yemek_skor'], ascending=False)
df_cls = pd.read_csv('res_cls.csv')


def insert_restaurants(form_dict):
    url = 'https://www.yemeksepeti.com/' + form_dict['il'] + '/' + \
          form_dict['semt']
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    restaurants = soup.find_all('div', class_='ys-item')
    print(len(restaurants))
    count = 1
    for restaurant in restaurants:
        try:
            is_new_res = False
            res_name = str(restaurant.a.text).strip()
            res_il = str(form_dict['il'])
            res_link = "https://www.yemeksepeti.com" + str(restaurant.a.attrs['href'])
            html_res = requests.get(res_link).text
            bs4_soup = BeautifulSoup(html_res, "html.parser")
            points = bs4_soup.find_all('span', class_='point')
            res_hiz = float(str(points[0].text).strip().replace(",", "."))
            res_lezzet = float(str(points[1].text).strip().replace(",", "."))
            res_servis = float(str(points[2].text).strip().replace(",", "."))

            calisma_saati = str(bs4_soup.find_all('div', class_='highlightText')[0].text)
            if "24 Saat" in calisma_saati or "24 Hours" in calisma_saati:
                res_acilis_zamani = "00:00:00"
                res_kapanis_zamani = "23:59:00"
            else:
                res_acilis_zamani = calisma_saati.split(' - ')[0] + ':00'
                res_kapanis_zamani = calisma_saati.split(' - ')[1] + ':00'

            hafta_count = len(bs4_soup.find_all('div', class_='ysTooltipItem'))
            if 5 < hafta_count:
                res_haftaici = True
                res_haftasonu = True
            elif 2 < hafta_count <= 5:
                res_haftaici = True
                res_haftasonu = False
            else:
                res_haftaici = False
                res_haftasonu = True

            res_info = {'name': res_name,
                        'il': res_il,
                        'hiz': res_hiz,
                        'lezzet': res_lezzet,
                        'servis': res_servis,
                        'acilis_zamani': res_acilis_zamani,
                        'kapanis_zamani': res_kapanis_zamani,
                        'haftaici': res_haftaici,
                        'haftasonu': res_haftasonu}
            print(count, res_name, res_il, res_hiz, res_lezzet, res_servis, res_acilis_zamani,
                  res_kapanis_zamani, res_haftaici, res_haftasonu)
            count += 1
            res_form = RestoranForm(res_info)
            print('Res Form:', res_form.is_valid())
            if len(Restoran.objects.filter(name=res_name, il=res_il)) == 0 and res_form.is_valid():
                is_new_res = True
                res_form.save()

            res_semt = str(form_dict['semt'])
            semt_min_tutar = str(bs4_soup.find_all('div', class_='shortInfoItem')[0].attrs['aria-label'])
            semt_min_tutar = float(semt_min_tutar.split(' ')[2].replace(',', '.'))
            res_objs = Restoran.objects.filter(name=res_name, il=res_il)
            print(res_semt, semt_min_tutar, res_objs.first())

            semt_form = SemtForm({'semt_mahalle_adi': res_semt,
                                  'minimum_tutar': semt_min_tutar,
                                  'restoran': res_objs.first()})
            print('Semt Form:', semt_form.is_valid())
            if len(Semt.objects.filter(semt_mahalle_adi=res_semt, restoran=res_objs.first())) == 0 and semt_form.is_valid():
                semt_form.save()

            insert_menus(res_objs.first(), res_link)
            insert_yorums(res_objs.first(), res_link, is_new_res)
        except:
            continue


def insert_menus(res_obj, res_link):
    html_res = requests.get(res_link).text
    bs4_soup = BeautifulSoup(html_res, "html.parser")
    yemekler = bs4_soup.find_all('div', class_='product-info')
    fiyatlar = bs4_soup.find_all('div', class_='product-price')
    if len(yemekler) == 0 and len(fiyatlar) == 0:
        yemekler = bs4_soup.find_all('div', class_='productName')
        fiyatlar = bs4_soup.find_all('div', class_='price-wrapper')

    for i in range(len(yemekler)):
        try:
            yemek = str(yemekler[i].text).strip()
            fiyat = float(str(fiyatlar[i].text).strip().split(' ')[0].replace(',', '.'))
            menu_form = MenuForm({'yemek': yemek,
                                  'fiyat': fiyat,
                                  'restoran': res_obj})
            if len(Menu.objects.filter(yemek=yemek, fiyat=fiyat, restoran=res_obj)) == 0 and menu_form.is_valid():
                print('Menu Form:', menu_form.is_valid())
                menu_form.save()
        except:
            continue


def insert_yorums(res_obj, res_link, is_new_res):
    args = Yorum.objects.filter(restoran=res_obj)
    pg_idx = 1
    while True:
        finish = False
        url = res_link + "?section=comments&page=" + str(pg_idx)
        print(pg_idx, url)
        html_res = requests.get(url).text
        bs4_soup = BeautifulSoup(html_res, "html.parser")
        pages = bs4_soup.find_all('ul', class_='ys-commentlist-page pagination')
        try:
            last_pg_idx = len(str(pages[0]).split('> <')) - 2
        except:
            continue
        comments = bs4_soup.find_all('div', class_='comments-body')

        for comment in comments:
            if "restaurantPoints" not in str(comment):
                continue
            else:
                try:
                    points = str(comment.text).strip().split('   ')[0]
                    date = str(comment.text).strip().split('   ')[1].strip()
                    ii = str(comment).index('<p>') + 3
                    jj = str(comment).index('</p>')
                    comment_text = str(comment)[ii:jj]
                    yorum_hiz = -1.0
                    yorum_lezzet = -1.0
                    yorum_servis = -1.0
                    for p in points.split(' | '):
                        print(p)
                        if 'Hız: ' in p:
                            yorum_hiz = float(p.split(': ')[1])
                        elif 'Servis: ' in p:
                            yorum_servis = float(p.split(': ')[1])
                        elif 'Lezzet: ' in p:
                            yorum_lezzet = float(p.split(': ')[1])

                    yorum_date = datetime.now().strftime("%Y-%m-%d")
                    if "gün önce" in date:
                        N = int(date.split(' ')[0])
                        yorum_date = (datetime.now() - timedelta(days=N)).strftime("%Y-%m-%d")
                    elif "ay önce" in date:
                        N = int(date.split(' ')[0])
                        yorum_date = (datetime.now() - timedelta(days=N * 30)).strftime("%Y-%m-%d")
                    elif "yıl önce" in date:
                        N = int(date.split(' ')[0])
                        yorum_date = (datetime.now() - timedelta(days=N * 365)).strftime("%Y-%m-%d")

                    if args.aggregate(Max('yorum_date'))['yorum_date__max'] is not None:
                        print('MAX:', args.aggregate(Max('yorum_date'))['yorum_date__max'].strftime("%Y-%m-%d"))
                    if not is_new_res:
                        if yorum_date < args.aggregate(Max('yorum_date'))['yorum_date__max'].strftime("%Y-%m-%d"):
                            finish = True
                            break

                    yorum_form = YorumForm({'yorum_hiz': yorum_hiz,
                                            'yorum_lezzet': yorum_lezzet,
                                            'yorum_servis': yorum_servis,
                                            'yorum_date': yorum_date,
                                            'yorum_icerik': comment_text,
                                            'restoran': res_obj})

                    if len(Yorum.objects.filter(yorum_icerik=comment_text,
                                                yorum_date=yorum_date, restoran=res_obj)) == 0 and yorum_form.is_valid():
                        print('Yorum Form:', yorum_form.is_valid())
                        yorum_form.save()
                except:
                    continue
        if finish:
            break
        pg_idx += 1
        try:
            i = str(pages[0]).split('> <')[last_pg_idx].index('page=') + 5
            j = str(pages[0]).split('> <')[last_pg_idx].rindex('">')
        except:
            break
        if int(str(pages[0]).split('> <')[last_pg_idx][i:j]) < pg_idx:
            break


def home(request):
    if request.method == 'POST':
        il = request.POST.get("il", "")
        semt = request.POST.get("semt", "")
        acilis_zamani = request.POST.get("acilis_zamani", "")
        kapanis_zamani = request.POST.get("kapanis_zamani", "")
        minimum_tutar = request.POST.get("minimum_tutar", "")
        minimum_puan = request.POST.get("minimum_puan", "")
        yorum_date = request.POST.get("yorum_date", "")
        haftaici = False
        haftasonu = False
        if request.POST.get("haftaici", "") == 'on':
            haftaici = True
        if request.POST.get("haftasonu", "") == 'on':
            haftasonu = True

        getir_but = request.POST.get("getir", "")
        kesfet_but = request.POST.get("kesfet", "")

        if len(il) == 0 or len(semt) == 0:
            messages.info(request, 'İl ve Semt seçmelisiniz!')
            return redirect('ne_yesem-home')

        form_dict = {'il': sehirler[int(il)]['sehir_adi'],
                     'semt': ilceler[int(semt)]['ilce_adi'],
                     'acilis_zamani': acilis_zamani,
                     'kapanis_zamani': kapanis_zamani,
                     'minimum_tutar': minimum_tutar,
                     'minimum_puan': minimum_puan,
                     'yorum_date': yorum_date,
                     'haftaici': haftaici,
                     'haftasonu': haftasonu
                     }
        request.session['form'] = form_dict

        if len(getir_but) > 0:
            insert_restaurants(form_dict)
            messages.info(request, 'İstenilen koşullar için veri çekildi ve veri tabanına eklendi.')
            return redirect('ne_yesem-home')
        if len(kesfet_but) > 0:
            return redirect('restaurant-list')
        else:
            return redirect('ne_yesem-home')
    else:
        sehirlerJSON = dumps({'sehirler': sehirler})
        ilcelerJSON = dumps({'ilceler': ilceler})
    return render(request, 'ne_yesem/home.html', {'data_sehirler': sehirlerJSON,
                                                  'data_ilceler': ilcelerJSON})


def restaurants(request):
    il = request.session['form']['il']
    semt = request.session['form']['semt']
    acilis = request.session['form']['acilis_zamani']
    kapanis = request.session['form']['kapanis_zamani']
    min_tutar = request.session['form']['minimum_tutar']
    min_puan = request.session['form']['minimum_puan']
    yorum_tarih = request.session['form']['yorum_date']
    haftaici = request.session['form']['haftaici']
    haftasonu = request.session['form']['haftaici']

    if request.method == 'POST':
        if len(request.POST.get("yemek", "")) > 0 and len(request.POST.get("ara", "")) > 0:
            yemek = [request.POST.get("yemek", "")]
            if str(yemek[0]) == "Çiğ Köfte & Köfte":
                yemek[0] = "kofte"
            elif str(yemek[0]) == "Sandviç & Tost":
                yemek[0] = "tost"
            elif str(yemek[0]) == "Pasta & Börek":
                yemek[0] = "pasta"
            else:
                yemek[0] = str(yemek[0]).translate(Tr2Eng).lower()

            if yemek[0] == "tatli":
                yemek = ['sutlac', 'kunefe', 'baklava', 'pasta', 'lokma', 'ekler', 'tatli']
                tmp_res_ids = df_yemek[(df_yemek['yemek'] == 'sutlac') |
                                       (df_yemek['yemek'] == 'kunefe') |
                                       (df_yemek['yemek'] == 'baklava') |
                                       (df_yemek['yemek'] == 'pasta') |
                                       (df_yemek['yemek'] == 'lokma') |
                                       (df_yemek['yemek'] == 'ekler') |
                                       (df_yemek['yemek'] == 'tatli')]['res_id'].values.tolist()
            elif yemek[0] == "tost":
                yemek = ['sandvic', 'sandwich', 'tost', 'tostu']
                tmp_res_ids = df_yemek[(df_yemek['yemek'] == 'sandvic') |
                                       (df_yemek['yemek'] == 'tost') |
                                       (df_yemek['yemek'] == 'sandwich') |
                                       (df_yemek['yemek'] == 'tostu')]['res_id'].values.tolist()
            elif yemek[0] == "kebap":
                yemek = ['kebap', 'adana', 'urfa']
                tmp_res_ids = df_yemek[(df_yemek['yemek'] == 'kebap') |
                                       (df_yemek['yemek'] == 'adana') |
                                       (df_yemek['yemek'] == 'urfa')]['res_id'].values.tolist()
            elif yemek[0] == "sushi":
                yemek = ['sushi', 'susi', 'roll']
                tmp_res_ids = df_yemek[(df_yemek['yemek'] == 'sushi') |
                                       (df_yemek['yemek'] == 'susi') |
                                       (df_yemek['yemek'] == 'roll')]['res_id'].values.tolist()
            elif yemek[0] == "pasta":
                yemek = ['pasta', 'borek', 'boregi']
                tmp_res_ids = df_yemek[(df_yemek['yemek'] == 'pasta') |
                                       (df_yemek['yemek'] == 'borek') |
                                       (df_yemek['yemek'] == 'boregi')]['res_id'].values.tolist()
            else:
                tmp_res_ids = df_yemek[df_yemek['yemek'] == yemek[0]]['res_id'].values.tolist()
            res_obj = Restoran.objects.filter(il=il,
                                              lezzet__gte=min_puan,
                                              acilis_zamani__lte=acilis,
                                              kapanis_zamani__gte=kapanis,
                                              haftaici=haftaici,
                                              haftasonu=haftasonu,
                                              semt__semt_mahalle_adi=semt,
                                              semt__minimum_tutar__gte=min_tutar,
                                              yorum__yorum_date__lte=yorum_tarih).distinct()

            res_ids = []
            for x in tmp_res_ids:
                for y in res_obj:
                    if x == y.pk:
                        res_ids.append(x)

            res_obj = Restoran.objects.filter(pk__in=res_ids,
                                              il=il,
                                              lezzet__gte=min_puan,
                                              acilis_zamani__lte=acilis,
                                              kapanis_zamani__gte=kapanis,
                                              haftaici=haftaici,
                                              haftasonu=haftasonu,
                                              semt__semt_mahalle_adi=semt,
                                              semt__minimum_tutar__gte=min_tutar,
                                              yorum__yorum_date__lte=yorum_tarih).distinct()

            semt_obj = Semt.objects.filter(restoran__in=res_obj, semt_mahalle_adi=semt)

            skorlar = []
            for res in res_obj:
                puan = []
                for yem in yemek:
                    puan_list = df_yemek[(df_yemek['yemek'] == yem) & (df_yemek['res_id'] == res.pk)]['yemek_skor'].values
                    if len(puan_list) == 0:
                        puan.append(0.0)
                    else:
                        puan.append(puan_list[0])
                skorlar.append(max(puan))

            zipped_data = sorted(zip(skorlar, res_obj, semt_obj), reverse=True, key=lambda x: x[0])
            print(zipped_data)
            context = {
                'restaurants': zipped_data
            }

        if len(request.POST.get("cluster", "")) > 0:
            res_obj = Restoran.objects.filter(il=il,
                                              lezzet__gte=min_puan,
                                              acilis_zamani__lte=acilis,
                                              kapanis_zamani__gte=kapanis,
                                              haftaici=haftaici,
                                              haftasonu=haftasonu,
                                              semt__semt_mahalle_adi=semt,
                                              semt__minimum_tutar__gte=min_tutar,
                                              yorum__yorum_date__lte=yorum_tarih).order_by('-lezzet',
                                                                                           '-hiz', '-servis').distinct()

            semt_obj = Semt.objects.filter(restoran__in=res_obj, semt_mahalle_adi=semt)

            skorlar = []
            clusters = []
            for res in res_obj:
                skorlar.append((float(res.hiz) + float(res.lezzet) + float(res.servis)) / 3.0)
                clusters.append(df_cls[df_cls['res_id'] == res.pk]['cls_label'].values[0])

            zipped_data = sorted(zip(skorlar, clusters, res_obj, semt_obj), reverse=True, key=lambda x: x[0])
            context = {
                'restaurants': zipped_data
            }
            return render(request, 'ne_yesem/restoran_clusters.html', context)
    else:
        res_obj = Restoran.objects.filter(il=il,
                                          lezzet__gte=min_puan,
                                          acilis_zamani__lte=acilis,
                                          kapanis_zamani__gte=kapanis,
                                          haftaici=haftaici,
                                          haftasonu=haftasonu,
                                          semt__semt_mahalle_adi=semt,
                                          semt__minimum_tutar__gte=min_tutar,
                                          yorum__yorum_date__lte=yorum_tarih).order_by('-lezzet',
                                                                                       '-hiz', '-servis').distinct()

        semt_obj = Semt.objects.filter(restoran__in=res_obj, semt_mahalle_adi=semt)

        skorlar = []
        for res in res_obj:
            skorlar.append((float(res.hiz) + float(res.lezzet) + float(res.servis))/3.0)

        zipped_data = sorted(zip(skorlar, res_obj, semt_obj), reverse=True, key=lambda x: x[0])
        context = {
            'restaurants': zipped_data
        }

    return render(request, 'ne_yesem/restoran_list.html', context)


def restaurants_detail(request, pk):
    res = Restoran.objects.filter(name=Restoran.objects.get(pk=pk)).first()
    semts = Semt.objects.filter(restoran=res)
    menus = Menu.objects.filter(restoran=res)

    context = {
        'restaurant': res,
        'semts': semts,
        'menus': menus,
    }
    return render(request, 'ne_yesem/restoran_detail.html', context=context)


def restaurant_comments(request, pk):
    res = Restoran.objects.filter(name=Restoran.objects.get(pk=pk)).first()
    yorums = Yorum.objects.filter(restoran=res).order_by('-yorum_date')

    context = {
        'restaurant': res,
        'yorums': yorums
    }
    return render(request, 'ne_yesem/restoran_comments.html', context=context)


def about(request):
    return render(request, 'ne_yesem/about.html')
