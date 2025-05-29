def format_angka_tampilan(nilai, maks_desimal=4, presisi_untuk_angka_kecil=6):
    """
    Memformat angka untuk tampilan:
    - Jika bilangan bulat, tampilkan sebagai integer (misal: 1).
    - Jika desimal, tampilkan hingga maks_desimal, hapus nol di akhir (misal: 0.123).
    - Jika angka sangat kecil (misal: 0.00001) tidak akan ditampilkan sebagai "0" begitu saja,
      melainkan akan dicoba ditampilkan dengan presisi lebih tinggi.
    """
    if not isinstance(nilai, (int, float)):
        return str(nilai) 

    epsilon_untuk_nol = 1e-9
    
    if abs(nilai) < epsilon_untuk_nol:
        return "0" 

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