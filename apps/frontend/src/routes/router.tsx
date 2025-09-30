import { createBrowserRouter, Navigate } from "react-router-dom";
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import Dashboard from "../pages/Dashboard";
import ProtectedRoute from "./ProtectedRoute";
import Generate from "../pages/Generate";
import SessionDetail from "../pages/sessions/SessionDetail"; 
import Home from "../pages/Home"

export const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/", element: <Navigate to="/dashboard" replace /> },
  { path: "/login", element: <Login /> },
  { path: "/register", element: <Register /> },
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: "/generate",
    element: (
      <ProtectedRoute>
        <Generate />
      </ProtectedRoute>
    ),
  },
  {
    path: "/sessions/:id",
    element: (
      <ProtectedRoute>
        <SessionDetail />
      </ProtectedRoute>
    ),
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
