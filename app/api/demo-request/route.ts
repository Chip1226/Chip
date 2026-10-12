import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

// How submissions are delivered:
// - If RESEND_API_KEY is set (it must be on Vercel), each request is emailed to
//   DEMO_NOTIFY_EMAIL through Resend (https://resend.com).
// - Otherwise (previewing on your own computer), it's saved to
//   data/demo-requests.json instead.
const FILE = path.join(process.cwd(), "data", "demo-requests.json");

const BUSINESS_TYPES = ["pool", "landscaping", "both"] as const;
const BUSINESS_LABELS: Record<(typeof BUSINESS_TYPES)[number], string> = {
  pool: "Pool service",
  landscaping: "Landscaping",
  both: "Pool service + landscaping",
};

type DemoRequest = {
  name: string;
  company: string;
  businessType: (typeof BUSINESS_TYPES)[number];
  phone: string;
  email: string;
  submittedAt: string;
};

const clean = (v: unknown, max = 200) => (typeof v === "string" ? v.trim().slice(0, max) : "");

const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  // Spam trap: real visitors never see or fill the "website" field
  if (clean(body.website)) {
    return NextResponse.json({ ok: true });
  }

  const entry: DemoRequest = {
    name: clean(body.name),
    company: clean(body.company),
    businessType: clean(body.businessType) as DemoRequest["businessType"],
    phone: clean(body.phone, 40),
    email: clean(body.email),
    submittedAt: new Date().toISOString(),
  };

  const errors: Record<string, string> = {};
  if (!entry.name) errors.name = "Please enter your name.";
  if (!entry.company) errors.company = "Please enter your company name.";
  if (!BUSINESS_TYPES.includes(entry.businessType)) errors.businessType = "Please choose one.";
  if (entry.phone.replace(/\D/g, "").length < 10) errors.phone = "Please enter a 10-digit phone number.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(entry.email)) errors.email = "Please enter a valid email.";
  if (Object.keys(errors).length) {
    return NextResponse.json({ errors }, { status: 422 });
  }

  try {
    if (process.env.RESEND_API_KEY) {
      await sendEmail(entry);
    } else if (process.env.VERCEL) {
      // On Vercel files can't be saved, so a missing key would silently lose leads
      throw new Error("RESEND_API_KEY is not set in Vercel's environment variables.");
    } else {
      await saveToFile(entry);
    }
  } catch (err) {
    console.error("Could not deliver demo request", err);
    return NextResponse.json(
      { error: "Something went wrong sending your request. Please try again in a minute." },
      { status: 500 },
    );
  }

  return NextResponse.json({ ok: true });
}

async function sendEmail(entry: DemoRequest) {
  const to = process.env.DEMO_NOTIFY_EMAIL;
  if (!to) throw new Error("DEMO_NOTIFY_EMAIL is not set.");
  // Resend's shared test sender works until you verify your own domain with them
  const from = process.env.DEMO_FROM_EMAIL || "DesertDesk <onboarding@resend.dev>";

  const when = new Date(entry.submittedAt).toLocaleString("en-US", {
    timeZone: "America/Phoenix",
    dateStyle: "medium",
    timeStyle: "short",
  });
  const rows: [string, string][] = [
    ["Name", entry.name],
    ["Company", entry.company],
    ["Business type", BUSINESS_LABELS[entry.businessType]],
    ["Phone", entry.phone],
    ["Email", entry.email],
    ["Submitted", `${when} (Arizona time)`],
  ];

  const text = [`New demo request from ${entry.company}`, "", ...rows.map(([k, v]) => `${k}: ${v}`)].join("\n");
  const html = `
    <div style="font-family:system-ui,sans-serif;color:#1F2326;max-width:520px">
      <h2 style="margin:0 0 4px;color:#0A6E8C">New demo request</h2>
      <p style="margin:0 0 16px;color:#4A5157">Reply to this email to respond to ${escapeHtml(entry.name)} directly.</p>
      <table style="border-collapse:collapse;width:100%">
        ${rows
          .map(
            ([k, v]) =>
              `<tr><td style="padding:8px 12px 8px 0;color:#6E767D;white-space:nowrap;vertical-align:top">${k}</td><td style="padding:8px 0;font-weight:600">${escapeHtml(v)}</td></tr>`,
          )
          .join("")}
      </table>
    </div>`;

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: to.split(",").map((s) => s.trim()),
      reply_to: entry.email,
      subject: `New demo request: ${entry.company} (${BUSINESS_LABELS[entry.businessType]})`,
      text,
      html,
    }),
  });
  if (!res.ok) {
    throw new Error(`Resend responded ${res.status}: ${await res.text()}`);
  }
}

async function saveToFile(entry: DemoRequest) {
  let existing: DemoRequest[] = [];
  try {
    existing = JSON.parse(await fs.readFile(FILE, "utf8"));
  } catch {
    // File doesn't exist yet; start a new list
  }
  existing.push(entry);
  await fs.mkdir(path.dirname(FILE), { recursive: true });
  await fs.writeFile(FILE, JSON.stringify(existing, null, 2));
}
