# Lab 2 Çözüm – Kaynaklar ve Referanslar (Hocaya Açıklama)

Bu belge, çözüm notebook’unda kullanılan **CAPEX/OPEX** ve **elektrik fiyatı** verilerinin nereden alındığını özetler; hocaya sunarken kullanabilirsiniz.

---

## 1. Elektrik fiyatı (gelir / NPV için)

| Ne kullanıldı? | Kaynak (resmi) | Açıklama |
|----------------|----------------|----------|
| Çeyreklik ortalama spot fiyat (AUD/MWh) | **Australian Energy Regulator (AER)** – Quarterly volume weighted average spot prices by region | NEM bölgeleri (Queensland, NSW, Victoria, South Australia, Tasmania) için çeyreklik hacim-ağırlıklı ortalama spot fiyatları. Veri CSV olarak AER sitesinden indirilebilir. |
| Resmi sayfa | https://www.aer.gov.au/industry/registers/charts/quarterly-volume-weighted-average-spot-prices-regions | Chart + “Download” ile CSV (ör. `AER_Spot prices_Quarterly VWA spot prices DATA_2_….CSV`). |
| Bölge notu | Perth (Batı Avustralya) **NEM’de değil**; SWIS/WEM piyasasında. | Bu yüzden NEM bölgeleri ortalaması **vekil (proxy)** olarak kullanıldı. WA’ya özel fiyat için: AEMO WEM verisi, [data.wa.aemo.com.au](https://data.wa.aemo.com.au/). |

**Hocaya söyleyebileceğiniz:** “Elektrik fiyatını AER’in resmi çeyreklik VWA spot fiyat verisinden aldım. Perth NEM’de olmadığı için NEM bölgeleri ortalamasını proxy olarak kullandım; kaynağı ve varsayımı notebook’ta ve bu referans belgesinde belirttim.”

---

## 2. Wave CAPEX / OPEX / ömür

| Parametre | Kullanılan değer | Kaynak |
|-----------|------------------|--------|
| CAPEX | 3 500 USD/kW | Literatür: de Castro et al. (2024) Galician coast çalışması (~3 M€/MW CAPEX); NREL/Tethys marine energy maliyet aralıkları. |
| OPEX | 60 USD/kW-yıl | Marine/wave O&M literatürü (NREL, Tethys); önceki 300 USD/kW-yr birim/rapor riski nedeniyle revize edildi. |
| Ömür | 20 yıl | Dalga projeleri için yaygın varsayım (20–25 yıl); deniz ortamı nedeniyle 20 yıl seçildi. |

**Hocaya söyleyebileceğiniz:** “Wave maliyetlerini 2021’deki tek bir rapora değil, 2024 literatürüne (Galician coast, NREL/Tethys) dayandırdım; CAPEX 3 500 USD/kW, OPEX 60 USD/kW-yıl ve ömür 20 yıl olarak güncellendi.”

---

## 3. Solar PV ve onshore wind

| Teknoloji | CAPEX / OPEX / ömür | Kaynak |
|-----------|----------------------|--------|
| Solar PV | 900 USD/kW, 18 USD/kW-yr, 25 yıl | IRENA, *Renewable Power Generation Costs in 2023* (2024). Utility-scale solar için global ortalama CAPEX ~900 USD/kW, O&M ~18 USD/kW-yr bandında; değerler doğru. |
| Onshore wind | 1 200 USD/kW, 32 USD/kW-yr, 25 yıl | IRENA aynı raporlar. |

---

## 4. Özet tablo (hocaya göstermek için)

| Veri | Kaynak (kısa) | Resmi link / not |
|------|----------------|-------------------|
| Elektrik fiyatı | AER Quarterly VWA spot prices | [AER – Quarterly VWA spot prices](https://www.aer.gov.au/industry/registers/charts/quarterly-volume-weighted-average-spot-prices-regions); NEM ortalaması, Perth için proxy. |
| Wave CAPEX/OPEX | de Castro et al. 2024, NREL/Tethys | Galician coast ~3 M€/MW; NREL/Tethys marine energy. |
| Solar/Wind | IRENA | Renewable Power Generation Costs in 2023 (veya güncel yıl). |

Bu belgeyi hocaya “verileri nereden çektim” diye açıklarken referans olarak kullanabilirsiniz.
