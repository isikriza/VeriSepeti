# VeriSepeti

Gerekli paketleri yüklemek için:

```
pip install -r requirements.txt
```

Projeyi doğru bir şekilde çalıştırmak için aşağıdaki drive klasöründen "db.sqlite3" dosyasını indirip manage.py dosyasının olduğu konuma koymanız gerekmektedir.

https://drive.google.com/drive/folders/1__V2O7Usi6AYUb_ghUvcmHoCYRMnFbTb?usp=sharing

Daha sonra manage.py scriptini şu şekilde çalıştırarak localde django projesini aktif hale getirmelisiniz.

```
python manage.py runserver
```

Web uygulamasını kullanmak için tarayıcıdan http://127.0.0.1:8000/ adresine gitmelisiniz.

Yukarıda paylaştığım drive klasöründe ayrıca bir de colab notebook var. Bu notebookta şu ana kadar çektiğim tüm verileri kullanarak bir takım işlemler gerçekleştirdim.
Herbir restoranın yorum sayısı, yorum puanları, yemek sayısı ve fiyatları, günlük yorum sıklığına göre restoranlar için bir clustering uyguladım.
Elimdeki veriye göre elbow metodunu kullanarak en uygun sayıda cluster sayısını (3) çıkarttım ve buna göre k-means algoritmasını çalıştırdım. Colab notebookunda bunu nasıl yaptığımı görebilirsiniz.
Bunlara ek olarak, bir yemek önerisi algoritması geliştirdim. Seçtiğiniz yemek için geliştirdiğim algoritmadan alınan skorlara göre en iyiden en kötüye sıralayarak bir restoran listesi veriyor. Bu algoritma yorumlarda geçen yemeklerin, yorum puanına ve sıklığına göre bir skor hesaplıyor ve en iyi skorları listeliyor. Algoritmanın nasıl hesaplandığı colab notebookunda mevcuttur.

Yemek puanı şu şekilde hesaplanmaktadır:
Yemek puanı = (yapılan yorumun ortalama puanı * 0.5) + ((yemeğin yorumlarda geçme sayısı * 0.5) / 6.9)

Not: 6.9 değeri tüm restoranlardaki yemeklerin sıklığının ortalaması alınarak bulunmuştur. Normalize etmek için kullanıyorum.
