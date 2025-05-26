from flask import Flask, render_template, request # type: ignore
import pandas as pd
import numpy as np

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Fungsi Helper untuk Format Angka ---
def format_angka_tampilan(nilai, maks_desimal=4, presisi_untuk_angka_kecil=6):
    """
    Memformat angka untuk tampilan:
    - Jika bilangan bulat, tampilkan sebagai integer (misal: 1).
    - Jika desimal, tampilkan hingga maks_desimal, hapus nol di akhir (misal: 0.123).
    - Jika angka sangat kecil (misal: 0.00001) tidak akan ditampilkan sebagai "0" begitu saja,
      melainkan akan dicoba ditampilkan dengan presisi lebih tinggi.
    """
    if not isinstance(nilai, (int, float)):
        return str(nilai) # Fallback jika bukan angka

    epsilon_untuk_nol = 1e-9 # Angka di bawah ambang batas ini dianggap nol absolut

    if abs(nilai) < epsilon_untuk_nol:
        return "0" # Jika nilai benar-benar sangat kecil (mendekati nol), anggap nol

    nilai_dibulatkan_standar = round(nilai, maks_desimal)

    if abs(nilai_dibulatkan_standar) < epsilon_untuk_nol and abs(nilai) >= epsilon_untuk_nol:
        presisi_efektif = max(maks_desimal, presisi_untuk_angka_kecil)
        if round(nilai, presisi_efektif) == int(round(nilai, presisi_efektif)):
             return str(int(round(nilai, presisi_efektif)))
        hasil_format_kecil = f"{nilai:.{presisi_efektif}f}".rstrip('0').rstrip('.')
        return hasil_format_kecil if hasil_format_kecil and hasil_format_kecil != '.' else "0"

    if nilai_dibulatkan_standar == int(nilai_dibulatkan_standar):
        return str(int(nilai_dibulatkan_standar))
    else:
        return f"{nilai_dibulatkan_standar:.{maks_desimal}f}".rstrip('0').rstrip('.')

# --- Memuat dan Membersihkan Data ---
try:
    df = pd.read_csv('tourism_with_id.csv')
    df['Time_Minutes'] = df['Time_Minutes'].fillna(df['Time_Minutes'].mean())
    CITIES = ['Semua'] + sorted(df['City'].unique().tolist())
except FileNotFoundError:
    print("Pastikan file 'tourism_with_id.csv' ada di folder yang sama dengan app.py")
    df = pd.DataFrame()
    CITIES = ['Semua']


# --- Fungsi CRITIC dan VIKOR ---
def critic_weight(data):
    epsilon = 1e-9 
    numeric_data = data.apply(pd.to_numeric, errors='coerce') 
    if len(numeric_data) <= 1: # Jika hanya ada satu baris data atau tidak ada data
        # Kembalikan bobot rata jika tidak cukup data untuk perhitungan CRITIC yang berarti
        if not data.columns.empty:
            return pd.Series([1/len(data.columns)] * len(data.columns), index=data.columns)
        else:
            return pd.Series([]) # Kembalikan Series kosong jika tidak ada kolom

    # Normalisasi data: (nilai - min) / (max - min)
    # Handle kasus di mana max - min adalah nol (semua nilai dalam kolom sama)
    min_vals = numeric_data.min()
    max_vals = numeric_data.max()
    range_vals = max_vals - min_vals
    
    # Buat DataFrame kosong untuk hasil normalisasi
    normalized_data = pd.DataFrame(index=numeric_data.index, columns=numeric_data.columns, dtype=float)

    for col in numeric_data.columns:
        if range_vals[col] == 0:
            # Jika semua nilai dalam kolom sama, normalisasinya bisa dianggap 0 atau 0.5
            # Mengisinya dengan 0 akan membuat std_dev = 0 untuk kolom ini
            normalized_data[col] = 0 
        else:
            normalized_data[col] = (numeric_data[col] - min_vals[col]) / (range_vals[col] + epsilon)
    
    std_dev = normalized_data.std()
    
    # Jika std_dev adalah 0 untuk suatu kolom, c_j untuk kolom itu akan 0.
    # Ini akan secara alami memberi bobot 0 pada kriteria yang tidak memiliki variasi.

    corr_matrix = normalized_data.corr() 
    diff_corr = 1 - corr_matrix 
    c_j = std_dev * diff_corr.sum() 
    
    if c_j.sum() == 0: # Jika semua c_j adalah nol (misalnya semua std_dev nol atau korelasi sempurna)
        if not data.columns.empty:
            return pd.Series([1/len(data.columns)] * len(data.columns), index=data.columns) # Bobot rata
        else:
            return pd.Series([])
            
    weights = c_j / c_j.sum() 
    return weights

def vikor_method(data, weights, benefit_cols): 
    epsilon = 1e-9 
    numeric_data = data.apply(pd.to_numeric, errors='coerce') 
    
    min_vals = numeric_data.min()
    max_vals = numeric_data.max()
    range_vals = max_vals - min_vals
    normalized_data = pd.DataFrame(index=numeric_data.index, columns=numeric_data.columns, dtype=float)
    for col in numeric_data.columns:
        if range_vals[col] == 0:
            normalized_data[col] = 0
        else:
            normalized_data[col] = (numeric_data[col] - min_vals[col]) / (range_vals[col] + epsilon)

    ideal_positive = pd.Series(index=numeric_data.columns, dtype='float64')
    ideal_negative = pd.Series(index=numeric_data.columns, dtype='float64')
    for col in numeric_data.columns:
        if col in benefit_cols: 
            ideal_positive[col] = normalized_data[col].max() 
            ideal_negative[col] = normalized_data[col].min() 
        else: 
            ideal_positive[col] = normalized_data[col].min() 
            ideal_negative[col] = normalized_data[col].max() 
    
    # Pastikan 'weights' adalah Series pandas dengan indeks yang cocok dengan kolom 'numeric_data'
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=numeric_data.columns) # Coba konversi jika dict
    elif not weights.index.equals(numeric_data.columns):
        weights = weights.reindex(numeric_data.columns).fillna(0) # Sesuaikan urutan dan isi NaN dengan 0 jika perlu

    weighted_normalized = normalized_data.multiply(weights, axis='columns') 
    s_values = ((ideal_positive - weighted_normalized).abs()).sum(axis=1)
    r_values = ((ideal_positive - weighted_normalized).abs()).max(axis=1)
    s_star, s_minus = s_values.min(), s_values.max()
    r_star, r_minus = r_values.min(), r_values.max()
    s_diff = s_minus - s_star
    r_diff = r_minus - r_star
    if s_diff == 0 or r_diff == 0: 
        q_values = pd.Series([0.5] * len(numeric_data), index=numeric_data.index)
    else:
        q_values = 0.5 * ((s_values - s_star) / s_diff) + 0.5 * ((r_values - r_star) / r_diff)
    return q_values.sort_values()

# --- Rute Aplikasi Web ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': 
        temp_df_original = df.copy() 
        submit_type = request.form.get('submit_button') 
        title = "" 
        
        criteria = ['Price', 'Rating', 'Time_Minutes'] 
        benefit_criteria = ['Rating', 'Time_Minutes'] 

        # Hapus atau komentari bagian bobot manual
        # manual_weights_values = {
        #     'Price': 0.45,
        #     'Rating': 0.35,
        #     'Time_Minutes': 0.20
        # }
        # manual_weights = pd.Series(manual_weights_values)
        
        if submit_type == 'city_selection': 
            choice = request.form['city_choice'] 
            if choice == 'Semua':
                data_to_process = temp_df_original
                title = "🏆 Rekomendasi dari DESTINA (Semua Kota)"
            else:
                data_to_process = temp_df_original[temp_df_original['City'] == choice]
                title = f"🏆 Rekomendasi DESTINA untuk Kota {choice}"

            if data_to_process.empty or len(data_to_process) < 2:
                return render_template('index.html', cities=CITIES, error="Tidak cukup data untuk perbandingan di kota/pilihan ini (minimal 2 destinasi).")

            numerical_data = data_to_process[criteria].copy()
            for col in criteria:
                numerical_data[col] = pd.to_numeric(numerical_data[col], errors='coerce')
            numerical_data.dropna(subset=criteria, inplace=True)

            if len(numerical_data) < 2:
                return render_template('index.html', cities=CITIES, error="Tidak cukup data valid setelah pembersihan untuk perbandingan.")

            # --- KEMBALIKAN PENGGUNAAN CRITIC ---
            weights_for_selection = critic_weight(numerical_data)
            # weights_for_selection = manual_weights # Baris ini dikomentari/dihapus
            # --- AKHIR PENGEMBALIAN CRITIC ---
            
            vikor_rankings_for_selection = vikor_method(numerical_data, weights_for_selection, benefit_criteria)
            
            ranked_results = data_to_process.loc[vikor_rankings_for_selection.index].copy()
            
            ranked_results['VIKOR_Score'] = vikor_rankings_for_selection.values
            ranked_results['Rank'] = range(1, len(ranked_results) + 1)
            
            ranked_results['Price_Formatted'] = ranked_results['Price'].apply(lambda x: f"Rp {int(x):,.0f}".replace(',', '.'))
            ranked_results['VIKOR_Score_Formatted'] = ranked_results['VIKOR_Score'].apply(format_angka_tampilan)
            ranked_results['Rating'] = ranked_results['Rating'].astype(float)
            
            rating_full_list, rating_half_list, rating_empty_list = [], [], []
            for r_val in ranked_results['Rating']:
                full_stars = int(r_val); half_star = 1 if (r_val - full_stars) >= 0.25 and (r_val - full_stars) < 0.75 else 0
                if (r_val - full_stars) >= 0.75: full_stars +=1; half_star = 0
                rating_full_list.append(full_stars); rating_half_list.append(half_star); rating_empty_list.append(5 - full_stars - half_star)
            ranked_results['rating_full'] = rating_full_list
            ranked_results['rating_half'] = rating_half_list
            ranked_results['rating_empty'] = rating_empty_list

            weights_dict_for_selection = {k: format_angka_tampilan(v) for k, v in weights_for_selection.to_dict().items()}

            return render_template('results.html', 
                                   title=title, 
                                   ranked_results=ranked_results.to_dict('records'),
                                   weights=weights_dict_for_selection,
                                   is_new_data_submission=False)

        elif submit_type == 'new_data': 
            try:
                new_data_input = {
                    'Place_Name': request.form['new_place_name'],
                    'City': request.form['new_city'].title(),
                    'Price': int(request.form['new_price']),
                    'Rating': float(request.form['new_rating']),
                    'Time_Minutes': float(request.form['new_time'])
                }
            except (ValueError, KeyError) as e:
                return render_template('index.html', cities=CITIES, error=f"Data baru tidak valid atau tidak lengkap: {e}. Silakan coba lagi.")

            title = f"📊 Hasil Analisis untuk Destinasi Baru: {new_data_input['Place_Name']}"
            new_df_row = pd.DataFrame([new_data_input])
            df_for_overall_ranking = pd.concat([temp_df_original, new_df_row], ignore_index=True)
            
            if df_for_overall_ranking.empty or len(df_for_overall_ranking) < 1:
                 return render_template('index.html', cities=CITIES, error="Tidak ada data untuk diproses.")

            numerical_data_overall = df_for_overall_ranking[criteria].copy()
            for col in criteria:
                numerical_data_overall[col] = pd.to_numeric(numerical_data_overall[col], errors='coerce')
            numerical_data_overall.dropna(subset=criteria, inplace=True)

            if len(numerical_data_overall) < 1 :
                 return render_template('index.html', cities=CITIES, error="Data baru tidak valid setelah pembersihan.")

            # --- KEMBALIKAN PENGGUNAAN CRITIC ---
            weights_overall = critic_weight(numerical_data_overall)
            # weights_overall = manual_weights # Baris ini dikomentari/dihapus
            # --- AKHIR PENGEMBALIAN CRITIC ---
            
            vikor_rankings_overall = vikor_method(numerical_data_overall, weights_overall, benefit_criteria)
            
            ranked_results_overall = df_for_overall_ranking.loc[vikor_rankings_overall.index].copy()
            
            ranked_results_overall['VIKOR_Score_Overall'] = vikor_rankings_overall.values
            ranked_results_overall['Rank_Overall'] = range(1, len(ranked_results_overall) + 1)

            newly_added_data_ranked_series = ranked_results_overall[
                (ranked_results_overall['Place_Name'] == new_data_input['Place_Name']) &
                (ranked_results_overall['City'] == new_data_input['City']) &
                (ranked_results_overall['Price'] == new_data_input['Price'])
            ]
            if newly_added_data_ranked_series.empty:
                 return render_template('index.html', cities=CITIES, error="Data yang baru ditambahkan tidak ditemukan setelah pemeringkatan. Mungkin ada masalah dengan data input atau proses.")
            
            newly_added_data_ranked = newly_added_data_ranked_series.iloc[0]

            new_destination_details = {
                'Place_Name': newly_added_data_ranked['Place_Name'],
                'City': newly_added_data_ranked['City'],
                'Price_Formatted': f"Rp {int(newly_added_data_ranked['Price']):,.0f}".replace(',', '.'),
                'Rating_Original': new_data_input['Rating'],
                'Time_Minutes_Original': new_data_input['Time_Minutes'],
                'VIKOR_Score_Overall_Formatted': format_angka_tampilan(newly_added_data_ranked['VIKOR_Score_Overall']),
                'Rank_Overall': newly_added_data_ranked['Rank_Overall'],
                'Total_Destinations_Overall': len(ranked_results_overall) # Seharusnya len(ranked_results_overall)
            }
            
            r_val = new_data_input['Rating']
            full_stars = int(r_val); half_star = 1 if (r_val - full_stars) >= 0.25 and (r_val - full_stars) < 0.75 else 0
            if (r_val - full_stars) >= 0.75: full_stars +=1; half_star = 0
            new_destination_details['rating_full'] = full_stars
            new_destination_details['rating_half'] = half_star
            new_destination_details['rating_empty'] = 5 - full_stars - half_star
            
            weights_dict_overall = {k: format_angka_tampilan(v) for k, v in weights_overall.to_dict().items()}

            return render_template('results.html',
                                   title=title,
                                   is_new_data_submission=True,
                                   new_destination_details=new_destination_details,
                                   weights_for_overall_rank=weights_dict_overall)
        else:
            return render_template('index.html', cities=CITIES)

    return render_template('index.html', cities=CITIES)

if __name__ == '__main__':
    app.run(debug=True)
