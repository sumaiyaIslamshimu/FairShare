import { request } from "./client.js";

export const getVerificationStatus = () => request("/verification/status");

export function submitVerification(nidNumber, file) {
  const form = new FormData();
  form.append("nid_number", nidNumber);
  form.append("document", file);
  return request("/verification/submit", { method: "POST", body: form });
}