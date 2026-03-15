# # workers/ui/utils_scan_view.py
# #
# # This file (utils_scan_view.py) provides utility functions to interact with and update the single plot in the Scan View display tab.
# #
# # Author: Anthony Peter Kuzub
# # Blog: www.Like.audio (Contributor to this project)
# #
# # Version 20251213.120000.44
# 
# import inspect
# import os
# import traceback
# import numpy as np
# from matplotlib.offsetbox import AnchoredText
# 
# from workers.logger.logger import initialize_logging, set_log_directory
# from loguru import logger
# 
# LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
# 
# # --- Protocol 4.4: Context Logging Keys ---
# current_version = "20251213.120000.44"
# 
# def _find_and_plot_peaks(ax, data, start_freq_MHz, end_freq_MHz):
#     """Finds and plots local peaks on a Matplotlib axis."""
#     if LOCAL_DEBUG: logger.debug(f"▶️ _find_and_plot_peaks with {len(data) if data else 0} data points.")
# 
#     try:
#         if not data:
#             if LOCAL_DEBUG: logger.success("✅ No data to search for peaks.")
#             return
# 
#         x_data = np.array(data)[:, 0]
#         y_data = np.array(data)[:, 1]
# 
#         total_span = end_freq_MHz - start_freq_MHz
#         segment_width = total_span / 150
#         peaks = []
#         i = 0
#         while i < len(x_data):
#             segment_end_freq = x_data[i] + segment_width
#             segment_indices = np.where(
#                 (x_data >= x_data[i]) & (x_data <= segment_end_freq)
#             )
#             if not segment_indices[0].any():
#                 i += 1
#                 continue
# 
#             segment_y_data = y_data[segment_indices]
#             segment_x_data = x_data[segment_indices]
#             peak_y = np.max(segment_y_data)
#             peak_x = segment_x_data[np.argmax(segment_y_data)]
#             peaks.append((peak_x, peak_y))
# 
#             next_i_candidate = np.where(x_data >= peak_x + segment_width)[0]
#             i = next_i_candidate[0] if len(next_i_candidate) > 0 else len(x_data)
# 
#         sorted_peaks = sorted(peaks, key=lambda p: p[1], reverse=True)[:10]
#         for peak_x, peak_y in sorted_peaks:
#             ax.axvline(x=peak_x, color="orange", linestyle="--", linewidth=1, zorder=4)
# 
#         if LOCAL_DEBUG: logger.success(f"✅ Found and plotted {len(sorted_peaks)} peaks.")
#     except Exception:
#         logger.exception("❌ Error in _find_and_plot_peaks")
# 
# 
# def _setup_zoom_events(ax, canvas, original_xlim):
#     """Sets up event handlers for horizontal zooming on the plot."""
#     if LOCAL_DEBUG: logger.debug("▶️ _setup_zoom_events.")
# 
#     try:
#         drag_start_x = None
#         ax.original_xlim = original_xlim
# 
#         def on_press(event):
#             nonlocal drag_start_x
#             if event.button == 1 and event.inaxes == ax:
#                 drag_start_x = event.xdata
# 
#         def on_release(event):
#             nonlocal drag_start_x
#             if event.button == 1 and event.inaxes == ax and drag_start_x is not None:
#                 drag_end_x = event.xdata
#                 if drag_end_x is not None and drag_start_x != drag_end_x:
#                     ax.set_xlim(
#                         min(drag_start_x, drag_end_x), max(drag_start_x, drag_end_x)
#                     )
#                     canvas.draw_idle()
#                 drag_start_x = None
# 
#         def on_double_click(event):
#             if event.button == 1 and event.inaxes == ax:
#                 reset_zoom(ax=ax, canvas=canvas)
# 
#         canvas.mpl_connect("button_press_event", on_press)
#         canvas.mpl_connect("button_release_event", on_release)
#         canvas.mpl_connect("button_press_event", on_double_click)
#         if LOCAL_DEBUG: logger.success("✅ Zoom events are now live!")
#     except Exception:
#         logger.exception("❌ Error in _setup_zoom_events")
# 
# 
# def reset_zoom(ax, canvas):
#     """Resets the plot to its original, full x-axis view."""
#     if LOCAL_DEBUG: logger.debug("▶️ reset_zoom.")
#     try:
#         if hasattr(ax, "original_xlim"):
#             ax.set_xlim(ax.original_xlim)
#             canvas.draw_idle()
#         if LOCAL_DEBUG: logger.success("✅ Zoom reset.")
#     except Exception:
#         logger.exception("❌ Error in reset_zoom")
# 
# 
# def update_single_plot(
#     scan_view_tab_instance,
#     data,
#     start_freq_MHz,
#     end_freq_MHz,
#     plot_title,
#     line_color="yellow",
# ):
#     """Updates the single plot in the Scan View tab with new data."""
#     if LOCAL_DEBUG: logger.debug(f"▶️ update_plot with plot_title: {plot_title}")
# 
#     try:
#         plot_info = scan_view_tab_instance.plot
#         ax = plot_info["ax"]
#         canvas = plot_info["canvas"]
#         ax.clear()
# 
#         data_tuples = None
#         if data is not None and not data.empty:
#             data_tuples = list(zip(data["Frequency_Hz"], data["Power_dBm"]))
# 
#         if data_tuples:
#             frequencies, amplitudes = zip(*data_tuples)
#             ax.plot(frequencies, amplitudes, color=line_color, linewidth=1)
# 
#         ax.set_title(plot_title, color="white")
#         ax.set_xlim(start_freq_MHz, end_freq_MHz)
#         ax.set_ylim(-120, 0)
#         ax.set_yticks(np.arange(-120, 1, 20))
#         ax.grid(True, linestyle="--", color="gray", alpha=0.5)
# 
#         annot = ax.annotate(
#             "",
#             xy=(0, 0),
#             xytext=(20, 20),
#             textcoords="offset points",
#             bbox=dict(boxstyle="round", fc="white", ec="black", lw=1),
#             arrowprops=dict(arrowstyle="wedge,tail_width=0.5", fc="white", ec="black"),
#         )
#         annot.set_visible(False)
# 
#         def update_annot(event):
#             if data_tuples and event.xdata and event.ydata:
#                 x_data = np.array(data_tuples)[:, 0]
#                 y_data = np.array(data_tuples)[:, 1]
#                 idx = np.abs(x_data - event.xdata).argmin()
#                 annot.xy = (x_data[idx], y_data[idx])
#                 annot.set_text(
#                     f"Freq: {x_data[idx]:.3f} MHz\nAmp: {y_data[idx]:.2f} dBm"
#                 )
#                 annot.set_visible(True)
#                 canvas.draw_idle()
#             else:
#                 annot.set_visible(False)
#                 canvas.draw_idle()
# 
#         canvas.mpl_connect("motion_notify_event", update_annot)
# 
#         _find_and_plot_peaks(
#             ax=ax,
#             data=data_tuples,
#             start_freq_MHz=start_freq_MHz,
#             end_freq_MHz=end_freq_MHz,
#         )
#         _setup_zoom_events(
#             ax=ax, canvas=canvas, original_xlim=(start_freq_MHz, end_freq_MHz)
#         )
# 
#         canvas.draw()
#         if LOCAL_DEBUG: logger.success("✅ Plot updated.")
#     except Exception:
#         logger.exception("❌ Error in update_single_plot")
