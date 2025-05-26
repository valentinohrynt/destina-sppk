[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

---
## English <a name="english"></a>

# DESTINA - Decision Support for Tourism in Indonesia

DESTINA is a web-based decision support system designed to help users find the best tourist destinations in Indonesia. It utilizes the CRITIC method for objective criteria weighting and the VIKOR method for ranking alternatives, providing recommendations based on user preferences or by analyzing newly submitted destination data. The application features a visually appealing interface with glassmorphism effects and background music.

## Features

* **City-Based Recommendations**: Users can select a city or view recommendations from all available cities.
* **New Destination Analysis**: Users can submit details of a new tourist destination (name, city, price, rating, time) and get an instant analysis of its ranking compared to existing data.
* **Objective Criteria Weighting (CRITIC)**: The system uses the CRITIC (Criteria Importance Through Intercriteria Correlation) method to determine the objective weights of criteria such as Price, Rating, and Time (in minutes).
* **Multi-Criteria Decision Making (VIKOR)**: The VIKOR (VlseKriterijumska Optimizacija I Kompromisno Resenje) method is employed to rank tourist destinations based on the calculated weights and criteria values.
* **Dynamic Results Display**: Shows ranked results in a table, including formatted prices, star ratings, and VIKOR scores. For new data submissions, a focused summary of the new destination's analysis is provided.
* **User-Friendly Interface**: Modern design with glassmorphism, animated backgrounds, and icons.
* **Background Music Player**: Includes a simple music player with a playlist and mute functionality.
* **Scroll Buttons**: Scroll to top/end buttons for easier navigation on results page.
* **Responsive Design**: Adapts to different screen sizes.

## Core Technologies Used

* **Backend**: Python, Flask
* **Data Handling**: Pandas, NumPy
* **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Font Awesome
* **Deployment Configuration**: Vercel (as per `vercel.json`)

## File Structure

destina-sppk/
├── app.py                      # Main Flask application logic, CRITIC and VIKOR implementations
├── requirements.txt            # Python dependencies
├── tourism_with_id.csv         # Dataset for tourist destinations
├── vercel.json                 # Vercel deployment configuration
├── static/
│   ├── css/
│   │   └── style.css           # Custom CSS styles for the application
│   ├── js/
│   │   └── script.js           # Custom JavaScript for frontend interactivity
│   ├── images/
│   │   └── destina_logo.png    # Application logo
│   └── audio/
│       ├── sound_of_java_orchestra.ogg # Background music file
│       └── sabilulungan.ogg    # Background music file
└── templates/
├── base.html               # Base HTML template with navbar, footer, and common elements
├── index.html              # Homepage with forms for city selection and new data input
└── results.html            # Page to display recommendation results and new data analysis


## Setup and Installation

1.  **Prerequisites**:
    * Python 3.x installed.
    * pip (Python package installer).

2.  **Clone the Repository** (Example):
    ```bash
    git clone [https://github.com/valentinohrynt/destina-sppk.git](https://github.com/valentinohrynt/destina-sppk.git)
    cd destina-sppk
    ```

3.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    This will install Flask, Pandas, NumPy, and other necessary libraries.

5.  **Dataset**:
    Ensure the `tourism_with_id.csv` file is present in the root directory of the project. The application relies on this file for destination data.

## Running the Application

1.  Navigate to the project's root directory.
2.  Run the Flask application:
    ```bash
    flask run
    ```
    Or directly using Python:
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5000/`.

## How It Works

1.  **Data Loading and Preprocessing**:
    * The application loads tourism data from `tourism_with_id.csv` into a Pandas DataFrame.
    * Missing values in `Time_Minutes` are filled with the mean of the column.
    * A helper function `format_angka_tampilan` is used to format numerical outputs neatly.

2.  **CRITIC Method (Objective Weighting)**:
    * The `critic_weight` function takes the numerical data for selected criteria (`Price`, `Rating`, `Time_Minutes`).
    * It normalizes the data and calculates the standard deviation for each criterion.
    * A correlation matrix is computed to determine the conflict between criteria.
    * The weights are derived based on standard deviation and the sum of differences from the correlation matrix, indicating both contrast intensity and conflict.
    * Handles cases with insufficient data by returning equal weights.

3.  **VIKOR Method (Ranking)**:
    * The `vikor_method` function processes the numerical data, the calculated weights, and a list of benefit criteria (`Rating`, `Time_Minutes` are benefit, `Price` is cost).
    * Data is normalized.
    * Ideal positive (best) and ideal negative (worst) solutions are determined for each criterion.
    * $S_i$ (group utility) and $R_i$ (individual regret) values are calculated for each alternative.
    * $Q_i$ values are computed, which represent the compromise solution. Alternatives are ranked based on these $Q_i$ values (lower is better).

4.  **User Interface (Flask Routes)**:
    * **`GET /`**: Displays the main page (`index.html`) with options to select a city or input new destination data.
    * **`POST /`**: Handles form submissions.
        * If `city_selection`: Filters data by the chosen city (or uses all data), applies CRITIC and VIKOR, and displays ranked results on `results.html`.
        * If `new_data`: Takes user input for a new destination, adds it to the dataset, recalculates weights (CRITIC) and rankings (VIKOR) for the entire dataset including the new entry, and then displays a summary of the new destination's performance on `results.html`.
    * Error handling is included for scenarios like insufficient data.
    * Star ratings are dynamically generated for display.

## Deployment

The `vercel.json` file suggests that this application is configured for deployment on the Vercel platform. It specifies build configurations for the Python backend and static files.

## Customization

* **Criteria**: The core criteria (`Price`, `Rating`, `Time_Minutes`) and benefit/cost nature are defined in the `index` route in `app.py`. These can be modified if the dataset supports other or different quantifiable attributes.
* **Dataset**: The application uses `tourism_with_id.csv`. To use a different dataset, ensure it has similar relevant columns or modify the data loading and processing parts in `app.py` accordingly.
* **Styling**: Styles can be modified in `static/css/style.css`.
* **Frontend Behavior**: JavaScript functionalities can be adjusted in `static/js/script.js`.

---
## Bahasa Indonesia <a name="bahasa-indonesia"></a>

# DESTINA - Sistem Pendukung Keputusan Pariwisata di Indonesia

DESTINA adalah sistem pendukung keputusan berbasis web yang dirancang untuk membantu pengguna menemukan destinasi wisata terbaik di Indonesia. Aplikasi ini menggunakan metode CRITIC untuk pembobotan kriteria secara objektif dan metode VIKOR untuk perangkingan alternatif, sehingga dapat memberikan rekomendasi berdasarkan preferensi pengguna atau melalui analisis data destinasi yang baru dimasukkan. Aplikasi ini memiliki antarmuka yang menarik secara visual dengan efek *glassmorphism* dan musik latar.

## Fitur

* **Rekomendasi Berdasarkan Kota**: Pengguna dapat memilih kota tertentu atau melihat rekomendasi dari semua kota yang tersedia.
* **Analisis Destinasi Baru**: Pengguna dapat memasukkan detail destinasi wisata baru (nama, kota, harga, rating, waktu) dan mendapatkan analisis instan mengenai peringkatnya dibandingkan dengan data yang sudah ada.
* **Pembobotan Kriteria Objektif (CRITIC)**: Sistem menggunakan metode CRITIC (Criteria Importance Through Intercriteria Correlation) untuk menentukan bobot objektif dari kriteria seperti Harga, Rating, dan Waktu (dalam menit).
* **Pengambilan Keputusan Multi-Kriteria (VIKOR)**: Metode VIKOR (VlseKriterijumska Optimizacija I Kompromisno Resenje) digunakan untuk merangking destinasi wisata berdasarkan bobot yang telah dihitung dan nilai kriteria.
* **Tampilan Hasil Dinamis**: Menampilkan hasil peringkat dalam tabel, termasuk harga yang diformat, peringkat bintang, dan skor VIKOR. Untuk pengajuan data baru, ringkasan fokus analisis destinasi baru disediakan.
* **Antarmuka Pengguna yang Ramah**: Desain modern dengan *glassmorphism*, latar belakang animasi, dan ikon.
* **Pemutar Musik Latar**: Termasuk pemutar musik sederhana dengan daftar putar dan fungsionalitas senyap (mute).
* **Tombol Gulir (Scroll)**: Tombol gulir ke atas/bawah untuk navigasi yang lebih mudah di halaman hasil.
* **Desain Responsif**: Dapat menyesuaikan dengan berbagai ukuran layar.

## Teknologi Inti yang Digunakan

* **Backend**: Python, Flask
* **Penanganan Data**: Pandas, NumPy
* **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Font Awesome
* **Konfigurasi Deployment**: Vercel (sesuai `vercel.json`)

## Struktur File

destina-sppk/
├── app.py                      # Logika utama aplikasi Flask, implementasi CRITIC dan VIKOR
├── requirements.txt            # Dependensi Python
├── tourism_with_id.csv         # Dataset untuk destinasi wisata
├── vercel.json                 # Konfigurasi deployment Vercel
├── static/
│   ├── css/
│   │   └── style.css           # Gaya CSS kustom untuk aplikasi
│   ├── js/
│   │   └── script.js           # JavaScript kustom untuk interaktivitas frontend
│   ├── images/
│   │   └── destina_logo.png    # Logo aplikasi
│   └── audio/
│       ├── sound_of_java_orchestra.ogg # File musik latar
│       └── sabilulungan.ogg    # File musik latar
└── templates/
├── base.html               # Template HTML dasar dengan navbar, footer, dan elemen umum
├── index.html              # Halaman utama dengan formulir untuk pemilihan kota dan input data baru
└── results.html            # Halaman untuk menampilkan hasil rekomendasi dan analisis data baru


## Pengaturan dan Instalasi

1.  **Prasyarat**:
    * Python 3.x terinstal.
    * pip (penginstal paket Python).

2.  **Klon Repositori** (Contoh):
    ```bash
    git clone [https://github.com/valentinohrynt/destina-sppk.git](https://github.com/valentinohrynt/destina-sppk.git)
    cd destina-sppk
    ```

3.  **Buat Lingkungan Virtual** (Direkomendasikan):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Pada Windows: venv\Scripts\activate
    ```

4.  **Instal Dependensi**:
    ```bash
    pip install -r requirements.txt
    ```
    Ini akan menginstal Flask, Pandas, NumPy, dan pustaka lain yang diperlukan.

5.  **Dataset**:
    Pastikan file `tourism_with_id.csv` ada di direktori root proyek. Aplikasi bergantung pada file ini untuk data destinasi.

## Menjalankan Aplikasi

1.  Arahkan ke direktori root proyek.
2.  Jalankan aplikasi Flask:
    ```bash
    flask run
    ```
    Atau langsung menggunakan Python:
    ```bash
    python app.py
    ```
    Aplikasi biasanya akan tersedia di `http://127.0.0.1:5000/`.

## Cara Kerja

1.  **Pemuatan dan Pemrosesan Awal Data**:
    * Aplikasi memuat data pariwisata dari `tourism_with_id.csv` ke dalam DataFrame Pandas.
    * Nilai yang hilang pada kolom `Time_Minutes` diisi dengan rata-rata kolom tersebut.
    * Fungsi bantuan `format_angka_tampilan` digunakan untuk memformat output numerik agar rapi.

2.  **Metode CRITIC (Pembobotan Objektif)**:
    * Fungsi `critic_weight` mengambil data numerik untuk kriteria yang dipilih (`Price`, `Rating`, `Time_Minutes`).
    * Ini menormalisasi data dan menghitung deviasi standar untuk setiap kriteria.
    * Matriks korelasi dihitung untuk menentukan konflik antar kriteria.
    * Bobot diturunkan berdasarkan deviasi standar dan jumlah perbedaan dari matriks korelasi, yang menunjukkan intensitas kontras dan konflik.
    * Menangani kasus dengan data yang tidak mencukupi dengan mengembalikan bobot yang sama.

3.  **Metode VIKOR (Perangkingan)**:
    * Fungsi `vikor_method` memproses data numerik, bobot yang dihitung, dan daftar kriteria manfaat (`Rating`, `Time_Minutes` adalah manfaat, `Price` adalah biaya).
    * Data dinormalisasi.
    * Solusi ideal positif (terbaik) dan ideal negatif (terburuk) ditentukan untuk setiap kriteria.
    * Nilai $S_i$ (utilitas grup) dan $R_i$ (penyesalan individu) dihitung untuk setiap alternatif.
    * Nilai $Q_i$ dihitung, yang mewakili solusi kompromi. Alternatif diberi peringkat berdasarkan nilai $Q_i$ ini (lebih rendah lebih baik).

4.  **Antarmuka Pengguna (Rute Flask)**:
    * **`GET /`**: Menampilkan halaman utama (`index.html`) dengan opsi untuk memilih kota atau memasukkan data destinasi baru.
    * **`POST /`**: Menangani pengiriman formulir.
        * Jika `city_selection`: Menyaring data berdasarkan kota yang dipilih (atau menggunakan semua data), menerapkan CRITIC dan VIKOR, dan menampilkan hasil peringkat di `results.html`.
        * Jika `new_data`: Menerima input pengguna untuk destinasi baru, menambahkannya ke dataset, menghitung ulang bobot (CRITIC) dan peringkat (VIKOR) untuk seluruh dataset termasuk entri baru, dan kemudian menampilkan ringkasan kinerja destinasi baru di `results.html`.
    * Penanganan kesalahan disertakan untuk skenario seperti data yang tidak mencukupi.
    * Peringkat bintang dibuat secara dinamis untuk ditampilkan.

## Deployment

File `vercel.json` menunjukkan bahwa aplikasi ini dikonfigurasi untuk deployment di platform Vercel. Ini menentukan konfigurasi build untuk backend Python dan file statis.

## Kustomisasi

* **Kriteria**: Kriteria inti (`Price`, `Rating`, `Time_Minutes`) dan sifat manfaat/biayanya didefinisikan dalam rute `index` di `app.py`. Ini dapat dimodifikasi jika dataset mendukung atribut lain atau berbeda yang dapat dikuantifikasi.
* **Dataset**: Aplikasi menggunakan `tourism_with_id.csv`. Untuk menggunakan dataset yang berbeda, pastikan dataset tersebut memiliki kolom relevan yang serupa atau modifikasi bagian pemuatan dan pemrosesan data di `app.py` sesuai kebutuhan.
* **Gaya**: Gaya dapat dimodifikasi di `static/css/style.css`.
* **Perilaku Frontend**: Fungsionalitas JavaScript dapat disesuaikan di `static/js/script.js`.