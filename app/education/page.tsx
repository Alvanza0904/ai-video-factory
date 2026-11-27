"use client";

import { useEffect } from "react";

export default function EducationRedirect() {
  useEffect(() => { window.location.replace("/"); }, []);
  return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#080d12", color: "#f3f7f8", fontFamily: "Arial, sans-serif" }}>Membuka Animated Video Studio…</main>;
}
