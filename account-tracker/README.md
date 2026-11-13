# Account Tracker

A single-page tool for tracking the betting accounts you're running for other people.

For each account it stores:

- **Account holder**: whose account it is, plus the sportsbook
- **Login**: username and password, hidden until you click Show, with copy buttons
- **Starting balance**: what was in the account when you started
- **Current / final balance**: update it from the table as you go
- **Profit**: current minus starting
- **Their cut**: 20% of the profit by default (you can change the % per account). If the account is down, the cut is $0.
- **You keep**: profit minus their cut

The cards at the top add it all up: money across all accounts (only active accounts count; when you click **Close out**, or mark the cut paid, the money has been paid back to you, so that account drops out of this total), total profit, total cuts, cuts you still owe (anything not marked "Cut paid"), and what you keep.

## Profit tab

The **Profit** tab totals your returns for a period: this month, the last 30 days, this year, any past year, or all time. It shows:

- Profit, their cuts, what you keep, and your return % on the starting balances
- A month-by-month chart and table (or year by year for "All time")
- A breakdown by account

Each balance change is saved with a date, so profit counts toward the month it happened in. When you add or edit an account, the **Date of this balance** field lets you backdate an entry (for example, an account you settled last month).

## Install it as a real app (recommended)

The tracker is published with GitHub Pages at **https://chip1226.github.io/Chip/account-tracker/**. Only the empty app is online. Your accounts and logins are stored in Chrome on your own computer, and nobody who visits the link can see them.

1. Open that link in Chrome.
2. Open the ⋮ menu (top right), choose **Cast, save, and share**, then **Install page as app…**, then **Install**. On older Chrome versions, use the install icon at the right end of the address bar.
3. It opens in its own window with its own Dock icon. Right-click that icon and choose **Options → Keep in Dock**.

The installed app works without internet and picks up updates automatically, so you don't need to download it again.

**Moving data from the old version:** in the old window, click **Export backup**. In the new app, click **Import backup** and pick that file.

## Install with the shortcut scripts (older method)

The scripts below open the local file in an app-style Chrome window. On a Mac that window sits under Chrome's Dock icon and doesn't get its own icon.


This opens the tracker in its own window, with no browser tabs or address bar, from a Desktop / Start Menu / Applications shortcut. You need Google Chrome or Microsoft Edge (Edge comes with Windows).

1. On GitHub, click **Code → Download ZIP**, then unzip it. Put the `account-tracker` folder somewhere permanent, such as Documents.
2. **Windows:** double-click `Install (Windows).bat`. If Windows shows "Windows protected your PC", click **More info → Run anyway**. You get an **Account Tracker** shortcut on the Desktop and in the Start Menu. Right-click its taskbar icon and choose **Pin to taskbar**.
3. **Mac:** right-click `Install (Mac).command` and choose **Open**, then **Open** again (a plain double-click gets blocked because the file was downloaded). It creates **Account Tracker** in the Applications folder in your home folder and adds it to your Dock. If macOS says the file "Not Opened", click **Done**, then go to **System Settings → Privacy & Security**, click **Open Anyway**, and run it again.

If you move the folder later, run the installer again. Your data is unaffected, because it's stored by the browser rather than in the folder.

## How to use it without installing

Open `index.html` in any browser. It needs no install and no internet.

## Where your data lives

Everything is saved in that browser on that device. Nothing is sent anywhere, and none of your data goes into this git repo.

- **Export backup** saves a `.json` file with everything, passwords included. Keep it private.
- **Import backup** restores from one of those files (it can also move your data to another device).
- **Export CSV** gives you a spreadsheet without the passwords.

Clearing your browser data deletes the tracker's data, so export backups regularly. The app reminds you once a month: if it's been 30 days since your last backup, a banner at the top offers **Back up now** or **Remind me in 3 days**. Your last backup date is shown next to the Export backup button.
