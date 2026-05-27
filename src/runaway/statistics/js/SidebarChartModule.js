// Chart module that renders into #sidebar instead of #elements
const SidebarChartModule = function (series, canvas_width, canvas_height) {
  const canvas = document.createElement("canvas");
  Object.assign(canvas, {
    width: canvas_width,
    height: canvas_height,
  });
  canvas.style.width = "100%";
  canvas.style.height = "auto";
  canvas.style.borderRadius = "8px";
  canvas.style.background = "#f8fafc";

  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.appendChild(canvas);
  }

  const context = canvas.getContext("2d");

  const convertColorOpacity = (hex) => {
    if (hex.indexOf("#") != 0) return "rgba(0,0,0,0.1)";
    hex = hex.replace("#", "");
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return "rgba(" + r + "," + g + "," + b + ",0.1)";
  };

  const datasets = [];
  for (const i in series) {
    const s = series[i];
    const new_series = {
      backgroundColor: convertColorOpacity(s.Color),
      borderColor: s.Color,
      label: s.Label,
      data: [],
    };
    for (const property in s) {
      if (["Color", "Label"].includes(property)) continue;
      new_series[property] = s[property];
    }
    datasets.push(new_series);
  }

  const chartData = { labels: [], datasets: datasets };
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    animation: { duration: 100, easing: 'linear' },
    plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } } },
    scales: {
      x: { display: true, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
      y: { display: true, ticks: { font: { size: 10 } } },
    },
  };

  const chart = new Chart(context, { type: "line", data: chartData, options: chartOptions });

  this.render = (data) => {
    chart.data.labels.push(control.tick);
    for (let i = 0; i < data.length; i++) {
      chart.data.datasets[i].data.push(data[i]);
    }
    chart.update("none");
  };

  this.reset = () => {
    while (chart.data.labels.length) chart.data.labels.pop();
    chart.data.datasets.forEach((dataset) => {
      while (dataset.data.length) dataset.data.pop();
    });
    chart.update("none");
  };
};
