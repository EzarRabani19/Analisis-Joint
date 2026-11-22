import io
from itertools import combinations
import matplotlib.pyplot as plt
import mplstereonet
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analisis Kinematik Joint Set - Stereonet",
    layout="wide",
)

st.title("Analisis Kinematik Perpotongan Joint Set (Stereonet)")
st.markdown(
    "Edit langsung nilai **Dip** dan **Dip Direction** pada tabel, atau"
    " gunakan tombol di bawah tabel untuk menambah dan menghapus *joint set*."
)

# =====================================================================
# INISIALISASI DATA AWAL
# =====================================================================
if "joint_table" not in st.session_state:
  st.session_state["joint_table"] = pd.DataFrame([
      {"Joint Set": "Joint Set 1", "Dip": 19.0, "Dip Direction": 30.0},
      {"Joint Set": "Joint Set 2", "Dip": 90.0, "Dip Direction": 80.0},
      {"Joint Set": "Joint Set 3", "Dip": 5.0, "Dip Direction": 250.0},
  ])

# =====================================================================
# SIDEBAR: PRESET & PENGATURAN JARING
# =====================================================================
st.sidebar.header("Pengaturan Tampilan & Preset")

net_type = st.sidebar.radio(
    "Jenis Jaring Stereonet",
    options=[
        "Equal-Angle (Wulff Net)",
        "Equal-Area (Schmidt Net)",
    ],
    index=0,
)

show_labels = st.sidebar.checkbox(
    "Tampilkan label angka pada titik potong", value=True
)
show_poles = st.sidebar.checkbox("Tampilkan kutub bidang (Poles)", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("Isi Cepat Parameter Tugas")
tgl_lahir = st.sidebar.number_input("Tanggal Lahir (Dip J1)", 1, 31, 19, 1)
nim_3digit = st.sidebar.number_input(
    "3 Digit Akhir NIM (Dip Dir J2)", 0, 360, 80, 1
)

if st.sidebar.button("Reset ke Data Tugas Default", use_container_width=True):
  st.session_state["joint_table"] = pd.DataFrame([
      {
          "Joint Set": "Joint Set 1",
          "Dip": float(tgl_lahir),
          "Dip Direction": 30.0,
      },
      {
          "Joint Set": "Joint Set 2",
          "Dip": 90.0,
          "Dip Direction": float(nim_3digit),
      },
      {"Joint Set": "Joint Set 3", "Dip": 5.0, "Dip Direction": 250.0},
  ])
  st.rerun()

# =====================================================================
# LAYOUT UTAMA: KOLOM KIRI (PLOT) & KOLOM KANAN (EDITOR TABEL & HASIL)
# =====================================================================
col_plot, col_data = st.columns([1.25, 1.05])

with col_data:
  st.subheader("1. Input & Edit Data Joint Set")

  # Tabel Editor (hide_index=False agar checkbox hapus baris di kiri muncul)
  edited_df = st.data_editor(
      st.session_state["joint_table"],
      num_rows="dynamic",
      use_container_width=True,
      hide_index=False,
      key="editor_joint",
      column_config={
          "Joint Set": st.column_config.TextColumn(
              "Nama Joint Set",
              default="Joint Set Baru",
              required=True,
          ),
          "Dip": st.column_config.NumberColumn(
              "Dip (°)",
              min_value=0.0,
              max_value=90.0,
              step=1.0,
              format="%.1f°",
              default=45.0,
              required=True,
          ),
          "Dip Direction": st.column_config.NumberColumn(
              "Dip Direction (°)",
              min_value=0.0,
              max_value=360.0,
              step=1.0,
              format="%.1f°",
              default=120.0,
              required=True,
          ),
      },
  )

  # Simpan perubahan tabel ke session_state secara otomatis
  if not edited_df.equals(st.session_state["joint_table"]):
    st.session_state["joint_table"] = edited_df.reset_index(drop=True)
    st.rerun()

  # Tombol Praktis Tambah & Hapus Joint
  btn_col1, btn_col2 = st.columns(2)
  with btn_col1:
    if st.button("+ Tambah Joint Set", use_container_width=True):
      next_num = len(st.session_state["joint_table"]) + 1
      new_row = pd.DataFrame([{
          "Joint Set": f"Joint Set {next_num}",
          "Dip": 45.0,
          "Dip Direction": 120.0,
      }])
      st.session_state["joint_table"] = pd.concat(
          [st.session_state["joint_table"], new_row], ignore_index=True
      )
      st.rerun()

  with btn_col2:
    if st.button(
        "Hapus Joint Terakhir",
        use_container_width=True,
        disabled=len(st.session_state["joint_table"]) == 0,
    ):
      st.session_state["joint_table"] = (
          st.session_state["joint_table"].iloc[:-1].reset_index(drop=True)
      )
      st.rerun()

  # Opsi Hapus Joint Tertentu (Pilih nama joint yang mau dihapus)
  if len(st.session_state["joint_table"]) > 0:
    with st.expander("Hapus Joint Tertentu", expanded=False):
      opsi_hapus = [
          f"{i}: {row['Joint Set']} ({row['Dip']}°/{row['Dip Direction']}°)"
          for i, row in st.session_state["joint_table"].iterrows()
      ]
      pilihan = st.selectbox("Pilih baris yang ingin dihapus:", opsi_hapus)
      if st.button("Hapus Baris Terpilih", type="primary"):
        idx_hapus = int(pilihan.split(":")[0])
        st.session_state["joint_table"] = (
            st.session_state["joint_table"]
            .drop(index=idx_hapus)
            .reset_index(drop=True)
        )
        st.rerun()

# =====================================================================
# PROSES VALIDASI & PERHITUNGAN STRIKE / DIP / INTERSECTION
# =====================================================================
valid_df = st.session_state["joint_table"].dropna(
    subset=["Dip", "Dip Direction"]
).copy()

palette = [
    "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
    "#17becf", "#e377c2", "#8c564b", "#bcbd22", "#393b79",
]
markers = ["o", "s", "^", "D", "v", "
