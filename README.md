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

Submissions are saved to `data/demo-requests.json`, which is created on the first submission. This file is kept out of git because it holds people's contact info.

**This only works on your own computer.** Vercel doesn't let websites save files, so before launch the form needs to send an email instead (for example with [Resend](https://resend.com)). The code to change is `app/api/demo-request/route.ts`.
