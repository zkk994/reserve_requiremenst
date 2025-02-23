import streamlit as st
import pandas as pd

# Başlık
st.title('Mevduat Parametre Yönetimi ve Hesaplama Uygulaması')

# Mevcut parametreler
default_parametreler = pd.DataFrame({
    'Vade Aralığı (Ay)': ['<1 Ay', '1-3 Ay', '3-6 Ay', '6-12 Ay', '>12 Ay'],
    'ZK Oranı': [0.17, 0.17, 0.17, 0.10, 0.10],

    'ZK Faiz Oranı': [0.37, 0.37, 0.00, 0.00, 0.00]
})

default_doviz_parametreler = pd.DataFrame({
    'Vade Aralığı (Ay)': ['<1 Ay', '1-3 Ay', '3-6 Ay', '6-12 Ay', '>12 Ay'],
    'ZK Oranı': [0.30, 0.26, 0.26, 0.26, 0.20],
    'Ek Oran': [0.04, 0.04, 0.04, 0.04, 0.04],
    'ZK Faiz Oranı': [0.00, 0.00, 0.00, 0.00, 0.00]
})

st.subheader('TL Zorunlu Karşılık Parametreleri')
parametreler = st.data_editor(default_parametreler, num_rows='dynamic')

st.subheader('Döviz Zorunlu Karşılık Parametreleri')
doviz_parametreler = st.data_editor(default_doviz_parametreler, num_rows='dynamic')

# Excel dosyası yükleme
uploaded_file = st.file_uploader('Mevduat Excel Dosyasını Yükleyin (.xlsx)', type='xlsx')

# Run butonu
if st.button('Run') and uploaded_file is not None:
    # Mevduat verilerini yükle
    mevduat_data = pd.read_excel(uploaded_file)
    
    # Dinamik ZK ve ek oran fonksiyonları
    def dinamik_zk_orani(vade, parametreler_df, column_name='ZK Oranı'):
        if vade <= 1:
            return parametreler_df.loc[parametreler_df['Vade Aralığı (Ay)'] == '<1 Ay', column_name].values[0]
        elif 1 < vade <= 3:
            return parametreler_df.loc[parametreler_df['Vade Aralığı (Ay)'] == '1-3 Ay', column_name].values[0]
        elif 3 < vade <= 6:
            return parametreler_df.loc[parametreler_df['Vade Aralığı (Ay)'] == '3-6 Ay', column_name].values[0]
        elif 6 < vade <= 12:
            return parametreler_df.loc[parametreler_df['Vade Aralığı (Ay)'] == '6-12 Ay', column_name].values[0]
        else:
            return parametreler_df.loc[parametreler_df['Vade Aralığı (Ay)'] == '>12 Ay', column_name].values[0]

    # ZK, Ek Oran ve ZK Faiz Oranı hesaplama
    mevduat_data['ZK Oranı'] = mevduat_data.apply(
        lambda row: dinamik_zk_orani(row['Vade'], parametreler, 'ZK Oranı')
        if row['Para Birimi'] == 'TL'
        else dinamik_zk_orani(row['Vade'], doviz_parametreler, 'ZK Oranı'),
        axis=1
    )

    mevduat_data['Ek Oran'] = mevduat_data.apply(
        lambda row: dinamik_zk_orani(row['Vade'], doviz_parametreler, 'Ek Oran') 
        if row['Para Birimi'] != 'TL' 
        else 0, 
        axis=1
    )
    
    mevduat_data['ZK Faiz Oranı'] = mevduat_data.apply(
        lambda row: dinamik_zk_orani(row['Vade'], parametreler, 'ZK Faiz Oranı') 
        if row['Para Birimi'] == 'TL' 
        else dinamik_zk_orani(row['Vade'], doviz_parametreler, 'ZK Faiz Oranı'), 
        axis=1
    )
    
    
    
    # ZK ve ek tutarları hesaplama
    mevduat_data['ZK Tutarı'] = mevduat_data['Tutar'] * mevduat_data['ZK Oranı']
    mevduat_data['Ek Tutar'] = mevduat_data['Tutar'] * mevduat_data['Ek Oran']
    
    # Toplam blokaj hesaplama
    mevduat_data['Toplam Blokaj'] = mevduat_data['ZK Tutarı'] + mevduat_data['Ek Tutar']
    
    # Serbest Kaynak hesaplama
    mevduat_data['Serbest Kaynak'] = mevduat_data['Tutar'] - mevduat_data['Toplam Blokaj']
    
    # Mevduat ve ZK nema gelirleri
    mevduat_data['Mevduat Faiz Maliyeti'] = mevduat_data['Tutar'] * (mevduat_data['Yıllık Faiz']) * (mevduat_data['Vade'] / 12)
    mevduat_data['ZK Nema Geliri'] = mevduat_data['ZK Tutarı'] * mevduat_data['ZK Faiz Oranı'] * (mevduat_data['Vade'] / 12)
    
    # Efektif maliyet ve yıllıklandırılmış basit faiz hesaplama
    mevduat_data['Dönemsel Efektif Maliyet'] = (mevduat_data['Mevduat Faiz Maliyeti'] - mevduat_data['ZK Nema Geliri']) / mevduat_data['Serbest Kaynak']
    mevduat_data['Yıllıklandırılmış Basit Maliyet'] = mevduat_data['Dönemsel Efektif Maliyet'] * (12 / mevduat_data['Vade'])


    # Sonuçları ekrana yazdır
    st.subheader('Hesaplama Sonuçları')
    st.write(mevduat_data)
    
    # Sonuçları Excel'e kaydetme
    output_path = 'mevduat_sonuc.xlsx'
    mevduat_data.to_excel(output_path, index=False)
    st.download_button('Sonuçları İndir', output_path)

else:
    st.warning('Lütfen geçerli bir Excel dosyası yükleyin ve ardından Run butonuna basın.')
