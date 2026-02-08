import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LTN Analysis: Canal St to Houston St Corridor",
  description:
    "Interactive GIS visualization for Low Traffic Neighborhood analysis in Lower Manhattan. Senior thesis research by Alexander Huang, The New School.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
