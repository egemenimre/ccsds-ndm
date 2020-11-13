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
2. Standartlardaki XSD Dosyaları ve sonuçta oluşan XML dosyalarının sayısı çok fazladır ve bazı alanlar ortaktır. Bu
nedenle XML verilerini oluşturacak ve okuyacak kodları yazmak çok miktarda zamana mal olabilir.
3. Buna ek olarak, XSD Dosyaları her standart güncellemesinde değişebilmektedir. Bu nedenle dosyaların standart güncellemeleri
ile güncellenmesi gerekmektedir. Buna ek olarak belli standartlara geri uyumluluk da gerekebilir.
4. Bu kütüphanenin kullanıcıları dünyadaki akademisyenler, amatör uyduları işleten üniversiteler ve bunlar için kod geliştiren
amatör ve açık kaynak topluluklarıdır. Bu nedenle İngilizce dokümantasyon, iyi test ve iyi bir geliştirme ortamı gereklidir.

Proje İsterleri
----------------
