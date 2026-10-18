import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import ProtectedRoute from "../components/ProtectedRoute.jsx";
import { AuthContext } from "../context/AuthContext.jsx";

function setup(value, roles, start = "/secret") {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[start]}>
        <Routes>
          <Route path="/roles" element={<div>Role page</div>} />
          <Route path="/app" element={<div>Shopper home</div>} />
          <Route path="/secret" element={<ProtectedRoute roles={roles}><div>Secret</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("ProtectedRoute", () => {
  it("shows a loading state while the session is restored", () => {
    setup({ user: null, loading: true }, ["admin"]);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
  it("redirects visitors to role selection", () => {
    setup({ user: null, loading: false }, ["admin"]);
    expect(screen.getByText("Role page")).toBeInTheDocument();
  });
  it("sends a shopper away from admin-only pages", () => {
    setup({ user: { role: "user" }, loading: false }, ["admin"]);
    expect(screen.getByText("Shopper home")).toBeInTheDocument();
  });
  it("lets the right role in", () => {
    setup({ user: { role: "admin" }, loading: false }, ["admin"]);
    expect(screen.getByText("Secret")).toBeInTheDocument();
  });
});