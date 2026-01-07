# 🔧 Troubleshooting Guide

Common issues and their solutions for TimeOff Manager.

## 🔥 Firebase Issues

### Issue: "Firebase: Error (auth/configuration-not-found)"

**Cause:** Firebase config is missing or incorrect.

**Solution:**
1. Check `.env` file exists in root directory
2. Verify all `NEXT_PUBLIC_FIREBASE_*` variables are set
3. Restart development server: `npm run dev`
4. For Vercel: Add env variables in dashboard and redeploy

### Issue: "Missing or insufficient permissions"

**Cause:** Firestore security rules not set up correctly.

**Solution:**
1. Go to Firebase Console → Firestore Database → Rules
2. Copy rules from `SETUP_GUIDE.md`
3. Click "Publish"
4. Wait 1-2 minutes for rules to propagate

### Issue: "User not found" after login

**Cause:** User exists in Authentication but not in Firestore.

**Solution:**
1. Go to Firebase Console → Authentication
2. Copy the User UID
3. Go to Firestore Database → `users` collection
4. Create document with User UID as ID
5. Add required fields (see SETUP_GUIDE.md)

## 🚀 Deployment Issues

### Issue: Vercel build fails with "Module not found"

**Cause:** Dependencies not installed or cache issue.

**Solution:**
```bash
# Clear cache
rm -rf .next node_modules package-lock.json

# Reinstall
npm install

# Try building locally first
npm run build

# If successful, deploy again
vercel --prod
```

### Issue: "Environment variables not found" on Vercel

**Cause:** Env variables not set in Vercel dashboard.

**Solution:**
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Settings → Environment Variables
4. Add all variables from `.env` file
5. Important: Use exact names including `NEXT_PUBLIC_` prefix
6. Redeploy after adding variables

### Issue: 404 error on deployed site

**Cause:** Vercel didn't detect Next.js framework.

**Solution:**
1. In Vercel dashboard, go to project Settings
2. Under "Framework Preset", select "Next.js"
3. Redeploy the project

## 💻 Local Development Issues

### Issue: "Port 3000 already in use"

**Solution:**
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process (replace PID with actual number)
kill -9 PID

# Or use a different port
PORT=3001 npm run dev
```

### Issue: Changes not reflecting in browser

**Solution:**
1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Delete `.next` folder: `rm -rf .next`
3. Restart dev server: `npm run dev`
4. Try incognito/private browsing mode

### Issue: TypeScript errors

**Solution:**
```bash
# Regenerate TypeScript config
npm run build

# If errors persist, check Node version
node --version  # Should be 18+

# Update dependencies
npm update
```

## 🔐 Authentication Issues

### Issue: "Cannot sign in" - wrong credentials

**Solution:**
1. Go to Firebase Console → Authentication
2. Verify user email is correct
3. Try resetting password through Firebase Console
4. Ensure email/password provider is enabled

### Issue: User redirects to login immediately after signing in

**Cause:** User document missing in Firestore or incorrect role.

**Solution:**
1. Check Firestore → `users` collection
2. Find document with User UID
3. Verify `role` field is set to 'admin', 'manager', or 'employee'
4. Verify all required fields exist

### Issue: "Auth state not persisting" - keeps logging out

**Cause:** Browser storage disabled or Firebase config issue.

**Solution:**
1. Check browser allows cookies and local storage
2. Try different browser
3. Check browser console for errors
4. Verify Firebase Auth domain in `.env` matches Firebase Console

## 📊 Data Issues

### Issue: Requests not showing up

**Cause:** Firestore query issue or security rules.

**Solution:**
1. Check Firestore → `requests` collection exists
2. Verify security rules allow reading requests
3. Check browser console for errors
4. Verify user has correct role in Firestore

### Issue: Can't create time off request

**Cause:** Insufficient balance or validation error.

**Solution:**
1. Check user has sufficient balance in Firestore
2. Verify `ptoBalance`, `sickBalance`, `personalBalance` fields exist
3. Check start date is not after end date
4. Ensure manager is assigned for employees

### Issue: Balance not updating after approval

**Cause:** Store logic issue or permission error.

**Solution:**
1. Check browser console for errors
2. Verify admin has permission in Firestore rules
3. Manually check Firestore → `users` → check balance values
4. Try refreshing the page

## 🎨 UI/Display Issues

### Issue: Styles not loading / ugly appearance

**Cause:** Tailwind CSS not compiling.

**Solution:**
```bash
# Rebuild
npm run build

# Clear Next.js cache
rm -rf .next

# Restart dev server
npm run dev
```

### Issue: Modal not closing / stuck

**Solution:**
1. Refresh the page (F5)
2. Check browser console for JavaScript errors
3. Clear browser cache

### Issue: Mobile view broken

**Solution:**
1. Check browser dev tools mobile emulation
2. Clear browser cache
3. Verify `viewport` meta tag in HTML
4. Try actual mobile device

## 📧 Invitation Issues

### Issue: Invitation link not working

**Cause:** Invitation expired or already used.

**Solution:**
1. Check Firestore → `invitations` collection
2. Verify invitation `status` is 'pending'
3. Check `expiresAt` date hasn't passed
4. Create new invitation if expired

### Issue: Can't create invitation

**Cause:** Email already exists or permission issue.

**Solution:**
1. Check if user already exists: Firebase Console → Authentication
2. Check Firestore → `users` for existing email
3. Verify logged-in user has 'admin' role
4. Check browser console for specific error

### Issue: "Email does not match invitation" during signup

**Cause:** User trying to sign up with different email than invited.

**Solution:**
- User must use the exact email the invitation was sent to
- Admin can delete old invitation and create new one
- Check invitation link has correct invitation ID

## 🔄 State Management Issues

### Issue: Data not updating after action

**Solution:**
1. Check browser console for errors
2. Try refreshing the page (F5)
3. Verify Firestore has the updated data
4. Check Zustand store is fetching correctly

### Issue: User info not loading

**Cause:** Auth state not initialized.

**Solution:**
1. Wait a few seconds for auth to initialize
2. Check Firebase Auth is enabled
3. Verify user document exists in Firestore
4. Check browser console for errors

## 🌐 Network Issues

### Issue: "Network request failed"

**Cause:** No internet or Firebase services down.

**Solution:**
1. Check internet connection
2. Check [Firebase Status](https://status.firebase.google.com/)
3. Try different network/WiFi
4. Disable VPN if using one
5. Check browser blocks Firebase domains

### Issue: Slow performance

**Solution:**
1. Check internet speed
2. Optimize Firestore queries (already optimized in code)
3. Choose Firebase region closer to users
4. Check browser has sufficient resources
5. Close unnecessary browser tabs

## 🛠️ Build Issues

### Issue: "Build failed" during deployment

**Cause:** Various - check error message.

**Common Solutions:**
```bash
# 1. Clear everything
rm -rf .next node_modules package-lock.json

# 2. Fresh install
npm install

# 3. Check for TypeScript errors
npm run build

# 4. Fix any errors shown
# 5. Try deployment again
```

### Issue: "Out of memory" during build

**Solution:**
```bash
# Increase Node memory
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Or in package.json scripts:
"build": "NODE_OPTIONS=--max-old-space-size=4096 next build"
```

## 🐛 Getting More Help

If issues persist:

### 1. Check Browser Console
- Open Developer Tools (F12)
- Check Console tab for errors
- Copy error messages

### 2. Check Firebase Console
- Go to Firebase Console
- Check Authentication tab
- Check Firestore Database
- Look for error patterns

### 3. Check Vercel Logs
- Go to Vercel Dashboard
- Select your project
- View deployment logs
- Check function logs

### 4. Enable Debug Mode

Add to your `.env`:
```env
NEXT_PUBLIC_DEBUG=true
```

### 5. Check Version Compatibility

```bash
node --version   # Should be 18+
npm --version    # Should be 9+
```

Update if needed:
```bash
nvm install 18   # Using nvm
# or download from nodejs.org
```

## 📝 Reporting Issues

When asking for help, include:

1. **Error message** (full text)
2. **Browser console** logs
3. **Steps to reproduce** the issue
4. **Environment:**
   - Node version
   - Browser & version
   - Operating system
5. **What you've tried** already

## ✅ Verification Checklist

Before reporting an issue, verify:

- [ ] Node.js 18+ installed
- [ ] All dependencies installed (`npm install`)
- [ ] `.env` file exists with correct values
- [ ] Firebase Authentication enabled
- [ ] Firestore Database created
- [ ] Security rules published
- [ ] Admin user created in Firestore
- [ ] Local build works (`npm run build`)
- [ ] Browser console clear of errors

---

**Still stuck?** That's okay! Create an issue in the repository with the information above, and we'll help you out! 🤝
