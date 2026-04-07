GPUMon - GPU Monitoring Toolkit
================================

Collect nvidia-smi dmon data on a server (no dependencies), then generate
line-chart PNGs on a local machine with matplotlib.

Files
-----
  gpu_collect.py    Data collector (server side, stdlib only)
  gpu_plot.py       CSV to PNG plotter (local side, needs matplotlib)
  gpu_burn_test.run All-in-one stress test script (gpu_collect + gpu-burn)

Requirements
------------
  Server:  Python 3, nvidia-smi
  Local:   Python 3, matplotlib (pip install matplotlib)

Quick Start
-----------

1. Collect data on the server:

    python3 gpu_collect.py
    python3 gpu_collect.py -i 2 -o my_data.csv -d 3600

    Options:
      -i  Sampling interval in seconds (default: 1)
      -o  Output CSV path (default: gpu_data.csv)
      -d  Duration in seconds, 0 = unlimited (default: 0)

    Press Ctrl+C to stop. The CSV includes: timestamp, gpu index, uuid,
    power, temperature, sm%, mem%, encoder%, decoder%, memory clock, sm clock.

2. Copy CSV to local machine and plot:

    python3 gpu_plot.py gpu_data.csv
    python3 gpu_plot.py gpu_data.csv -o chart.png --dpi 200
    python3 gpu_plot.py gpu_data.csv --metrics sm mem pclk

    Options:
      -o        Output PNG path (default: <csv_name>.png)
      --dpi     Image DPI (default: 150)
      --metrics Metrics to plot (default: pwr gtemp sm mem pclk)
                Available: pwr gtemp sm mem enc dec mclk pclk

    The output PNG contains line charts for each selected metric and a
    summary table at the bottom showing GPU index, UUID, max, min, and
    average values per metric.

3. Stress test with gpu-burn:

    Place gpu-burn binary in the same directory, then:

    ./gpu_burn_test.run

    Flow: start collecting -> wait 10s -> gpu-burn -d 1800 -> wait for
    gpu-burn to finish -> wait 10s -> stop collecting.

    Output CSV is named gpu_burn_<timestamp>.csv.

CSV Format
----------
  timestamp, gpu, uuid, pwr, gtemp, sm, mem, enc, dec, mclk, pclk
