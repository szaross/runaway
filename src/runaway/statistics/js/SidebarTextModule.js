// Sidebar-targeting TextModule for the stats dashboard
const SidebarTextModule = function () {
  const container = document.createElement("div");
  container.style.width = "100%";

  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.appendChild(container);
  }

  this.render = function (data) {
    container.innerHTML = data;
  };

  this.reset = function () {
    container.innerHTML = "";
  };
};
