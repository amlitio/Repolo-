# ⚡ Quick Start - Get Running in 5 Minutes

For experienced developers who want to get started quickly.

## Prerequisites

- Node.js 18+
- Firebase account
- Vercel account (for deployment)

## 1. Install & Configure (2 min)

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your Firebase config
nano .env  # or use your editor
```

## 2. Firebase Setup (2 min)

1. Create project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable **Email/Password** auth
3. Create **Firestore** database
4. Set **Security Rules** (copy from `SETUP_GUIDE.md`)
5. Create first admin user manually in Firestore

## 3. Run Locally (30 sec)

```bash
npm run dev
# Open http://localhost:3000
```

## 4. Deploy to Vercel (30 sec)

```bash
# Login
vercel login

# Deploy
./deploy.sh
# or: vercel --prod

# Add env vars in Vercel dashboard
# Redeploy
```

## Done! 🎉

Access your app at the Vercel URL.

## What's Included

✅ Full authentication system
✅ Role-based access (Admin/Manager/Employee)
✅ Time-off request workflow
✅ PTO balance tracking
✅ Multi-level approval chain
✅ User invitation system
✅ Responsive UI
✅ Ready for production

## Admin First Steps

1. Login with admin credentials
2. Invite users via "Invite User" button
3. Copy invitation links and share with users
4. Manage requests as they come in

## Tech Stack

- Next.js 14 + TypeScript
- Firebase (Auth + Firestore)
- Tailwind CSS
- Zustand state management

## Need Help?

- 📖 Full guide: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- 🔧 Issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📚 Features: [README.md](README.md)

---

Built with speed in mind! ⚡
