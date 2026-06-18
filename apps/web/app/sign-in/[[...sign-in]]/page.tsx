import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <SignIn
        appearance={{
          variables: { colorPrimary: "#22d3ee" },
        }}
      />
    </main>
  );
}
