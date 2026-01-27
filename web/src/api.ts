const API_URL = "http://127.0.0.1:8000";

export async function register(username: string, password: string, role: string = "employee") {
  const form = new FormData();
  form.append("username", username);
  form.append("password", password);
  form.append("role", role);
  const res = await fetch(`${API_URL}/register`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function login(username: string, password: string) {
  const form = new FormData();
  form.append("username", username);
  form.append("password", password);
  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAllCars() {
  const res = await fetch(`${API_URL}/cars`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUnpaidCars() {
  const res = await fetch(`${API_URL}/cars/unpaid`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addCar(plate: string) {
  const form = new FormData();
  form.append("plate", plate);
  const res = await fetch(`${API_URL}/cars`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function markCarPaid(carId: number) {
  const res = await fetch(`${API_URL}/cars/pay/${carId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadCarVideo(carId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/upload-car-video/${carId}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCarsWithAnalysis() {
  const res = await fetch(`${API_URL}/cars-with-analysis`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeVideo(carId: number) {
  const res = await fetch(`${API_URL}/analyze-video/${carId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getCarVideoFrameUrl(carId: number) {
  return `${API_URL}/car-video-frame/${carId}`;
}

export async function updateVehiclePlate(vehicleId: number, plateText: string) {
  const res = await fetch(`${API_URL}/detected-vehicles/${vehicleId}/plate`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ plate_text: plateText }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

