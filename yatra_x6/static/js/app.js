const itineraryForm = document.querySelector("#itinerary-form");
const routeForm = document.querySelector("#route-form");
const ticketForm = document.querySelector("#ticket-form");
const verifyForm = document.querySelector("#verify-form");
const sosButton = document.querySelector("#sos-button");
const scannerToggle = document.querySelector("#scanner-toggle");
let routeMap;
let routeLayer;
let qrScanner;

function setResult(elementId, message, type = "") {
  const element = document.querySelector(elementId);
  element.className = `result ${type}`;
  element.textContent = message;
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }
  return payload;
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function createItineraryMarkup(plan) {
  const days = Array.isArray(plan.days) ? plan.days : [];
  const daysMarkup = days.map((day) => {
    const activities = Array.isArray(day.activities) ? day.activities : [];
    const activityMarkup = activities.map((activity) => `
      <li>
        <strong>${activity.time || ""} ${activity.place || ""}</strong>
        <span>${activity.notes || ""} ${formatCurrency(activity.cost)}</span>
      </li>
    `).join("");
    return `<div class="result-day"><strong>Day ${day.day}: ${day.theme || "Explore"}</strong><ul>${activityMarkup}</ul></div>`;
  }).join("");

  return `<strong>${plan.destination || "Your itinerary"}</strong><span>Estimated total: ${formatCurrency(plan.total_estimated_cost)}</span>${daysMarkup}`;
}

function drawRouteMap(geometry) {
  if (!window.L || !geometry?.coordinates?.length) {
    document.querySelector("#route-map").textContent = "Route calculated. Map preview unavailable.";
    return;
  }

  if (!routeMap) {
    routeMap = L.map("route-map").setView([20.5937, 78.9629], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(routeMap);
  }

  if (routeLayer) {
    routeLayer.remove();
  }
  const points = geometry.coordinates.map(([longitude, latitude]) => [latitude, longitude]);
  routeLayer = L.polyline(points, { color: "#0f7771", weight: 5 }).addTo(routeMap);
  routeMap.fitBounds(routeLayer.getBounds(), { padding: [18, 18] });
}

itineraryForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(itineraryForm);
  const interests = formData.get("interests").split(",").map((item) => item.trim()).filter(Boolean);
  setResult("#itinerary-result", "Building your itinerary...");

  try {
    const plan = await requestJson("/api/itinerary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        destination: formData.get("destination"),
        days: Number(formData.get("days")),
        budget: Number(formData.get("budget")),
        interests,
      }),
    });
    const result = document.querySelector("#itinerary-result");
    result.className = "result result-success";
    result.innerHTML = createItineraryMarkup(plan);
  } catch (error) {
    setResult("#itinerary-result", error.message, "result-error");
  }
});

function parseCoordinates(value) {
  const coordinates = value.split(",").map((part) => Number(part.trim()));
  if (coordinates.length !== 2 || coordinates.some((part) => !Number.isFinite(part))) {
    throw new Error("Use coordinates in latitude, longitude format.");
  }
  return coordinates;
}

routeForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(routeForm);
  setResult("#route-result", "Calculating route...");

  try {
    const route = await requestJson("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start: parseCoordinates(formData.get("start")),
        end: parseCoordinates(formData.get("end")),
      }),
    });
    setResult("#route-result", `${Number(route.distance_km).toFixed(1)} km | ${Number(route.duration_min).toFixed(0)} minutes`, "result-success");
    drawRouteMap(route.geometry);
  } catch (error) {
    setResult("#route-result", error.message, "result-error");
  }
});

verifyForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const ticketId = new FormData(verifyForm).get("ticket_id").trim();
  setResult("#verify-result", "Checking ticket...");

  try {
    const result = await requestJson(`/api/ticket/${encodeURIComponent(ticketId)}/verify`, { method: "POST" });
    setResult("#verify-result", result.message, "result-success");
  } catch (error) {
    setResult("#verify-result", error.message, "result-error");
  }
});

async function verifyTicket(ticketId) {
  setResult("#verify-result", "Checking ticket...");
  try {
    const result = await requestJson(`/api/ticket/${encodeURIComponent(ticketId)}/verify`, { method: "POST" });
    setResult("#verify-result", result.message, "result-success");
  } catch (error) {
    setResult("#verify-result", error.message, "result-error");
  }
}

scannerToggle?.addEventListener("click", async () => {
  const reader = document.querySelector("#qr-reader");
  if (qrScanner) {
    await qrScanner.stop();
    qrScanner.clear();
    qrScanner = null;
    reader.hidden = true;
    scannerToggle.textContent = "Scan QR ticket";
    return;
  }
  if (!window.Html5Qrcode) {
    setResult("#verify-result", "QR scanner library is unavailable.", "result-error");
    return;
  }
  reader.hidden = false;
  scannerToggle.textContent = "Stop scanner";
  qrScanner = new Html5Qrcode("qr-reader");
  await qrScanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: { width: 220, height: 220 } },
    async (decodedText) => {
      document.querySelector("#verify-ticket-id").value = decodedText;
      await verifyTicket(decodedText);
      await qrScanner.stop();
      qrScanner.clear();
      qrScanner = null;
      reader.hidden = true;
      scannerToggle.textContent = "Scan QR ticket";
    },
    () => {}
  );
});

ticketForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(ticketForm);
  setResult("#ticket-result", "Creating your ticket...");

  try {
    const ticket = await requestJson("/api/ticket", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: formData.get("name"),
        monument: formData.get("monument"),
        date: formData.get("date"),
      }),
    });
    const result = document.querySelector("#ticket-result");
    result.className = "result result-success ticket-result-content";
    result.innerHTML = `<strong>Ticket created</strong><span>ID: ${ticket.ticket_id}</span><img src="data:image/png;base64,${ticket.qr_base64}" alt="QR code for ticket ${ticket.ticket_id}">`;
  } catch (error) {
    setResult("#ticket-result", error.message, "result-error");
  }
});

sosButton?.addEventListener("click", () => {
  if (!navigator.geolocation) {
    setResult("#sos-result", "Location is not available in this browser.", "result-error");
    return;
  }

  sosButton.disabled = true;
  sosButton.textContent = "Locating you...";
  setResult("#sos-result", "Requesting your location...");

  navigator.geolocation.getCurrentPosition(async (position) => {
    try {
      await requestJson("/api/sos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          user: "Yatra traveller",
        }),
      });
      setResult("#sos-result", "SOS alert sent with your location.", "result-success");
    } catch (error) {
      setResult("#sos-result", error.message, "result-error");
    } finally {
      sosButton.disabled = false;
      sosButton.textContent = "Send SOS alert";
    }
  }, () => {
    setResult("#sos-result", "Location permission was denied or unavailable.", "result-error");
    sosButton.disabled = false;
    sosButton.textContent = "Send SOS alert";
  });
});
