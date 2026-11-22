import io
from itertools import combinations
import matplotlib.pyplot as plt
import mplstereonet
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analisis Kinematik Joint Set - Stereonet _ By Ezar",
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
markers = ["o", "s", "^", "D", "v", "P", "*", "X", "<", ">"]

planes = []
for idx, row in valid_df.iterrows():
  name = str(row["Joint Set"]).strip() or f"Joint Set {len(planes) + 1}"
  dip = float(np.clip(row["Dip"], 0.0, 90.0))
  dip_dir = float(row["Dip Direction"]) % 360.0
  strike = (dip_dir - 90.0) % 360.0
  planes.append({
      "id": f"J{len(planes) + 1}",
      "name": name,
      "strike": strike,
      "dip": dip,
      "dip_dir": dip_dir,
      "color": palette[len(planes) % len(palette)],
  })

intersection_results = []
for pair_idx, (p1, p2) in enumerate(combinations(planes, 2)):
  plunge, bearing = mplstereonet.plane_intersection(
      p1["strike"], p1["dip"], p2["strike"], p2["dip"]
  )
  plunge_val = float(np.squeeze(plunge))
  trend_val = float(np.squeeze(bearing))

  if np.isnan(plunge_val) or np.isnan(trend_val):
    continue

  intersection_results.append({
      "pair_name": f"{p1['name']} ∩ {p2['name']}",
      "short": f"L({p1['id']}-{p2['id']})",
      "plunge": plunge_val,
      "trend": trend_val,
      "color": palette[(pair_idx + 3) % len(palette)],
      "marker": markers[pair_idx % len(markers)],
  })

# =====================================================================
# RENDER STEREONET
# =====================================================================
with col_plot:
  proj = (
      "equal_angle_stereonet"
      if "Wulff" in net_type
      else "equal_area_stereonet"
  )
  fig = plt.figure(figsize=(7.8, 7.8), dpi=150)
  ax = fig.add_subplot(111, projection=proj)

  ax.grid(True, color="gray", linestyle=":", linewidth=0.6, alpha=0.7)
  ax.set_azimuth_ticks(np.arange(0, 360, 10))
  ax.set_azimuth_ticklabels([
      f"{deg}°" if deg % 30 == 0 else "" for deg in np.arange(0, 360, 10)
  ])

  for p in planes:
    label_text = (
        f"{p['id']}: {p['name']} ({p['dip']:.0f}°/{int(p['dip_dir']):03d}° | RHR:"
        f" N{int(p['strike']):03d}°E/{p['dip']:.0f}°)"
    )
    ax.plane(
        p["strike"],
        p["dip"],
        color=p["color"],
        linewidth=2.2,
        label=label_text,
    )
    if show_poles:
      ax.pole(
          p["strike"],
          p["dip"],
          marker="x",
          markersize=7,
          color=p["color"],
          markeredgewidth=1.5,
      )

  for res in intersection_results:
    ax.line(
        res["plunge"],
        res["trend"],
        marker=res["marker"],
        markersize=8.5,
        markerfacecolor=res["color"],
        markeredgecolor="black",
        markeredgewidth=1.2,
        linestyle="None",
        label=(
            f"{res['short']} ({res['pair_name']}) -> {res['plunge']:.1f}° /"
            f" {res['trend']:.1f}°"
        ),
        zorder=5,
    )
    if show_labels:
      lon, lat = mplstereonet.line(res["plunge"], res["trend"])
      x_pos = float(np.squeeze(lon))
      y_pos = float(np.squeeze(lat))
      ax.annotate(
          f" {res['short']}\n ({res['plunge']:.0f}°/{res['trend']:.0f}°)",
          xy=(x_pos, y_pos),
          fontsize=8,
          fontweight="bold",
          xytext=(5, 4),
          textcoords="offset points",
      )

  ax.set_title(
      f"Stereonet Analisis Diskontinuitas ({net_type.split()[0]})\n"
      f"Total Bidang: {len(planes)} | Total Perpotongan: {len(intersection_results)}",
      pad=22,
      fontsize=11,
      fontweight="bold",
  )
  ax.legend(
      loc="upper center",
      bbox_to_anchor=(0.5, -0.06),
      ncol=1,
      frameon=True,
      facecolor="#f9f9f9",
      fontsize=8.2,
  )
  plt.tight_layout()
  st.pyplot(fig)

  buf = io.BytesIO()
  fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
  st.download_button(
      label="Download Gambar Stereonet (PNG)",
      data=buf.getvalue(),
      file_name="hasil_stereonet_joint.png",
      mime="image/png",
  )

# =====================================================================
# TABEL KONVERSI RHR & HASIL PERPOTONGAN
# =====================================================================
with col_data:
  if len(planes) > 0:
    st.subheader("2. Konversi Strike / Dip (Aturan Tangan Kanan)")
    df_rhr = pd.DataFrame([
        {
            "Kode": p["id"],
            "Nama": p["name"],
            "Dip / Dip Dir": f"{p['dip']:.0f}° / {int(p['dip_dir']):03d}°",
            "Strike / Dip (RHR)": f"N {int(p['strike']):03d}° E / {p['dip']:.0f}°",
        }
        for p in planes
    ])
    st.dataframe(df_rhr, use_container_width=True, hide_index=True)

  st.subheader("3. Orientasi Struktur Garis Hasil Perpotongan")
  if len(intersection_results) > 0:
    df_int = pd.DataFrame([
        {
            "Kode": r["short"],
            "Perpotongan Bidang": r["pair_name"],
            "Plunge (°)": f"{r['plunge']:.2f}° (≈ {round(r['plunge'])}°)",
            "Trend (°)": f"{r['trend']:.2f}° (≈ {round(r['trend']):03d}°)",
        }
        for r in intersection_results
    ])
    st.dataframe(df_int, use_container_width=True, hide_index=True)
  else:
    st.warning(
        "Minimal diperlukan 2 bidang yang tidak sejajar untuk menghitung"
        " perpotongan."
    )
