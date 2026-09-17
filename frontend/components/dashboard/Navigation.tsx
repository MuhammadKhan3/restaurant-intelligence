const links = [{ href: "/", label: "Floor View" }];

export function Navigation() {
  return (
    <nav aria-label="Primary" className="flex items-center gap-6">
      {links.map((link) => (
        <a
          key={link.href}
          href={link.href}
          className="text-sm font-medium text-zinc-700 hover:text-black dark:text-zinc-300 dark:hover:text-white"
        >
          {link.label}
        </a>
      ))}
    </nav>
  );
}
