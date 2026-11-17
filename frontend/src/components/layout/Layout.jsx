import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import ToastStack from "../ui/Toast";

export default function Layout() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="pl-60">
        <Navbar />
        <main className="mx-auto max-w-6xl px-6 py-6">
          <Outlet />
        </main>
      </div>
      <ToastStack />
    </div>
  );
}
