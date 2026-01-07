# 🏢 TimeOff Manager

A complete company-wide time-off management system built with Next.js 14, TypeScript, Firebase, and Tailwind CSS.

## ✨ Features

### For Employees
- ✅ Submit vacation, sick, and personal leave requests
- 📊 Real-time PTO balance tracking
- 👁️ View request status through approval chain
- ❌ Cancel pending requests

### For Managers
- ✅ Approve/reject team requests
- 👥 View team members and their balances
- 📅 Track upcoming time off
- 🔄 Multi-level approval workflow

### For Admins
- 👤 Invite users with custom roles
- ⚙️ Manage all users and their balances
- ✅ Final approval authority
- 🌐 View all requests system-wide
- 📧 Manage pending invitations

## 🔥 Approval Workflow

1. **Employee submits** → **Manager reviews** → **Admin approves**
2. Email notifications at each step (configurable)
3. Automatic PTO balance deduction upon final approval
4. Business days calculation (excludes weekends)

## 🛠️ Tech Stack

- **Framework:** Next.js 14 with TypeScript
- **Authentication & Database:** Firebase (Auth + Firestore)
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Icons:** Lucide React
- **Notifications:** React Hot Toast
- **Date Handling:** date-fns

## 📋 Prerequisites

Before you begin, ensure you have:

- Node.js 18+ installed
- npm or yarn package manager
- A Firebase account (free tier works!)
- A Vercel account (free tier works!)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd time-off-management
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Set Up Firebase

#### Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Follow the setup wizard
4. Once created, click on the web icon (</>) to add a web app
5. Register your app and copy the configuration

#### Enable Authentication

1. In Firebase Console, go to **Authentication**
2. Click "Get started"
3. Enable "Email/Password" provider

#### Create Firestore Database

1. In Firebase Console, go to **Firestore Database**
2. Click "Create database"
3. Start in **production mode** (we'll set up rules next)
4. Choose a location closest to your users

#### Set Up Firestore Security Rules

Go to **Firestore Database** → **Rules** and paste:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users collection
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        (request.auth.uid == userId ||
         get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin');
    }

    // Requests collection
    match /requests/{requestId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null &&
        request.resource.data.userId == request.auth.uid;
      allow update: if request.auth != null && (
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['manager', 'admin']
      );
      allow delete: if request.auth != null &&
        request.auth.uid == resource.data.userId &&
        resource.data.status == 'pending';
    }

    // Invitations collection
    match /invitations/{invitationId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow update: if request.auth != null;
      allow delete: if request.auth != null &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
  }
}
```

Click **Publish** to save the rules.

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your Firebase configuration:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_ADMIN_EMAIL=admin@yourcompany.com
```

### 5. Create Your First Admin User

Since this is a fresh installation, you'll need to manually create the first admin user in Firebase:

1. Go to **Firebase Console** → **Authentication**
2. Click "Add user"
3. Enter email and password for your admin account
4. Copy the User UID
5. Go to **Firestore Database**
6. Create a new collection called `users`
7. Add a document with the User UID as the document ID
8. Add these fields:

```json
{
  "email": "admin@yourcompany.com",
  "name": "Admin User",
  "role": "admin",
  "ptoBalance": 20,
  "sickBalance": 10,
  "personalBalance": 5,
  "createdAt": [Current Timestamp],
  "updatedAt": [Current Timestamp]
}
```

### 6. Run the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🌐 Deployment to Vercel (FREE!)

### Option 1: Using the Deploy Script (Recommended)

1. Make the script executable:

```bash
chmod +x deploy.sh
```

2. Run the deployment:

```bash
./deploy.sh
```

The script will:
- Install Vercel CLI if needed
- Check for required files
- Install dependencies
- Build the project
- Deploy to Vercel

### Option 2: Manual Deployment

1. Install Vercel CLI:

```bash
npm install -g vercel
```

2. Login to Vercel:

```bash
vercel login
```

3. Deploy:

```bash
vercel --prod
```

### Configure Environment Variables on Vercel

After deployment, you need to add your environment variables:

1. Go to your project on [Vercel Dashboard](https://vercel.com/dashboard)
2. Go to **Settings** → **Environment Variables**
3. Add all variables from your `.env` file
4. Redeploy the project

### Set Up Custom Domain (Optional)

1. In Vercel Dashboard, go to your project
2. Go to **Settings** → **Domains**
3. Add your custom domain
4. Follow the DNS configuration instructions

## 📖 User Guide

### For Admins

#### Inviting Users

1. Log in to the admin dashboard
2. Click "Invite User"
3. Fill in:
   - Name and email
   - Role (Employee, Manager, or Admin)
   - Manager (for employees)
   - Initial PTO balances
4. Click "Send Invitation"
5. Copy the invitation link and send it to the user

#### Managing Users

- View all users and their balances
- Click on any balance to edit it
- Assign managers to employees

#### Approving Requests

- View all pending requests
- Click on a request to review details
- Approve or reject with optional comments

### For Managers

#### Reviewing Requests

1. Log in to the manager dashboard
2. View pending requests from your team
3. Click on a request to review
4. Approve (sends to admin) or reject with comments

#### Viewing Team

- See all team members and their balances
- Track upcoming time off

### For Employees

#### Requesting Time Off

1. Log in to the employee dashboard
2. Click "Request Time Off"
3. Select:
   - Leave type (Vacation, Sick, Personal)
   - Start and end dates
   - Reason
4. Check your remaining balance
5. Submit request

#### Tracking Requests

- View all your requests and their status
- Cancel pending requests if needed
- See your current PTO balances

## 🔧 Customization

### Changing Initial Balances

Edit default values in `/components/InviteUserModal.tsx`:

```typescript
const [ptoBalance, setPtoBalance] = useState(15);
const [sickBalance, setSickBalance] = useState(10);
const [personalBalance, setPersonalBalance] = useState(5);
```

### Adding Holidays

To exclude holidays from business days calculation, modify `/lib/utils.ts`:

```typescript
const holidays = [
  new Date('2024-12-25'), // Christmas
  new Date('2024-01-01'),  // New Year
  // Add more holidays...
];

export function calculateBusinessDays(startDate: Date, endDate: Date): number {
  // Add holiday check logic
}
```

### Customizing Email Notifications

The system is ready for email notifications. To implement:

1. Set up a Firebase Cloud Function or external service
2. Add email logic in the stores when status changes
3. Configure SMTP or use services like SendGrid, Mailgun, etc.

## 🎨 Theming

The app uses Tailwind CSS. To customize colors:

Edit `/tailwind.config.ts`:

```typescript
colors: {
  primary: {
    50: '#f0f9ff',
    // ... change to your brand colors
  },
}
```

## 📱 Mobile Support

The app is fully responsive and works on:
- 📱 Mobile phones
- 📱 Tablets
- 💻 Desktops

## 🔒 Security

- Firebase Authentication for secure login
- Firestore security rules for data protection
- Role-based access control (RBAC)
- Client-side and server-side validation

## 🐛 Troubleshooting

### Build Errors

```bash
# Clear cache and reinstall
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

### Firebase Connection Issues

- Verify your `.env` file has correct values
- Check Firebase project settings
- Ensure Firestore is enabled

### Deployment Issues

- Make sure all environment variables are set in Vercel
- Check build logs for specific errors
- Verify Firebase rules are published

## 📄 License

MIT License - feel free to use this for your company!

## 🤝 Support

Need help? Create an issue in the repository or contact your system administrator.

## 🎉 Features Coming Soon

- 📧 Email notifications
- 📊 Analytics dashboard
- 📅 Calendar view
- 📱 Push notifications
- 🌍 Multi-language support
- 🎨 Dark mode

---

Built with ❤️ using Next.js, Firebase, and Tailwind CSS
