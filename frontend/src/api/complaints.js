import { request } from "./client.js";

export const fileComplaint = (body) => request("/complaints", { method: "POST", body });
export const listMyComplaints = (page = 1) => request(`/complaints?page=${page}`);