# 🚀 Complete Setup Guide - TimeOff Manager

This guide will walk you through setting up the TimeOff Management System from scratch to deployment.

## 📦 What You'll Need

- **15-20 minutes** of your time
- **Computer** with internet connection
- **Email account** for Firebase & Vercel
- **Node.js 18+** installed on your machine

## Part 1: Initial Setup (5 minutes)

### Step 1: Install Node.js

If you don't have Node.js installed:

1. Go to [nodejs.org](https://nodejs.org/)
2. Download the LTS version
3. Install and verify:

```bash
node --version  # Should show v18 or higher
npm --version   # Should show 9 or higher
```

### Step 2: Download the Project

```bash
# Navigate to your projects folder
cd ~/projects

# Clone or download the project
# Then navigate into it
cd time-off-management

# Install dependencies
npm install
```

## Part 2: Firebase Setup (5 minutes)

### Step 1: Create Firebase Project

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Click **"Add project"**
3. Enter project name: `timeoff-manager` (or your choice)
4. **Disable Google Analytics** (not needed)
5. Click **"Create project"**
6. Wait for project creation (30 seconds)

### Step 2: Register Web App

1. In your Firebase project, click the **web icon** `</>`
2. App nickname: `TimeOff Manager`
3. **Don't** check "Firebase Hosting"
4. Click **"Register app"**
5. **Copy** the config object that looks like:

```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};
```

### Step 3: Enable Authentication

1. In Firebase Console sidebar, click **"Authentication"**
2. Click **"Get started"**
3. Click **"Email/Password"**
4. Toggle **"Enable"** on
5. Click **"Save"**

### Step 4: Create Database

1. In Firebase Console sidebar, click **"Firestore Database"**
2. Click **"Create database"**
3. Select **"Start in production mode"**
4. Choose location closest to your users
5. Click **"Enable"**

### Step 5: Set Security Rules

1. In Firestore, click **"Rules"** tab
2. **Delete everything** and paste this:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && (
        request.auth.uid == userId ||
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin'
      );
    }

    match /requests/{requestId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null && request.resource.data.userId == request.auth.uid;
      allow update: if request.auth != null && (
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['manager', 'admin']
      );
      allow delete: if request.auth != null &&
        request.auth.uid == resource.data.userId &&
        resource.data.status == 'pending';
    }

    match /invitations/{invitationId} {
      allow read: if request.auth != null;
      allow create, delete: if request.auth != null &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow update: if request.auth != null;
    }
  }
}
```

3. Click **"Publish"**

## Part 3: Configure Your App (2 minutes)

### Step 1: Create Environment File

In your project folder:

```bash
cp .env.example .env
```

### Step 2: Add Firebase Config

Edit `.env` file and paste your Firebase config:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef
NEXT_PUBLIC_ADMIN_EMAIL=your.email@company.com
```

## Part 4: Create First Admin (3 minutes)

### Option A: Using Firebase Console (Recommended)

1. Go to **Authentication** in Firebase Console
2. Click **"Add user"**
3. Enter:
   - Email: `admin@yourcompany.com`
   - Password: `YourSecurePassword123`
4. Click **"Add user"**
5. **Copy the User UID** (looks like: `Xy3kF8mN2pQr...`)

6. Go to **Firestore Database**
7. Click **"Start collection"**
8. Collection ID: `users`
9. Click **"Next"**
10. Document ID: **Paste the User UID you copied**
11. Add these fields:

| Field | Type | Value |
|-------|------|-------|
| email | string | admin@yourcompany.com |
| name | string | Admin User |
| role | string | admin |
| ptoBalance | number | 20 |
| sickBalance | number | 10 |
| personalBalance | number | 5 |
| createdAt | timestamp | (click "Add timestamp") |
| updatedAt | timestamp | (click "Add timestamp") |

12. Click **"Save"**

### Option B: Using Firebase Admin SDK

See `ADMIN_SETUP.md` for programmatic setup.

## Part 5: Test Locally (2 minutes)

```bash
# Start development server
npm run dev
```

1. Open [http://localhost:3000](http://localhost:3000)
2. You should see the login page
3. Login with your admin credentials
4. You should see the Admin Dashboard!

**🎉 If you see the dashboard, your setup is complete!**

## Part 6: Deploy to Vercel (5 minutes)

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"**
3. Sign up with GitHub (recommended) or email

### Step 2: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 3: Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate.

### Step 4: Deploy

```bash
# Option A: Use our script
chmod +x deploy.sh
./deploy.sh

# Option B: Manual deployment
vercel --prod
```

### Step 5: Add Environment Variables

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click on your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable from your `.env` file:
   - Name: `NEXT_PUBLIC_FIREBASE_API_KEY`
   - Value: `AIza...`
   - Click **"Save"**
5. Repeat for all variables

### Step 6: Redeploy

```bash
vercel --prod
```

## 🎉 You're Done!

Your TimeOff Manager is now live at: `https://your-project.vercel.app`

## Next Steps

### 1. Invite Your First Employees

1. Login as admin
2. Click **"Invite User"**
3. Fill in employee details
4. Copy the invitation link
5. Send it to the employee

### 2. Set Up Managers

1. Invite users with "Manager" role
2. Employees can be assigned to managers

### 3. Customize

- Edit balances in Admin Dashboard
- Customize colors in `tailwind.config.ts`
- Add your company logo

## Common Issues & Solutions

### Issue: "Permission denied" when deploying

**Solution:**
```bash
chmod +x deploy.sh
```

### Issue: Build fails with Firebase errors

**Solution:**
- Verify all env variables are set
- Check Firebase config is correct
- Ensure Firestore is enabled

### Issue: Can't login

**Solution:**
- Check Firebase Authentication is enabled
- Verify user exists in Authentication tab
- Ensure user document exists in Firestore `users` collection

### Issue: Firestore permission denied

**Solution:**
- Verify security rules are published
- Check user has correct role in Firestore document

## Need Help?

1. Check the main [README.md](README.md)
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check Firebase Console logs
4. Check Vercel deployment logs

## Security Checklist

Before going live, ensure:

- ✅ Firestore security rules are published
- ✅ Admin user is created with strong password
- ✅ Environment variables are set in Vercel
- ✅ `.env` file is in `.gitignore`
- ✅ Firebase project has proper access controls

---

**Estimated Total Time:** 15-20 minutes

**Cost:** $0 (using free tiers)

**Difficulty:** Beginner-friendly 🟢

Happy managing time off! 🎉
