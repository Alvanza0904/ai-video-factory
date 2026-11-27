import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Animated Video Studio | OMODA × JAECOO",
  description: "Studio produksi video animasi otomotif: generate, pantau proses render, dan simpan hasil produksi OMODA serta JAECOO.",
  applicationName: "Animated Video Studio"
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#090b10"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
