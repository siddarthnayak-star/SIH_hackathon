function sendSOS() {
  navigator.geolocation.getCurrentPosition(pos => {
    fetch("/sos", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        user: currentUser
      })
    });
  });
}