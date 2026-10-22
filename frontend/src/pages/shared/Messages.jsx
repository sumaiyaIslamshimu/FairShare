import { useEffect, useState } from "react";
import { getThreads, getThreadMessages, sendMessage } from "../../api/messages.js";
import { useAuth } from "../../context/AuthContext.jsx";
import Button from "../../components/Button.jsx";

export default function Messages() {
  const { user } = useAuth();
  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [reply, setReply] = useState("");

  const fetchThreads = async () => {
    try {
      const data = await getThreads();
      setThreads(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchThreads();
  }, []);

  const openThread = async (thread) => {
    setActiveThread(thread);
    try {
      const msgs = await getThreadMessages(thread.thread_id);
      setMessages(msgs);
      fetchThreads(); // Refresh to clear unread badges
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!reply.trim()) return;
    try {
      const recipientId = activeThread.participants.find(p => p !== user.id);
      await sendMessage({
        recipient_id: recipientId,
        body: reply,
        order_id: activeThread.order_id,
        product_id: activeThread.product_id
      });
      setReply("");
      openThread(activeThread); // Refresh conversation
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={{ display: "flex", gap: "2rem", height: "70vh" }}>
      <div style={{ width: "30%", borderRight: "1px solid #ccc", paddingRight: "1rem", overflowY: "auto" }}>
        <h2>Conversations</h2>
        {!threads.length && <p>No messages yet.</p>}
        {threads.map(t => (
          <div
            key={t.thread_id}
            onClick={() => openThread(t)}
            style={{
              padding: "10px",
              marginBottom: "10px",
              cursor: "pointer",
              background: activeThread?.thread_id === t.thread_id ? "#e0f2fe" : "#f9f9f9",
              border: "1px solid #ddd",
              borderRadius: "5px"
            }}
          >
            <strong>{t.last_message.body.substring(0, 30)}...</strong>
            {t.unread_count > 0 && <span style={{ color: "red", marginLeft: "10px" }}>({t.unread_count} new)</span>}
          </div>
        ))}
      </div>

      <div style={{ width: "70%", display: "flex", flexDirection: "column" }}>
        {!activeThread ? (
          <div style={{ margin: "auto", color: "#888" }}>Select a conversation to start messaging.</div>
        ) : (
          <>
            <div style={{ flex: 1, overflowY: "auto", border: "1px solid #ddd", padding: "1rem", marginBottom: "1rem", borderRadius: "5px" }}>
              {messages.map(m => (
                <div key={m.id} style={{ textAlign: m.sender_id === user.id ? "right" : "left", marginBottom: "10px" }}>
                  <div style={{
                    display: "inline-block",
                    padding: "8px 12px",
                    borderRadius: "15px",
                    background: m.sender_id === user.id ? "#3b82f6" : "#e5e7eb",
                    color: m.sender_id === user.id ? "white" : "black"
                  }}>
                    {m.body}
                  </div>
                </div>
              ))}
            </div>
            <form onSubmit={handleSend} style={{ display: "flex", gap: "10px" }}>
              <input
                type="text"
                value={reply}
                onChange={e => setReply(e.target.value)}
                placeholder="Type your message..."
                style={{ flex: 1, padding: "10px", borderRadius: "5px", border: "1px solid #ccc" }}
              />
              <Button type="submit">Send</Button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}