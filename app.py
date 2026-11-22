import io
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
    "Aplikasi interaktif untuk memplot kedudukan diskontinuitas (*great circle*)"
    " serta menghitung orientasi (**Plunge** & **Trend**) hasil perpotongan"
    " bidang."
)

# =====================================================================
# SIDEBAR: INPUT PARAMETER TUGAS
# =====================================================================
st.sidebar.header("Parameter Input Mahasiswa")
tgl_lahir = st.sidebar.number_input(
    "Dua Angka Tanggal Lahir (Dip Joint Set 1)",
    min_value=1,
    max_value=31,
    value=19,
    step=1,
)
nim_3digit = st.sidebar.number_input(
    "Tiga Angka Belakang NIM (Dip Direction Joint Set 2)",
    min_value=0,
    max_value=360,
    value=80,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Pengaturan Lanjutan Joint Set")

with st.sidebar.expander("Ubah Nilai Manual Tiap Joint Set", expanded=False):
  j1_dip = st.number_input("J1 - Dip (°)", 0.0, 90.0, float(tgl_lahir), 1.0)
  j1_dd = st.number_input("J1 - Dip Direction (°)", 0.0, 360.0, 30.0, 1.0)

  j2_dip = st.number_input("J2 - Dip (°)", 0.0, 90.0, 90.0, 1.0)
  j2_dd = st.number_input(
      "J2 - Dip Direction (°)", 0.0, 360.0, float(nim_3digit), 1.0
  )

  j3_dip = st.number_input("J3 - Dip (°)", 0.0, 90.0, 5.0, 1.0)
  j3_dd = st.number_input("J3 - Dip Direction (°)", 0.0, 360.0, 250.0, 1.0)

net_type = st.sidebar.radio(
    "Jenis Jaring Stereonet",
    options=[
        "Equal-Angle (Wulff Net)",
        "Equal-Area (Schmidt Net)",
    ],
    index=0,
)

# =====================================================================
# PERHITUNGAN STRIKE/DIP & INTERSECTION
# =====================================================================
joint_sets = [
    ("Joint Set 1", j1_dip, j1_dd, "#1f77b4"),
    ("Joint Set 2", j2_dip, j2_dd, "#d62728"),
    ("Joint Set 3", j3_dip, j3_dd, "#2ca02c"),
]

planes = []
for name, dip, dip_dir, color in joint_sets:
  strike = (dip_dir - 90.0) % 360.0
  planes.append({
      "name": name,
      "strike": strike,
      "dip": dip,
      "dip_dir": dip_dir,
      "color": color,
  })

pairs = [
    (0, 1, "L1-2 (J1 ∩ J2)", "#9467bd", "o"),
    (0, 2, "L1-3 (J1 ∩ J3)", "#ff7f0e", "s"),
    (1, 2, "L2-3 (J2 ∩ J3)", "#17becf", "^"),
]

intersection_results = []
for idx1, idx2, label_int, marker_color, marker_style in pairs:
  p1, p2 = planes[idx1], planes[idx2]
  plunge, bearing = mplstereonet.plane_intersection(
      p1["strike"], p1["dip"], p2["strike"], p2["dip"]
  )
  intersection_results.append({
      "label": label_int,
      "short": label_int.split()[0],
      "plunge": float(np.squeeze(plunge)),
      "trend": float(np.squeeze(bearing)),
      "color": marker_color,
      "marker": marker_style,
  })

# =====================================================================
# TAMPILAN UTAMA (2 KOLOM: PLOT STEREONET & TABEL DATA)
# =====================================================================
col_plot, col_data = st.columns([1.3, 1])

with col_plot:
  proj = (
      "equal_angle_stereonet"
      if "Wulff" in net_type
      else "equal_area_stereonet"
  )
  fig = plt.figure(figsize=(7.5, 7.5), dpi=150)
  ax = fig.add_subplot(111, projection=proj)

  ax.grid(True, color="gray", linestyle=":", linewidth=0.6, alpha=0.7)
  ax.set_azimuth_ticks(np.arange(0, 360, 10))
  ax.set_azimuth_ticklabels([
      f"{deg}°" if deg % 30 == 0 else "" for deg in np.arange(0, 360, 10)
  ])

  for p in planes:
    label_text = (
        f"{p['name']} ({int(p['dip'])}°/{int(p['dip_dir']):03d}° | RHR:"
        f" N{int(p['strike']):03d}°E/{int(p['dip'])}°)"
    )
    ax.plane(
        p["strike"],
        p["dip"],
        color=p["color"],
        linewidth=2.2,
        label=label_text,
    )

  for res in intersection_results:
    ax.line(
        res["plunge"],
        res["trend"],
        marker=res["marker"],
        markersize=9,
        markerfacecolor=res["color"],
        markeredgecolor="black",
        markeredgewidth=1.2,
        linestyle="None",
        label=(
            f"{res['label']} -> Plunge: {res['plunge']:.1f}°, Trend:"
            f" {res['trend']:.1f}°"
        ),
        zorder=5,
    )
    # Ekstrak koordinat x, y menjadi float tunggal agar kompatibel dengan NumPy terbaru
    lon, lat = mplstereonet.line(res["plunge"], res["trend"])
    x_pos = float(np.squeeze(lon))
    y_pos = float(np.squeeze(lat))

    ax.annotate(
        f" {res['short']}\n ({res['plunge']:.0f}°/{res['trend']:.0f}°)",
        xy=(x_pos, y_pos),
        fontsize=8.5,
        fontweight="bold",
        xytext=(6, 5),
        textcoords="offset points",
    )

  ax.set_title(
      f"Stereonet Perpotongan Joint Set ({net_type.split()[0]})\n"
      f"Dip J1 = {int(j1_dip)}° | Dip Direction J2 = {int(j2_dd):03d}°",
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
      fontsize=8.5,
  )
  plt.tight_layout()

  st.pyplot(fig)

  buf = io.BytesIO()
  fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
  st.download_button(
      label="Download Gambar Stereonet (PNG)",
      data=buf.getvalue(),
      file_name=f"stereonet_tgl{int(j1_dip)}_nim{int(j2_dd):03d}.png",
      mime="image/png",
  )

with col_data:
  st.subheader("1. Data Orientasi Bidang (Joint Set)")
  df_planes = pd.DataFrame([
      {
          "Joint Set": p["name"],
          "Dip (°)": f"{p['dip']:.0f}°",
          "Dip Direction (°)": f"{int(p['dip_dir']):03d}°",
          "Strike / Dip (RHR)": f"N {int(p['strike']):03d}° E / {p['dip']:.0f}°",
      }
      for p in planes
  ])
  st.dataframe(df_planes, use_container_width=True, hide_index=True)

  st.subheader("2. Hasil Perpotongan Bidang (Lineation)")
  df_int = pd.DataFrame([
      {
          "Perpotongan": r["label"],
          "Plunge (°)": f"{r['plunge']:.2f}° (≈ {round(r['plunge'])}°)",
          "Trend (°)": f"{r['trend']:.2f}° (≈ {round(r['trend']):03d}°)",
      }
      for r in intersection_results
  ])
  st.dataframe(df_int, use_container_width=True, hide_index=True)

  st.info(
      "**Catatan:** Pada Joint Set 3, nilai soal (250 / 5) disesuaikan menjadi"
      " **Dip = 05°** dan **Dip Direction = 250°** karena kemiringan bidang"
      " (*dip*) maksimal adalah 90°."
  )
