### Gerekli import işlemlerinin ve görüntü ayarlarının yapılması. ###
import datetime as dt
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

### Veri setinin okutulması ve bir kopyasının alınması. ###
df_ = pd.read_excel( "/Users/ilayda/Desktop/MİUUL/crmAnalytics/datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()

# VERİYİ ANLAMA #
df.head()
df.shape
df.isnull().sum()

### Eşsiz ürün sayısı için ###
df["Description"].nunique()

### Hangi üründen kaç tane var? ###
df["Description"].value_counts().head()

### En çok sipariş edilen ürün ###
df.groupby("Description").agg({"Quantity": "sum"}).head()

### Her üründe toplam verilen sipariş miktarı ###
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()

### Toplam kaç tane eşsiz fatura kesilmiş? ###
df["Invoice"].nunique()

### Her ürün için tam fiyat ###
df["TotalPrice"] = df["Quantity"] * df["Price"]

### Fatura başına toplam tutar ###
df.groupby("Invoice").agg({"TotalPrice": "sum"}).head()

# VERİYİ HAZIRLAMA #

df.shape
df.isnull().sum()
df.dropna(inplace=True)   #eksik değerleri silme
df.describe().T

# Invoice'larda başında "C" olanlar iadeyi ifade etmekte. İadeler ise quantity değerini eksiye düşürmekte.
# Bu yüzden iadeleri faturadan çıkarmalıyız.

df = df[~df["Invoice"].str.contains("C", na=False)]

filtre = ("InvoiceDate" < "2011-01-01") | ("InvoiceDate" >= "2012-01-01")
tarihler_filtrasyonlu = "InvoiceDate"[filtre]
print(tarihler_filtrasyonlu)


# RFM METRİKLERİNİN HESAPLANMASI #

df.head()
df["InvoiceDate"].max()

# Hesap yapabilmek için en son ki fatura tarihinin iki gün sonrasını günümüz varsayalım
today_date = dt.datetime(2011, 12, 11)


rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days, #Recency
                                     "Invoice": lambda Invoice: Invoice.nunique(), #Frequency
                                     "TotalPrice": lambda TotalPrice: TotalPrice.sum()}) #Monetary

rfm.head()

# Sütun isimlerinin RFM metrikleri ile değiştirilmesi
rfm.columns = ["Recency", "Frequency", "Monetary"]

# Monetary metriğinde görünen sıfırın kaldırılması
rfm = rfm[rfm["Monetary"] > 0]

rfm.shape

# RFM SKORLARININ HESAPLANMASI #
rfm["Recency_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1])
rfm.head()

rfm["Frequency_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm.head()

rfm["Monetary_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5])
rfm.head()

# Recency ve Frequency metriklerinin stirnge çevrilmesi
rfm["RFM_SCORE"] = (rfm["Recency_Score"].astype(str) +
                    rfm["Frequency_Score"].astype(str))

# Skor tablosunda şampiyon müşterileri görmek için;
rfm[rfm["RFM_SCORE"] == "55"]

# RFM SEGMENTLERİNİN OLUŞTURULMASI VE ANALİZ EDİLMESİ #

# RFM segment isimlendirmesi
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

# Segmentlerin yazdığı yeni bir "Segment" kolonunun oluşturulması
rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)

# Segmentlerin metrikler üzerinden sayı ve ortalamalarına bakılması
rfm[["Segment", "Recency", "Frequency", "Monetary"]].groupby("Segment").agg(["mean", "count"])

rfm.head()

df.head()

###############################################################
# Tüm Sürecin Fonksiyonlaştırılması
###############################################################

def create_rfm(dataframe, csv=False):

    # Veriyi Hazırlama
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    # RFM Metriklerinin Hesaplanması
    today_date = dt.datetime(2011, 12, 11)
    rfm = dataframe.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                                'Invoice': lambda num: num.nunique(),
                                                "TotalPrice": lambda price: price.sum()})
    rfm.columns = ['Recency', 'Frequency', "Monetary"]
    rfm = rfm[(rfm['Monetary'] > 0)]

    # RFM Skorlarının Hesaplanması
    rfm["Recency_Score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["Frequency_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["Monetary_Score"] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])

    # cltv_df skorları kategorik değere dönüştürülüp df'e eklendi
    rfm["RFM_SCORE"] = (rfm['Recency_Score'].astype(str) +
                        rfm['Frequency_Score'].astype(str))


    # Segmentlerin Isimlendirilmesi
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    rfm = rfm[["Recency", "Frequency", "Monetary", "Segment"]]
    rfm.index = rfm.index.astype(int)

    if csv:
        rfm.to_csv("rfm.csv")
        return rfm

df = df_.copy()

rfm_new = create_rfm(df, csv=True)




