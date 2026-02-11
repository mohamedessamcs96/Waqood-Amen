const API_URL = "http://127.0.0.1:8000";

export async function register(username: string, password: string, role: string = "employee") {
  const res = await fetch(`${API_URL}/api/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      password,
      password_confirm: password,
      role,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.error || "Registration failed");
  }
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_URL}/api/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.error || "Invalid username or password");
  }
  const data = await res.json();
  // Return the format App.tsx expects: { role, name }
  return {
    role: data.user?.role || "employee",
    name: data.user?.username || username,
    token: data.token,
  };
}

export async function getAllCars() {
  const res = await fetch(`${API_URL}/api/cars/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUnpaidCars() {
  const res = await fetch(`${API_URL}/api/cars/unpaid/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addCar(plate: string) {
  const form = new FormData();
  form.append("plate", plate);
  const res = await fetch(`${API_URL}/api/cars/`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function markCarPaid(carId: number) {
  const res = await fetch(`${API_URL}/api/cars/${carId}/mark_paid/`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function markCarUnpaid(carId: number) {
  const res = await fetch(`${API_URL}/api/cars/${carId}/mark_unpaid/`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function checkPlate(plate: string) {
  const res = await fetch(`${API_URL}/api/cars/check_plate/?plate=${encodeURIComponent(plate)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadCarVideo(carId: number, file: File) {
  const form = new FormData();
  form.append("video", file);
  const res = await fetch(`${API_URL}/api/cars/upload_video/`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCarsWithAnalysis() {
  const res = await fetch(`${API_URL}/api/cars/with_analysis/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeVideo(carId: number) {
  const res = await fetch(`${API_URL}/api/cars/${carId}/analyze/`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getCarVideoFrameUrl(carId: number) {
  return `${API_URL}/api/cars/${carId}/video_frame/`;
}

export async function updateVehiclePlate(vehicleId: number, plateText: string) {
  const res = await fetch(`${API_URL}/api/detected-vehicles/${vehicleId}/update_plate/`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ plate_text: plateText }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

