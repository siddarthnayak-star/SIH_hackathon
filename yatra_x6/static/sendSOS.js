async function sendSOS(user = "Yatra traveller") {
  if (!navigator.geolocation) {
    throw new Error("Location is not available in this browser.");
  }

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(async pos => {
      try {
        const response = await fetch("/api/sos", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            user
          })
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Unable to send SOS alert.");
        }
        resolve(payload);
      } catch (error) {
        reject(error);
      }
    }, () => reject(new Error("Location permission was denied or unavailable.")));
  });
}