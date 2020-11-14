# ccsds-odm

CCSDS Orbit Data Messages Python ile Okuma/Yazma
================================================

Giriş
--------------
Uydular ile ilgilenen akademisyenler, şirketler ve kurumlar uyduların yörünge (orbit), uzayda izledikleri yol (trajectory) ve
yönelim (attitude) verilerini oluşturmak, iletmek ve kullanmak için çeşitli dosya formatları kullanırlar. Bu formatlar arası
karışıklıklar (birimler, parametre tanımları ve modeller) verilerin doğru şekilde kullanılmasını engelleyebilir ve hatalara yol
açabilir. Bu nedenle verilerin tam ve doğru şekilde oluşturulması ve kullanılması için CCSDS 
`Orbit Data Messages <https://public.ccsds.org/Pubs/502x0b2c1.pdf>`_ adlı bir standart oluşturmuştur.

Bu standart, XML Schema Tanım Dosyaları (XSD Dosyaları) ile detaylı bi şekilde tanımlanır ve XML dosyaları şeklinde oluşturulur. 

Problem Tanımı
--------------

1. Bu standart XML dosyalarını okuyacak, yazacak ve bu arada XSD Dosyasında tanımlı kısıtlarla verilerin doğruluğunu 
   denetleyecek açık kaynak kodlar çok sınırlıdır (örn. Orekit). Python'da ise bunu yapacak bir açık kaynak kod bulunmamaktadır.
2. Standartlardaki XSD Dosyaları ve sonuçta oluşan XML dosyalarının sayısı çok fazladır ve bazı alanlar ortaktır. Bu nedenle XML 
   verilerini oluşturacak ve okuyacak kodları yazmak çok miktarda zamana mal olabilir.
3. Buna ek olarak, XSD Dosyaları her standart güncellemesinde değişebilmektedir. Bu nedenle dosyaların standart güncellemeleri 
   ile güncellenmesi gerekmektedir. Buna ek olarak belli standartlara geri uyumluluk da gerekebilir.
4. Bu kütüphanenin potansiyel kullanıcıları dünyadaki akademisyenler, amatör uyduları işleten üniversiteler ve bunlar için kod 
   geliştiren amatör ve açık kaynak topluluklarıdır. Bu nedenle İngilizce dokümantasyon, iyi test ve iyi bir geliştirme ortamı
   gereklidir.


Proje İsterleri
----------------

1. İşlev:
   
   1. Yazılım XSD dosyalarına göre oluşturulmuş XML dosyalarını okuyabilecek, XSD dosyalarında tanımlanmış doğruluk 
      kontrollerini yapabilecek ve bu dosyalara uygun olarak XML dosyalarını oluşturabilecektir.

   2. Yazılım, bu XML dosyalarının okunan içeriğini kullanıcılara bir nesne (object) halinde verecek ve yine bu nesne 
      içeriğini XML dosyasına yazmak üzere kullanıcıdan alacaktır.
      
2. Test: 
   
   1. Yazılım en az %90 coverage olacak şekilde testlerle doğrulanacaktır. 
   2. Testler bir "Continuous Integration" ortamı üstünde çalışacaktır. 
   
3. Dokümantasyon: 
   
   1. Yazılım kod seviyesinde (her bir sınıf, fonksiyon ve parametre) dokümante edilecektir.
   2. Yazılımın örnek kullanımları gösteren ve tasarımı anlatan bir kullanım kılavuzu bulunacaktır.
   3. Dokümantasyon standardı Restructured Text olacaktır. (Bu ister bir örnek, talep gelirse Markdown da olabilir)
   4. Dokümanlar Readthedocs ya da GitHub docs gibi bir çevrimiçi ortamda yayınlanacaktır.
   5. Dokümantasyon dili İngilizce olacaktır.

4. Dağıtım
   
   1. Proje paketi PyPI ile Conda ya da Conda-forge üzerinden dağıtılacaktır. 
 
Tasarım Notları
------------------

Temelde iki tasarım alternatifi göze çarpmaktadır:
1. XSD dosyalarından otomatik olarak nesneleri içeren ve XML okuyan/yazan kodun yaratılması. 
   (örn. `generateDS <https://sourceforge.net/projects/generateds/>`_)
2. XSD ile XML kodunun otomatik olarak okunması, test edilmesi ve yazılması; sınıfların yaratılması işinin
   geliştirici ekip tarafından yapılması. (örn. `xmlschema <https://pypi.org/project/xmlschema/>`_)
   
İlk alternatif, özellikle standartlarda gerçekleşen değişikliklerin nesne yapılarına hızla geçirilebilmelerini sağlar. XSD
dosyalarından yeni nesne dosyaları tek seferde üretilebilir. Ancak, en azından `generateDS` özelinde, otomatik olarak
üretilen kodlar son derece karmaşıktır ve kullanımları zordur.

İkinci alternatif, dosya okuma, kontrol ve yazma işlerini bir başka kütüphaneye devreder. Ancak, en azından `xmlschema` 
özelinde, özellikle dosya yazmak için dosya tipine ait _XML tag_ yapısını bilmek mecburidir. Bu nedenle geliştirici ekibin,
kullanıcının dolduracağı nesneyi hazırlayıp bu nesneyi _tag_'lerle ilişkilendiren kodu yazması ve standart değişimlerinde de 
güncel tutması gerekir.
