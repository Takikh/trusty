export function NavigationBar() {
  return (
    <nav className="w-full bg-white border-b border-border px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground">TH</span>
          </div>
          <span className="text-foreground">TeleHealth</span>
        </div>
      </div>
    </nav>
  );
}
