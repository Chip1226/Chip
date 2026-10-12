import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

// Where submissions are saved. NOTE: this works on your computer, but hosts like
// Vercel don't allow writing files, so before going live this should be swapped
// for an email service (e.g. Resend) or a database.
const FILE = path.join(process.cwd(), "data", "demo-requests.json");

const BUSINESS_TYPES = ["pool", "landscaping", "both"] as const;

type DemoRequest = {
  name: string;
  company: string;
  businessType: (typeof BUSINESS_TYPES)[number];
  phone: string;
  email: string;
  submittedAt: string;
};

const clean = (v: unknown, max = 200) => (typeof v === "string" ? v.trim().slice(0, max) : "");

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
    let existing: DemoRequest[] = [];
    try {
      existing = JSON.parse(await fs.readFile(FILE, "utf8"));
    } catch {
      // File doesn't exist yet; start a new list
    }
    existing.push(entry);
    await fs.mkdir(path.dirname(FILE), { recursive: true });
    await fs.writeFile(FILE, JSON.stringify(existing, null, 2));
  } catch (err) {
    console.error("Could not save demo request", err);
    return NextResponse.json(
      { error: "Something went wrong saving your request. Please try again." },
      { status: 500 },
    );
  }

  return NextResponse.json({ ok: true });
}
