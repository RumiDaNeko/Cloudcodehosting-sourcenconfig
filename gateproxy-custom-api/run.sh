#!/bin/bash

# --- Move to container root ---
cd /home/container || exit 1

# --- Start Node.js automation in background ---
echo "[Startup] Launching Node.js automation..."
npx --yes tsx ./app/logs.ts &
NODE_PID=$!
echo "[Startup] Node.js PID: $NODE_PID"

# --- Start Gate Lite ---
echo "[Startup] Launching Gate Lite..."
chmod +x gate*
./gate --config gate.yaml &
GATE_PID=$!
echo "[Startup] Gate PID: $GATE_PID"

# --- Wait for Gate to exit so container stays alive ---
wait $GATE_PID
