"""
차트 유틸리티 - Matplotlib 그래프를 CustomTkinter에 임베드
"""
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


# 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


def create_bar_chart(parent, data, title="", xlabel="", ylabel="", colors=None, bg_color="#FFFFFF", text_color="#333333", figsize=(6, 3.5)):
    """막대 차트 생성"""
    fig = Figure(figsize=figsize, dpi=100, facecolor=bg_color)
    ax = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    if not colors:
        cmap = plt.cm.get_cmap("Blues", len(values) + 2)
        colors = [cmap(i + 2) for i in range(len(values))]

    bars = ax.bar(labels, values, color=colors, edgecolor="none", width=0.6)
    ax.set_title(title, fontsize=12, fontweight="bold", color=text_color, pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color=text_color)
    ax.set_ylabel(ylabel, fontsize=9, color=text_color)
    ax.tick_params(colors=text_color, labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(text_color + "40")
    ax.spines["bottom"].set_color(text_color + "40")

    # 바 위에 값 표시
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.0f}" if isinstance(val, float) else str(val),
                ha="center", va="bottom", fontsize=8, color=text_color)

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget(), fig


def create_pie_chart(parent, data, title="", bg_color="#FFFFFF", text_color="#333333", figsize=(5, 3.5)):
    """파이 차트 생성"""
    fig = Figure(figsize=figsize, dpi=100, facecolor=bg_color)
    ax = fig.add_subplot(111)

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    colors_list = ["#4FC3F7", "#81C784", "#FFB74D", "#E57373", "#BA68C8",
                   "#4DD0E1", "#AED581", "#FFD54F", "#FF8A65", "#7986CB"]

    ax.pie(values, labels=labels, colors=colors_list[:len(values)],
           autopct="%1.0f%%", startangle=90, textprops={"fontsize": 9, "color": text_color})
    ax.set_title(title, fontsize=12, fontweight="bold", color=text_color, pad=10)

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget(), fig


def create_line_chart(parent, x_data, y_datasets, title="", xlabel="", ylabel="",
                      labels=None, bg_color="#FFFFFF", text_color="#333333", figsize=(6, 3.5)):
    """라인 차트 생성"""
    fig = Figure(figsize=figsize, dpi=100, facecolor=bg_color)
    ax = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    line_colors = ["#2196F3", "#E53935", "#43A047", "#FB8C00", "#8E24AA"]

    for i, y_data in enumerate(y_datasets):
        label = labels[i] if labels and i < len(labels) else f"데이터 {i + 1}"
        color = line_colors[i % len(line_colors)]
        ax.plot(x_data[:len(y_data)], y_data, marker="o", markersize=4,
                linewidth=2, color=color, label=label)

    ax.set_title(title, fontsize=12, fontweight="bold", color=text_color, pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color=text_color)
    ax.set_ylabel(ylabel, fontsize=9, color=text_color)
    ax.tick_params(colors=text_color, labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(text_color + "40")
    ax.spines["bottom"].set_color(text_color + "40")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2)

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget(), fig


def destroy_chart(widget, fig):
    """차트 정리"""
    if widget:
        widget.destroy()
    if fig:
        plt.close(fig)
