import { request } from "./client.js";

export const loginRequest = (email, password) =>
  request("/auth/login", { method: "POST", body: { email, password }, auth: false });

export const registerRequest = (payload) =>
  request("/auth/register", { method: "POST", body: payload, auth: false });

export const meRequest = () => request("/auth/me");