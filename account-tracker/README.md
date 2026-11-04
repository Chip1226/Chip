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

The cards at the top add it all up: money across all accounts, total profit, total cuts, cuts you still owe (anything not marked "Cut paid"), and what you keep.

## How to use it

Open `index.html` in any browser (double-click it, or AirDrop / email it to your phone). It needs no install and no internet.

## Where your data lives

Everything is saved in that browser on that device. Nothing is sent anywhere, and none of your data goes into this git repo.

- **Export backup** saves a `.json` file with everything, passwords included. Keep it private.
- **Import backup** restores from one of those files (it can also move your data to another device).
- **Export CSV** gives you a spreadsheet without the passwords.

Clearing your browser data deletes the tracker's data, so export backups regularly.
