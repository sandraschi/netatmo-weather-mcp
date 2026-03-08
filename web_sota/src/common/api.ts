/**
 * API client for Netatmo Weather MCP backend.
 * Backend runs on port 10823 (see web_sota/start.ps1).
 */

const DEFAULT_BASE = "http://127.0.0.1:10823/api";
const base = (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ?? DEFAULT_BASE;

export interface HealthResponse {
  success: boolean;
  status: string;
  service?: string;
}

export interface StationSummary {
  id: string;
  name: string;
  home_name: string;
  reachable: boolean;
  modules_count: number;
  data_types?: string[];
}

export interface StationsResponse {
  success: boolean;
  stations: StationSummary[];
  total_count: number;
  reachable_count: number;
}

export interface StationStatusResponse {
  success: boolean;
  status: { reachable?: boolean; [k: string]: unknown };
}

export interface CurrentWeatherData {
  temperature?: number;
  humidity?: number;
  pressure?: number;
  co2?: number;
  noise?: number;
  rain?: number;
  wind_strength?: number;
  wind_angle?: number;
  gust_strength?: number;
  gust_angle?: number;
}

export interface CurrentWeatherResponse {
  success: boolean;
  station_id: string;
  timestamp: string;
  data: CurrentWeatherData;
  data_points?: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getStations(): Promise<StationsResponse> {
  return request<StationsResponse>("/stations");
}

export async function getStation(stationId: string): Promise<{ success: boolean; station: unknown }> {
  return request(`/stations/${encodeURIComponent(stationId)}`);
}

export async function getStationStatus(stationId: string): Promise<StationStatusResponse> {
  return request(`/stations/${encodeURIComponent(stationId)}/status`);
}

export async function getCurrentWeather(stationId: string): Promise<CurrentWeatherResponse> {
  return request(`/weather/current?station_id=${encodeURIComponent(stationId)}`);
}

export interface CredentialsStatus {
  configured: boolean;
}

export interface CredentialsPayload {
  client_id: string;
  client_secret: string;
  username: string;
  password: string;
  scope?: string;
}

export async function getCredentialsStatus(): Promise<CredentialsStatus> {
  return request<CredentialsStatus>("/config/credentials");
}

export async function setCredentials(payload: CredentialsPayload): Promise<{ success: boolean; message?: string }> {
  return request("/config/credentials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
