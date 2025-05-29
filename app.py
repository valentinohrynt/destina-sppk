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
    # dan simpan juga versi string untuk tampilan
    if 'Toilet_Availability' in df.columns:
        df['Toilet_Availability_Display'] = df['Toilet_Availability'].astype(str).str.lower() # Untuk tampilan 'yes'/'no'
        df['Toilet_Availability'] = df['Toilet_Availability'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    else:
        print("PERINGATAN: Kolom 'Toilet_Availability' tidak ditemukan.")
        df['Toilet_Availability'] = 0 # Default jika kolom tidak ada
        df['Toilet_Availability_Display'] = 'no'


    if 'Parking_Availability' in df.columns:
        df['Parking_Availability_Display'] = df['Parking_Availability'].astype(str).str.lower() # Untuk tampilan 'yes'/'no'
        df['Parking_Availability'] = df['Parking_Availability'].astype(str).str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    else:
        print("PERINGATAN: Kolom 'Parking_Availability' tidak ditemukan.")
        df['Parking_Availability'] = 0 # Default jika kolom tidak ada
        df['Parking_Availability_Display'] = 'no'

    if 'Accessibility_Score' in df.columns:
        df['Accessibility_Score'] = pd.to_numeric(df['Accessibility_Score'], errors='coerce')
        df['Accessibility_Score'] = df['Accessibility_Score'].fillna(df['Accessibility_Score'].mean())
    else:
        print("PERINGATAN: Kolom 'Accessibility_Score' tidak ditemukan.")
        df['Accessibility_Score'] = 5 # Default jika kolom tidak ada

    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(df['Price'].median()) # Median mungkin lebih baik untuk harga
    if 'Rating' in df.columns:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(df['Rating'].mean())
    
    if 'Time_Minutes' in df.columns:
         df['Time_Minutes'] = df['Time_Minutes'].fillna(df['Time_Minutes'].mean())


    CITIES = ['All'] + sorted(df['City'].unique().tolist())
except FileNotFoundError:
    print("Pastikan file 'tourism_data_updated.csv' ada di folder yang sama dengan app.py")
    df = pd.DataFrame()
    CITIES = ['All']


# --- Fungsi CRITIC dan VIKOR (Logika tetap sama) ---
def critic_weight(data):
    epsilon = 1e-9 
    numeric_data = data.apply(pd.to_numeric, errors='coerce') 
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
        if range_vals[col] == 0:
            normalized_data[col] = 0 
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
    
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=numeric_data.columns)
    elif not weights.index.equals(numeric_data.columns):
        weights = weights.reindex(numeric_data.columns).fillna(0)

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
        
        # --- Perubahan Kriteria: Menambahkan Toilet & Parkir ---
        criteria = ['Price', 'Rating', 'Accessibility_Score', 'Toilet_Availability', 'Parking_Availability'] 
        benefit_criteria = ['Rating', 'Accessibility_Score', 'Toilet_Availability', 'Parking_Availability'] 
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
                return render_template('index.html', cities=CITIES, error=f"The following criteria columns are missing: {', '.join(missing_criteria)}. Please check the CSV file and data loading.")

            numerical_data = data_to_process[criteria].copy() # Ini akan menggunakan kolom numerik (1/0) untuk Toilet & Parkir
            for col in criteria:
                numerical_data[col] = pd.to_numeric(numerical_data[col], errors='coerce')
            numerical_data.dropna(subset=criteria, inplace=True)

            if len(numerical_data) < 2:
                return render_template('index.html', cities=CITIES, error="Not enough valid data after cleaning for comparison.")

            weights_for_selection = critic_weight(numerical_data)
            vikor_rankings_for_selection = vikor_method(numerical_data, weights_for_selection, benefit_criteria)
            
            # Gabungkan kembali dengan data asli yang telah difilter dan dibersihkan
            ranked_results = data_to_process.loc[numerical_data.index].loc[vikor_rankings_for_selection.index].copy()
            
            ranked_results['VIKOR_Score'] = vikor_rankings_for_selection.values
            ranked_results['Rank'] = range(1, len(ranked_results) + 1)
            
            ranked_results['Price_Formatted'] = ranked_results['Price'].apply(lambda x: f"Rp {int(x):,.0f}".replace(',', '.'))
            ranked_results['VIKOR_Score_Formatted'] = ranked_results['VIKOR_Score'].apply(format_angka_tampilan)
            if 'Rating' in ranked_results.columns:
                 ranked_results['Rating_Display'] = ranked_results['Rating'].astype(float) # Untuk tampilan bintang
            if 'Accessibility_Score' in ranked_results.columns:
                 ranked_results['Accessibility_Score_Formatted'] = ranked_results['Accessibility_Score'].apply(lambda x: format_angka_tampilan(x, maks_desimal=1))
            
            # Untuk Toilet & Parking, kita akan menggunakan kolom *_Display yang berisi 'yes'/'no'
            # Jika tidak ada, default 'no'
            ranked_results['Toilet_Availability_For_Display'] = ranked_results.get('Toilet_Availability_Display', pd.Series(['no'] * len(ranked_results))).str.capitalize()
            ranked_results['Parking_Availability_For_Display'] = ranked_results.get('Parking_Availability_Display', pd.Series(['no'] * len(ranked_results))).str.capitalize()


            rating_full_list, rating_half_list, rating_empty_list = [], [], []
            if 'Rating_Display' in ranked_results.columns:
                for r_val in ranked_results['Rating_Display']:
                    full_stars = int(r_val); half_star = 1 if (r_val - full_stars) >= 0.25 and (r_val - full_stars) < 0.75 else 0
                    if (r_val - full_stars) >= 0.75: full_stars +=1; half_star = 0
                    rating_full_list.append(full_stars); rating_half_list.append(half_star); rating_empty_list.append(5 - full_stars - half_star)
                ranked_results['rating_full'] = rating_full_list
                ranked_results['rating_half'] = rating_half_list
                ranked_results['rating_empty'] = rating_empty_list
            else:
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
                    'Toilet_Availability': 1 if new_toilet_input_str == 'yes' else 0, # Konversi ke numerik
                    'Parking_Availability': 1 if new_parking_input_str == 'yes' else 0 # Konversi ke numerik
                }
                # Simpan juga versi string untuk ditampilkan di detail
                new_data_input_display_extras = {
                    'Toilet_Availability_Display': new_toilet_input_str.capitalize(),
                    'Parking_Availability_Display': new_parking_input_str.capitalize()
                }

            except (ValueError, KeyError) as e:
                return render_template('index.html', cities=CITIES, error=f"New data is invalid or incomplete: {e}. Ensure all fields are filled correctly. Please try again.")

            title = f"📊 Analysis Results for New Destination: {new_data_input['Place_Name']}"
            # Tambahkan kolom display 'yes'/'no' untuk data baru agar konsisten jika diperlukan concat nanti
            new_df_row_data = new_data_input.copy()
            new_df_row_data.update(new_data_input_display_extras)
            new_df_row = pd.DataFrame([new_df_row_data])
            
            df_for_overall_ranking = pd.concat([temp_df_original, new_df_row], ignore_index=True)
            
            if df_for_overall_ranking.empty or len(df_for_overall_ranking) < 1:
                return render_template('index.html', cities=CITIES, error="No data to process.")

            missing_criteria_overall = [c for c in criteria if c not in df_for_overall_ranking.columns]
            if missing_criteria_overall:
                 return render_template('index.html', cities=CITIES, error=f"The following criteria columns are missing for overall data: {', '.join(missing_criteria_overall)}.")

            numerical_data_overall = df_for_overall_ranking[criteria].copy()
            for col in criteria:
                numerical_data_overall[col] = pd.to_numeric(numerical_data_overall[col], errors='coerce')
            numerical_data_overall.dropna(subset=criteria, inplace=True)

            if len(numerical_data_overall) < 1 :
                return render_template('index.html', cities=CITIES, error="New data is invalid after cleaning.")

            weights_overall = critic_weight(numerical_data_overall)
            vikor_rankings_overall = vikor_method(numerical_data_overall, weights_overall, benefit_criteria)
            
            ranked_results_overall = df_for_overall_ranking.loc[numerical_data_overall.index].loc[vikor_rankings_overall.index].copy()
            
            ranked_results_overall['VIKOR_Score_Overall'] = vikor_rankings_overall.values
            ranked_results_overall['Rank_Overall'] = range(1, len(ranked_results_overall) + 1)

            # Mencari data baru yang ditambahkan
            # Perlu lebih hati-hati karena float bisa tidak presisi, Price (int) lebih aman
            newly_added_data_ranked_series = ranked_results_overall[
                (ranked_results_overall['Place_Name'] == new_data_input['Place_Name']) &
                (ranked_results_overall['City'] == new_data_input['City']) &
                (ranked_results_overall['Price'] == new_data_input['Price']) 
            ]
            # Ambil baris terakhir jika ada duplikat nama & kota & harga (meskipun kecil kemungkinannya dg data baru)
            if not newly_added_data_ranked_series.empty:
                newly_added_data_ranked = newly_added_data_ranked_series.iloc[-1] 
            else:
                return render_template('index.html', cities=CITIES, error="Newly added data not found after ranking. There might be an issue with input data or processing.")
            

            new_destination_details = {
                'Place_Name': newly_added_data_ranked['Place_Name'],
                'City': newly_added_data_ranked['City'],
                'Price_Formatted': f"Rp {int(newly_added_data_ranked['Price']):,.0f}".replace(',', '.'),
                'Rating_Original': new_data_input['Rating'],
                'Accessibility_Score_Original': new_data_input['Accessibility_Score'],
                'Toilet_Availability_Original': new_data_input_display_extras['Toilet_Availability_Display'], # Ambil dari string input
                'Parking_Availability_Original': new_data_input_display_extras['Parking_Availability_Display'], # Ambil dari string input
                'VIKOR_Score_Overall_Formatted': format_angka_tampilan(newly_added_data_ranked['VIKOR_Score_Overall']),
                'Rank_Overall': newly_added_data_ranked['Rank_Overall'],
                'Total_Destinations_Overall': len(ranked_results_overall)
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