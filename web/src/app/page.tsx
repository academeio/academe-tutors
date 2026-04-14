export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-800">Academe Tutors</h1>
        <p className="mt-2 text-slate-500">
          This application launches from Canvas LMS via LTI 1.3.
        </p>
        <p className="mt-1 text-sm text-slate-400">
          Direct access is not supported. Please launch from your course in Canvas.
        </p>
      </div>
    </main>
  );
}
