import express from "express";
import { exec } from "child_process";
import fs from "fs";
import yaml from "js-yaml";
import bodyParser from "body-parser";

const app = express();
const PORT = 3000;
const GATE_PATH = "/home/container/gate/gate.yaml";
const ROUTES_PATH = "./routes.json";

// --- Middleware ---
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));

// --- Load or create routes.json ---
let routes = {};
if (fs.existsSync(ROUTES_PATH)) {
  routes = JSON.parse(fs.readFileSync(ROUTES_PATH));
} else {
  fs.writeFileSync(ROUTES_PATH, JSON.stringify(routes));
}

// --- Functions ---
function updateGateConfig(routes) {
  const config = {
    bind: "0.0.0.0:19132",
    lite: {
      enabled: true,
      routes: Object.keys(routes).map(domain => ({
        host: domain,
        backend: routes[domain],
        modifyVirtualHost: true
      }))
    }
  };

  fs.writeFileSync(GATE_PATH, yaml.dump(config));
  console.log("[Node] gate.yaml updated");
}

function reloadGate() {
  console.log("[Node] Reloading Gate...");
  exec(`pkill -f 'gate' && cd /home/container/gate && ./gate --config gate.yaml &`, (err) => {
    if (err) console.error("[Node] Error reloading Gate:", err);
    else console.log("[Node] Gate reloaded successfully");
  });
}

// --- Routes ---
app.get("/", (req, res) => {
  res.sendFile(`${process.cwd()}/public/index.html`);
});

app.post("/add-server", (req, res) => {
  const { domain, port } = req.body;
  if (!domain || !port) return res.status(400).send("Missing domain or port");

  routes[domain] = `127.0.0.1:${port}`;
  fs.writeFileSync(ROUTES_PATH, JSON.stringify(routes, null, 2));

  updateGateConfig(routes);
  reloadGate();

  res.send(`Added ${domain}:${port} and reloaded Gate!`);
});

app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
