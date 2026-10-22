import { request } from "./client.js";

export const getThreads = () => request("/messages/threads");
export const getThreadMessages = (threadId) => request(`/messages/threads/${threadId}`);
export const sendMessage = (data) => request("/messages", { method: "POST", body: data });