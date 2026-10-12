# DesertDesk marketing site

One-page marketing site for DesertDesk, a 24/7 AI receptionist for Phoenix-area pool service and landscaping companies. Built with Next.js and Tailwind CSS.

## Preview it on your computer

1. Install [Node.js](https://nodejs.org) (the "LTS" version) if you don't have it.
2. Open a terminal in this folder and run:
   ```
   npm install
   npm run dev
   ```
3. Open **http://localhost:3000** in your browser.
4. To see it on your phone: make sure the phone is on the same Wi-Fi, then open `http://<your-computer's-IP>:3000`. The terminal prints this as the "Network" address.

Press `Ctrl + C` in the terminal to stop the preview.

## Where things live

| What you want to change | File |
| --- | --- |
| Hero headline, buttons | `components/Hero.tsx` |
| Sample call transcript and owner text | `components/CallTranscript.tsx` |
| Problem cards | `components/Problem.tsx` |
| How it works steps | `components/HowItWorks.tsx` |
| Pool / landscaping call types | `components/Trades.tsx` |
| Prices and plan features | `components/Pricing.tsx` |
| FAQ questions and answers | `components/Faq.tsx` |
| Demo form | `components/DemoForm.tsx` |
| Colors and fonts | `tailwind.config.ts`, `app/layout.tsx` |
| Page title / Google description | `app/layout.tsx` |

## Demo form submissions

Each demo request is emailed to you through [Resend](https://resend.com) (free for up to 3,000 emails a month). Hitting **Reply** on that email goes straight to the person who filled out the form.

On your own computer, if Resend isn't set up, requests are saved to `data/demo-requests.json` instead (kept out of git because it holds contact info).

### Setting up Resend

1. Sign up at resend.com **using the email address where you want demo requests delivered**.
2. Go to **API Keys → Create API Key**, and copy the key (starts with `re_`).
3. In Vercel: **Project → Settings → Environment Variables**, add:
   - `RESEND_API_KEY` = the key from step 2
   - `DEMO_NOTIFY_EMAIL` = that same email address
4. Redeploy (Vercel → Deployments → ⋯ → Redeploy) and send yourself a test request.

Until you verify a domain with Resend, emails come from `onboarding@resend.dev` and can only be delivered to the address you signed up with. Once your domain is live, add it under **Domains** in Resend (it gives you DNS records to copy, same as Vercel), then set `DEMO_FROM_EMAIL` to something like `DesertDesk <demos@yourdomain.com>`. After that you can send to any address, including several (comma-separated).

See `.env.example` for all settings. The code lives in `app/api/demo-request/route.ts`.
