from flask import Flask, render_template, request # type: ignore
import pandas as pd
import numpy as np
from helpers import format_angka_tampilan

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Memuat dan Membersihkan Data ---
try:
    df = pd.read_csv('tourism_data_updated.csv')
    print("File 'tourism_data_updated.csv' berhasil dimuat.")

    # Konversi 'yes'/'no' ke 1/0 untuk kolom fasilitas
    if 'Toilet_Availability' in df.columns:
        df['Toilet_Availability_Display'] = df['Toilet_Availability'].astype(str).str.lower()
        df['Toilet_Availability'] = df['Toilet_Availability'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    else:
        print("WARNING: Column 'Toilet_Availability' not found.")
        df['Toilet_Availability'] = 0
        df['Toilet_Availability_Display'] = 'no'

    if 'Parking_Availability' in df.columns:
        df['Parking_Availability_Display'] = df['Parking_Availability'].astype(str).str.lower()
        df['Parking_Availability'] = df['Parking_Availability'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    else:
        print("WARNING: Column 'Parking_Availability' not found.")
        df['Parking_Availability'] = 0
        df['Parking_Availability_Display'] = 'no'

    # Pastikan kolom numerik utama adalah numerik dan NaN diisi
    for col_name, default_val in [
        ('Accessibility_Score', 5), 
        ('Price', df['Price'].median() if 'Price' in df.columns and not df['Price'].empty else 0), 
        ('Rating', df['Rating'].mean() if 'Rating' in df.columns and not df['Rating'].empty else 3),
        ('Time_Minutes', df['Time_Minutes'].mean() if 'Time_Minutes' in df.columns and not df['Time_Minutes'].empty else 60) # Kembalikan Time_Minutes
    ]:
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            if df[col_name].isnull().any():
                fill_value = default_val if pd.isna(default_val) or not callable(default_val) else default_val() # Handle jika default adalah fungsi
                df[col_name] = df[col_name].fillna(fill_value)
        else:
            print(f"WARNING: Column '{col_name}' not found. Using default value: {default_val}")
            df[col_name] = default_val


    CITIES = ['All'] + sorted(df['City'].unique().tolist())
except FileNotFoundError:
    print("ERROR: File 'tourism_data_updated.csv' not found. Make sure it's in the same folder as app.py.")
    df = pd.DataFrame() # Buat DataFrame kosong agar aplikasi tidak crash total
    CITIES = ['All']
except Exception as e:
    print(f"An error occurred during data loading: {e}")
    df = pd.DataFrame()
    CITIES = ['All']


# --- Fungsi CRITIC dan VIKOR (Logika tetap sama) ---
def critic_weight(data):
    epsilon = 1e-9 
    numeric_data = data.apply(pd.to_numeric, errors='coerce').dropna() # Hapus baris dg NaN setelah konversi
    if len(numeric_data) <= 1:
        if not data.columns.empty:
            return pd.Series([1/len(data.columns)] * len(data.columns), index=data.columns)
        else:
            return pd.Series([])

    min_vals = numeric_data.min()
    max_vals = numeric_data.max()
    range_vals = max_vals - min_vals
    
    normalized_data = pd.DataFrame(index=numeric_data.index, columns=numeric_data.columns, dtype=float)

    for col in numeric_data.columns:
        if range_vals[col] == 0: # Semua nilai sama
            normalized_data[col] = 0.0 # Atau 0.5 jika diinginkan
        else:
            normalized_data[col] = (numeric_data[col] - min_vals[col]) / (range_vals[col] + epsilon)
    
    std_dev = normalized_data.std()
    
    corr_matrix = normalized_data.corr() 
    diff_corr = 1 - corr_matrix 
    c_j = std_dev * diff_corr.sum() 
    
    if c_j.sum() == 0:
        if not data.columns.empty:
            return pd.Series([1/len(data.columns)] * len(data.columns), index=data.columns)
        else:
            return pd.Series([])
            
    weights = c_j / c_j.sum() 
    return weights

def vikor_method(data, weights, benefit_cols): 
    epsilon = 1e-9 
    numeric_data = data.apply(pd.to_numeric, errors='coerce').dropna()
    
    if numeric_data.empty:
        return pd.Series([])

    min_vals = numeric_data.min()
    max_vals = numeric_data.max()
    range_vals = max_vals - min_vals
    normalized_data = pd.DataFrame(index=numeric_data.index, columns=numeric_data.columns, dtype=float)
    for col in numeric_data.columns:
        if range_vals[col] == 0:
            normalized_data[col] = 0.0
        else:
            normalized_data[col] = (numeric_data[col] - min_vals[col]) / (range_vals[col] + epsilon)

    ideal_positive = pd.Series(index=numeric_data.columns, dtype='float64')
    ideal_negative = pd.Series(index=numeric_data.columns, dtype='float64')
    for col in numeric_data.columns:
        if col in benefit_cols: 
            ideal_positive[col] = normalized_data[col].max() 
            ideal_negative[col] = normalized_data[col].min() 
        else: # Cost criteria
            ideal_positive[col] = normalized_data[col].min() 
            ideal_negative[col] = normalized_data[col].max() 
    
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=numeric_data.columns)
    elif not weights.index.equals(numeric_data.columns):
        weights = weights.reindex(numeric_data.columns).fillna(0)

    weighted_normalized = normalized_data.multiply(weights, axis='columns') 
    
    # Hitung S dan R untuk setiap alternatif
    # Menggunakan ideal_positive yang sudah benar (nilai terbaik, min untuk cost, max untuk benefit)
    # Rumus VIKOR: sum[ w_i * (f*_i - f_ij) / (f*_i - f^-_i) ] -- ini jika dinormalisasi dulu ke [0,1] dg f*_i jadi 1 dan f^-_i jadi 0
    # Atau lebih sederhana: w_i * |f*_i - f_ij|
    # Untuk S_values, kita ingin jarak dari ideal_positive (nilai terbaik)
    # Untuk R_values, kita ingin jarak maksimum dari ideal_positive
    
    # Jarak dari ideal_positive (nilai terbaik yang dinormalisasi)
    # Jika f*_i adalah nilai terbaik (max untuk benefit, min untuk cost pada data asli),
    # maka pada data ternormalisasi (0-1, dimana 1 adalah terbaik utk benefit, 0 terbaik utk cost setelah pembalikan jika perlu)
    # atau (nilai - min)/(max-min), dimana 1 adalah max, 0 adalah min.

    # ideal_positive Series berisi nilai terbaik (1 untuk benefit, 0 untuk cost setelah normalisasi tipe (max-x)/(max-min) atau (x-min)/(max-min) dan idealnya 0).
    # Sederhananya, kita hitung perbedaan ternormalisasi terbobot dari nilai ideal positif.
    # nilai f_ij adalah nilai pada weighted_normalized[col]
    # nilai f*_i adalah ideal_positive[col] yang sudah terbobot juga (atau bobot diterapkan pada perbedaan)
    
    # Perhitungan S dan R:
    # S_i = sum_j {w_j * (|f*_j - f_ij| / |f*_j - f^-_j|)}
    # R_i = max_j {w_j * (|f*_j - f_ij| / |f*_j - f^-_j|)}
    # Di sini, f*_j dan f^-_j adalah nilai ideal positif dan negatif dari kriteria j (setelah normalisasi)
    # f_ij adalah nilai kriteria j untuk alternatif i (setelah normalisasi)
    
    # Kita sudah menormalisasi data (0-1).
    # ideal_positive dan ideal_negative adalah nilai 0 atau 1 pada skala normalisasi.
    # Jadi |f*_j - f^-_j| adalah 1.
    
    s_values = pd.Series(0.0, index=numeric_data.index)
    r_values = pd.Series(0.0, index=numeric_data.index)

    for col in numeric_data.columns:
        term = weights[col] * ( (ideal_positive[col] - normalized_data[col]).abs() ) # Tidak perlu dibagi (ideal_positive[col] - ideal_negative[col]).abs() karena itu 1
        s_values += term
        r_values = np.maximum(r_values, term)

    s_star, s_minus = s_values.min(), s_values.max()
    r_star, r_minus = r_values.min(), r_values.max()
    
    s_diff = s_minus - s_star
    r_diff = r_minus - r_star
    
    # Handle pembagian dengan nol
    q_s_component = ((s_values - s_star) / (s_diff + epsilon))
    q_r_component = ((r_values - r_star) / (r_diff + epsilon))
    
    v = 0.5 # Bobot untuk strategi mayoritas, bisa disesuaikan
    q_values = v * q_s_component + (1 - v) * q_r_component
    
    return q_values.sort_values()


# --- Rute Aplikasi Web ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if df.empty and request.method == 'POST': # Jika df kosong dan ada POST, berarti CSV gagal load
         return render_template('index.html', cities=CITIES, error="Dataset could not be loaded. Please check the server console for errors regarding 'tourism_data_updated.csv'.")

    if request.method == 'POST': 
        temp_df_original = df.copy() 
        submit_type = request.form.get('submit_button') 
        title = "" 
        
        # --- Kriteria dikembalikan dengan Time_Minutes ---
        criteria = ['Price', 'Rating', 'Accessibility_Score', 'Toilet_Availability', 'Parking_Availability', 'Time_Minutes'] 
        benefit_criteria = ['Rating', 'Accessibility_Score', 'Toilet_Availability', 'Parking_Availability'] 
        # Time_Minutes adalah cost criterion, jadi tidak masuk benefit_criteria
        # --- Akhir Perubahan Kriteria ---
        
        if submit_type == 'city_selection': 
            choice = request.form['city_choice'] 
            if choice == 'All':
                data_to_process = temp_df_original
                title = "🏆 DESTINA Recommendations (All Cities)"
            else:
                data_to_process = temp_df_original[temp_df_original['City'] == choice]
                title = f"🏆 DESTINA Recommendations for {choice} City"

            if data_to_process.empty or len(data_to_process) < 2:
                return render_template('index.html', cities=CITIES, error="Not enough data for comparison in this city/selection (minimum 2 destinations).")

            missing_criteria = [c for c in criteria if c not in data_to_process.columns]
            if missing_criteria:
                return render_template('index.html', cities=CITIES, error=f"The following criteria columns are missing: {', '.join(missing_criteria)}. Please check the CSV file and data loading section in app.py.")

            numerical_data = data_to_process[criteria].copy()
            for col in criteria: # Pastikan konversi numerik
                numerical_data[col] = pd.to_numeric(numerical_data[col], errors='coerce')
            numerical_data.dropna(subset=criteria, inplace=True) # Hapus baris jika ada NaN di kriteria PENTING

            if len(numerical_data) < 2: # Cek lagi setelah dropna
                return render_template('index.html', cities=CITIES, error="Not enough valid data after cleaning (due to missing values in criteria columns) for comparison.")

            weights_for_selection = critic_weight(numerical_data)
            vikor_rankings_for_selection = vikor_method(numerical_data, weights_for_selection, benefit_criteria)
            
            if vikor_rankings_for_selection.empty:
                 return render_template('index.html', cities=CITIES, error="Could not compute VIKOR rankings, possibly due to insufficient distinct data after processing.")

            ranked_results = data_to_process.loc[numerical_data.index].loc[vikor_rankings_for_selection.index].copy()
            
            ranked_results['VIKOR_Score'] = vikor_rankings_for_selection.values
            ranked_results['Rank'] = range(1, len(ranked_results) + 1)
            
            ranked_results['Price_Formatted'] = ranked_results['Price'].apply(lambda x: f"Rp {int(x):,.0f}".replace(',', '.'))
            ranked_results['VIKOR_Score_Formatted'] = ranked_results['VIKOR_Score'].apply(format_angka_tampilan)
            
            if 'Rating' in ranked_results.columns:
                 ranked_results['Rating_Display'] = ranked_results['Rating'].astype(float)
            if 'Accessibility_Score' in ranked_results.columns:
                 ranked_results['Accessibility_Score_Formatted'] = ranked_results['Accessibility_Score'].apply(lambda x: format_angka_tampilan(x, maks_desimal=1))
            if 'Time_Minutes' in ranked_results.columns: # Tambahkan format untuk Time_Minutes
                 ranked_results['Time_Minutes_Formatted'] = ranked_results['Time_Minutes'].apply(lambda x: f"{format_angka_tampilan(x, maks_desimal=0)} min")


            ranked_results['Toilet_Availability_For_Display'] = ranked_results.get('Toilet_Availability_Display', pd.Series(['N/A'] * len(ranked_results))).str.capitalize()
            ranked_results['Parking_Availability_For_Display'] = ranked_results.get('Parking_Availability_Display', pd.Series(['N/A'] * len(ranked_results))).str.capitalize()

            rating_full_list, rating_half_list, rating_empty_list = [], [], []
            if 'Rating_Display' in ranked_results.columns:
                for r_val in ranked_results['Rating_Display']:
                    r_val_float = float(r_val) # Pastikan float
                    full_stars = int(r_val_float)
                    half_star = 0
                    if (r_val_float - full_stars) >= 0.75:
                        full_stars +=1
                    elif (r_val_float - full_stars) >= 0.25:
                        half_star = 1
                    rating_full_list.append(full_stars)
                    rating_half_list.append(half_star)
                    rating_empty_list.append(5 - full_stars - half_star)
                ranked_results['rating_full'] = rating_full_list
                ranked_results['rating_half'] = rating_half_list
                ranked_results['rating_empty'] = rating_empty_list
            else:
                # Fallback jika Rating_Display tidak ada
                ranked_results['rating_full'] = [0] * len(ranked_results)
                ranked_results['rating_half'] = [0] * len(ranked_results)
                ranked_results['rating_empty'] = [5] * len(ranked_results)


            weights_dict_for_selection = {k: format_angka_tampilan(v) for k, v in weights_for_selection.to_dict().items()}

            return render_template('results.html', 
                                   title=title, 
                                   ranked_results=ranked_results.to_dict('records'),
                                   weights=weights_dict_for_selection,
                                   is_new_data_submission=False)

        elif submit_type == 'new_data': 
            try:
                new_toilet_input_str = request.form.get('new_toilet_availability', 'no').lower()
                new_parking_input_str = request.form.get('new_parking_availability', 'no').lower()
                
                new_data_input = {
                    'Place_Name': request.form['new_place_name'],
                    'City': request.form['new_city'].title(),
                    'Price': int(request.form['new_price']),
                    'Rating': float(request.form['new_rating']),
                    'Accessibility_Score': float(request.form['new_accessibility_score']),
                    'Time_Minutes': float(request.form.get('new_time_minutes', 60)), # Ambil Time_Minutes
                    'Toilet_Availability': 1 if new_toilet_input_str == 'yes' else 0,
                    'Parking_Availability': 1 if new_parking_input_str == 'yes' else 0,
                }
                new_data_input_display_extras = { # Untuk tampilan string di detail
                    'Toilet_Availability_Display': new_toilet_input_str.capitalize(),
                    'Parking_Availability_Display': new_parking_input_str.capitalize()
                }

            except (ValueError, KeyError) as e:
                return render_template('index.html', cities=CITIES, error=f"New data is invalid or incomplete: {e}. Ensure all fields are filled correctly. Please try again.")

            title = f"📊 Analysis Results for New Destination: {new_data_input['Place_Name']}"
            
            new_df_row_data = new_data_input.copy()
            new_df_row_data.update(new_data_input_display_extras) # Tambahkan versi display
            new_df_row = pd.DataFrame([new_df_row_data])
            
            df_for_overall_ranking = pd.concat([temp_df_original, new_df_row], ignore_index=True)
            
            if df_for_overall_ranking.empty or len(df_for_overall_ranking) < 1: # Seharusnya < 2 untuk perbandingan
                return render_template('index.html', cities=CITIES, error="No data to process for ranking (need at least 2 for CRITIC).")

            missing_criteria_overall = [c for c in criteria if c not in df_for_overall_ranking.columns]
            if missing_criteria_overall:
                 return render_template('index.html', cities=CITIES, error=f"The following criteria columns are missing for overall data: {', '.join(missing_criteria_overall)}.")

            numerical_data_overall = df_for_overall_ranking[criteria].copy()
            for col in criteria:
                numerical_data_overall[col] = pd.to_numeric(numerical_data_overall[col], errors='coerce')
            numerical_data_overall.dropna(subset=criteria, inplace=True)

            if len(numerical_data_overall) < 2 : # CRITIC butuh minimal 2 baris data yang valid
                return render_template('index.html', cities=CITIES, error="Not enough valid distinct data after cleaning for overall comparison (CRITIC needs min 2).")

            weights_overall = critic_weight(numerical_data_overall)
            vikor_rankings_overall = vikor_method(numerical_data_overall, weights_overall, benefit_criteria)

            if vikor_rankings_overall.empty:
                 return render_template('index.html', cities=CITIES, error="Could not compute VIKOR rankings for new data, possibly due to insufficient distinct data after processing.")
            
            ranked_results_overall = df_for_overall_ranking.loc[numerical_data_overall.index].loc[vikor_rankings_overall.index].copy()
            
            ranked_results_overall['VIKOR_Score_Overall'] = vikor_rankings_overall.values
            ranked_results_overall['Rank_Overall'] = range(1, len(ranked_results_overall) + 1)

            # Mencari data baru yang ditambahkan
            newly_added_data_ranked_series = ranked_results_overall[
                (ranked_results_overall['Place_Name'] == new_data_input['Place_Name']) &
                (ranked_results_overall['City'] == new_data_input['City']) &
                (ranked_results_overall['Price'] == new_data_input['Price']) &
                (abs(ranked_results_overall['Rating'] - new_data_input['Rating']) < 0.01) & # Perbandingan float
                (abs(ranked_results_overall['Accessibility_Score'] - new_data_input['Accessibility_Score']) < 0.01) &
                (abs(ranked_results_overall['Time_Minutes'] - new_data_input['Time_Minutes']) < 0.01)
            ]

            if newly_added_data_ranked_series.empty:
                return render_template('index.html', cities=CITIES, error="Newly added data not found after ranking. There might be an issue with input data matching or processing.")
            
            newly_added_data_ranked = newly_added_data_ranked_series.iloc[0]

            new_destination_details = {
                'Place_Name': newly_added_data_ranked['Place_Name'],
                'City': newly_added_data_ranked['City'],
                'Price_Formatted': f"Rp {int(newly_added_data_ranked['Price']):,.0f}".replace(',', '.'),
                'Rating_Original': new_data_input['Rating'],
                'Accessibility_Score_Original': new_data_input['Accessibility_Score'],
                'Time_Minutes_Original': new_data_input['Time_Minutes'], # Tambahkan ini
                'Toilet_Availability_Original': new_data_input_display_extras['Toilet_Availability_Display'],
                'Parking_Availability_Original': new_data_input_display_extras['Parking_Availability_Display'],
                'VIKOR_Score_Overall_Formatted': format_angka_tampilan(newly_added_data_ranked['VIKOR_Score_Overall']),
                'Rank_Overall': newly_added_data_ranked['Rank_Overall'],
                'Total_Destinations_Overall': len(ranked_results_overall)
            }
            
            r_val = float(new_data_input['Rating'])
            full_stars = int(r_val)
            half_star = 0
            if (r_val - full_stars) >= 0.75:
                full_stars +=1
            elif (r_val - full_stars) >= 0.25:
                half_star = 1
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