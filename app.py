import matplotlib.pyplot as plt
import mplstereonet
import numpy as np


def main():
  # =====================================================================
  # 1. DATA INPUT (Tanggal: 19, NIM: 080)
  # =====================================================================
  # Format: (Nama, Dip, Dip Direction)
  # Catatan: Joint Set 3 dikoreksi menjadi Dip = 5°, Dip Direction = 250°
  joint_sets = [
      ("Joint Set 1", 19.0, 30.0, "#1f77b4"),  # Biru
      ("Joint Set 2", 90.0, 80.0, "#d62728"),  # Merah
      ("Joint Set 3", 5.0, 250.0, "#2ca02c"),  # Hijau
  ]

  # Konversi Dip Direction ke Strike (Right-Hand Rule: Strike = (DipDir - 90) % 360)
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

  # =====================================================================
  # 2. INISIALISASI STEREONET (Equal-Angle / Wulff Net)
  # =====================================================================
  fig = plt.figure(figsize=(9, 8), dpi=120)
  ax = fig.add_subplot(111, projection="stereonet")

  # Mengatur tampilan grid stereonet menyerupai Wulff Net manual
  ax.grid(True, color="gray", linestyle=":", linewidth=0.6, alpha=0.7)
  ax.set_azimuth_ticks(np.arange(0, 360, 10))
  ax.set_azimuth_ticklabels([
      f"{deg}°" if deg % 30 == 0 else "" for deg in np.arange(0, 360, 10)
  ])

  # =====================================================================
  # 3. PLOTTING BIDANG (GREAT CIRCLES)
  # =====================================================================
  for p in planes:
    label_text = (
        f"{p['name']} (Dip/DD: {int(p['dip'])}°/{int(p['dip_dir']):03d}° | RHR:"
        f" N{int(p['strike']):03d}°E/{int(p['dip'])}°)"
    )
    ax.plane(
        p["strike"],
        p["dip"],
        color=p["color"],
        linewidth=2.2,
        label=label_text,
    )

  # =====================================================================
  # 4. PERHITUNGAN & PLOTTING PERPOTONGAN GARIS (LINEATIONS)
  # =====================================================================
  pairs = [
      (0, 1, "L1-2 (J1 ∩ J2)", "#9467bd", "o"),
      (0, 2, "L1-3 (J1 ∩ J3)", "#ff7f0e", "s"),
      (1, 2, "L2-3 (J2 ∩ J3)", "#17becf", "^"),
  ]

  print("=" * 65)
  print("HASIL PERHITUNGAN ORIENTASI PERPOTONGAN BIDANG (PLUNGE & TREND)")
  print("=" * 65)

  for idx1, idx2, label_int, marker_color, marker_style in pairs:
    p1 = planes[idx1]
    p2 = planes[idx2]

    # Menghitung perpotongan dua bidang menggunakan mplstereonet
    plunge, bearing = mplstereonet.plane_intersection(
        p1["strike"], p1["dip"], p2["strike"], p2["dip"]
    )
    plunge_val = float(plunge[0])
    trend_val = float(bearing[0])

    # Cetak hasil ke terminal VS Code
    print(f"{label_int:<16} -> Plunge: {plunge_val:05.2f}° | Trend: {trend_val:06.2f}°")

    # Plot titik perpotongan pada stereonet
    legend_label = (
        f"{label_int} -> Plunge: {plunge_val:.1f}°, Trend: {trend_val:.1f}°"
    )
    ax.line(
        plunge_val,
        trend_val,
        marker=marker_style,
        markersize=9,
        markerfacecolor=marker_color,
        markeredgecolor="black",
        markeredgewidth=1.2,
        linestyle="None",
        label=legend_label,
        zorder=5,
    )

    # Anotasi teks langsung pada plot
    ax.annotate(
        f" {label_int.split()[0]}\n ({plunge_val:.0f}°/{trend_val:.0f}°)",
        xy=mplstereonet.line(plunge_val, trend_val),
        fontsize=8.5,
        fontweight="bold",
        color="black",
        xytext=(5, 5),
        textcoords="offset points",
    )

  print("=" * 65)

  # =====================================================================
  # 5. FORMATTING JUDUL & LEGENDA
  # =====================================================================
  ax.set_title(
      "Analisis Kinematik Perpotongan Joint Set (Tugas 1)\n"
      "Input: Tanggal Lahir = 19 | NIM = 080 (Equal-Angle / Wulff Net)",
      pad=25,
      fontsize=12,
      fontweight="bold",
  )

  ax.legend(
      loc="upper center",
      bbox_to_anchor=(0.5, -0.06),
      ncol=1,
      frameon=True,
      facecolor="#f9f9f9",
      edgecolor="gray",
      fontsize=9,
  )

  plt.tight_layout()
  plt.show()


if __name__ == "__main__":
  main()