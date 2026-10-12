import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Inter } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
});

const body = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "DesertDesk | 24/7 AI receptionist for pool & landscaping companies",
  description:
    "DesertDesk answers every call for Phoenix-area pool service and landscaping companies, 24/7. It books estimates and texts you a summary of every call.",
  openGraph: {
    title: "DesertDesk | Your crew's in the yard. Your phone still gets answered.",
    description:
      "A 24/7 AI receptionist built for Arizona pool service and landscaping companies.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#FBF9F5",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>{children}</body>
    </html>
  );
}
